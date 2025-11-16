"""Planner agent for orchestrating multi-agent workflows using LLM-based intent understanding with memory/checkpointer."""

from typing import Dict, Any, Optional, Literal, List
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from research_assistant.agents.base import BaseReActAgent
from research_assistant.prompts.planner import PLANNER_PROMPT


class RoutingDecision(BaseModel):
    """Structured output for routing decisions."""
    
    next_agent: Literal["researcher", "coder", "reporter", "finish"] = Field(
        description="The next agent to route the task to, or 'finish' if complete"
    )
    reasoning: str = Field(
        description="Brief explanation of why this routing decision was made"
    )
    task_description: Optional[str] = Field(
        default=None,
        description="Specific task description for the next agent, if applicable"
    )
    is_complete: bool = Field(
        default=False,
        description="Whether the overall task is complete and ready for final reporting"
    )


class PlannerAgent(BaseReActAgent):
    """
    Agent that orchestrates task routing using LLM-based intent understanding.
    
    This agent runs in a loop after each sub-agent completes. It reads from
    conversation history (persisted via checkpointer) to understand what has
    been completed and decides the next step.
    """

    def __init__(self, llm: ChatOpenAI = None):
        """Initialize Planner agent with LLM and structured output parser."""
        if llm is None:
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        self.parser = PydanticOutputParser(pydantic_object=RoutingDecision)
        
        try:
            self.structured_llm = llm.with_structured_output(RoutingDecision)
        except AttributeError:
            self.structured_llm = None
            self.parser_llm = llm
        
        super().__init__(
            llm=llm,
            system_prompt=PLANNER_PROMPT,
            tools=[],
        )

    def decide_next_step(
        self, 
        user_question: str,
        conversation_history: List[BaseMessage] = None,
        research_results: Dict[str, Any] = None,
        coder_results: Dict[str, Any] = None,
        reporter_results: Dict[str, Any] = None
    ) -> RoutingDecision:
        """
        Analyze user question and state variables to decide the next agent to route to.
            This method is called in a loop after each agent completes. It checks state variables
        to see what has been completed and uses that information to decide the next step.
        
        Args:
            user_question: The original user question/goal
            conversation_history: List of messages from checkpointer/memory
            research_results: The actual research_results state variable (None if not completed)
            coder_results: The actual coder_results state variable (None if not completed)
            reporter_results: The actual reporter_results state variable (None if not completed)
                
        Returns:
            RoutingDecision with next_agent, reasoning, and task_description
        """
        if not user_question or not isinstance(user_question, str) or not user_question.strip():
            return RoutingDecision(
                next_agent="researcher",
                reasoning="Empty or invalid question, defaulting to research agent",
                task_description="Analyze the user's request",
                is_complete=False
            )
        
        conversation_history = conversation_history or []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conversation_summary = self._summarize_conversation_history(conversation_history)
        
        has_research = research_results is not None
        has_coder = coder_results is not None
        has_reporter = reporter_results is not None
        
        state_content = self._format_state_variables(
            research_results=research_results,
            coder_results=coder_results,
            reporter_results=reporter_results
        )
        
        routing_prompt = f"""{PLANNER_PROMPT.format(
            goal=user_question,
            state="See state variables and conversation history below",
            previous_results="See state variables below for what has been completed",
            time=current_time
        )}

{state_content}

Conversation History (from checkpointer/memory):
{conversation_summary}

Original User Question: {user_question}

Based on the state variables and conversation history above, analyze:
1. What has been completed so far? (Check the state variables above - if a variable exists, that agent has completed)
2. What still needs to be done?
3. Which agent should be called next?

Routing Logic:
- If research_results exists → Research agent has already been called and completed
- If coder_results exists → Coder agent has already been called and completed
- If reporter_results exists → Reporter agent has already been called and completed
- If research_results does NOT exist and question needs research → route to "researcher"
- If coder_results does NOT exist and question needs code → route to "coder"
- If research_results exists (and code is done or not needed) and reporter_results does NOT exist → route to "reporter"
- If reporter_results exists → route to "finish"

IMPORTANT: 
- Check the state variables above to see what has been completed
- Do NOT route to an agent if its corresponding state variable already exists (e.g., if research_results exists, do NOT route to researcher again)
- Use the actual content of state variables to understand what has been gathered
- Make an intelligent decision based on what you see in the state variables

Provide your routing decision with clear reasoning based on the state variables."""
        
        try:
            if self.structured_llm:
                decision = self.structured_llm.invoke(routing_prompt)
            else:
                formatted_prompt = f"""{routing_prompt}

{self.parser.get_format_instructions()}

Respond in the following JSON format:
{self.parser.get_format_instructions()}"""
                
                response = self.parser_llm.invoke(formatted_prompt)
                decision = self.parser.parse(response.content)
            
            return decision
        except Exception as e:
            return self._fallback_routing(
                user_question, 
                conversation_history, 
                str(e),
                research_results=research_results,
                coder_results=coder_results,
                reporter_results=reporter_results
            )

    def _format_state_variables(
        self,
        research_results: Dict[str, Any] = None,
        coder_results: Dict[str, Any] = None,
        reporter_results: Dict[str, Any] = None
    ) -> str:
        """
        Format state variables for inclusion in planner prompt.
        
        Args:
            research_results: The research_results state variable
            coder_results: The coder_results state variable
            reporter_results: The reporter_results state variable
            
        Returns:
            Formatted string with state variable contents
        """
        parts = []
        parts.append("=" * 80)
        parts.append("STATE VARIABLES (Check these to see what agents have completed)")
        parts.append("=" * 80)
        parts.append("")
        
        # Research results
        if research_results is not None:
            parts.append("✓ research_results EXISTS (Research agent has been called and completed)")
            result_content = research_results.get("result", "")
            if result_content:
                # Truncate if too long, but show substantial content
                if len(str(result_content)) > 1000:
                    parts.append(f"Content (truncated): {str(result_content)[:1000]}...")
                else:
                    parts.append(f"Content: {result_content}")
            parts.append("")
        else:
            parts.append("✗ research_results DOES NOT EXIST (Research agent has NOT been called)")
            parts.append("")
        
        # Coder results
        if coder_results is not None:
            parts.append("✓ coder_results EXISTS (Coder agent has been called and completed)")
            result_content = coder_results.get("result", "")
            if result_content:
                if len(str(result_content)) > 1000:
                    parts.append(f"Content (truncated): {str(result_content)[:1000]}...")
                else:
                    parts.append(f"Content: {result_content}")
            parts.append("")
        else:
            parts.append("✗ coder_results DOES NOT EXIST (Coder agent has NOT been called)")
            parts.append("")
        
        # Reporter results
        if reporter_results is not None:
            parts.append("✓ reporter_results EXISTS (Reporter agent has been called and completed)")
            result_content = reporter_results.get("result", "")
            if result_content:
                if len(str(result_content)) > 1000:
                    parts.append(f"Content (truncated): {str(result_content)[:1000]}...")
                else:
                    parts.append(f"Content: {result_content}")
            parts.append("")
        else:
            parts.append("✗ reporter_results DOES NOT EXIST (Reporter agent has NOT been called)")
            parts.append("")
        
        parts.append("=" * 80)
        return "\n".join(parts)
    
    def _summarize_conversation_history(self, conversation_history: List[BaseMessage]) -> str:
        """
        Summarize conversation history to extract what agents have completed.
        
        Args:
            conversation_history: List of messages from checkpointer
            
        Returns:
            Formatted string summarizing the conversation
        """
        if not conversation_history:
            return "No previous conversation. This is the first step."
        
        summary_parts = []
        has_research = False
        has_code = False
        has_reporter = False
        
        for i, message in enumerate(conversation_history):
            content = message.content if hasattr(message, 'content') else str(message)
            
            if isinstance(message, AIMessage):
                content_lower = content.lower()
                
                if not has_research and any(indicator in content_lower for indicator in 
                    ["research", "researcher", "tavily", "web search", "found information"]):
                    has_research = True
                    summary_parts.append(f"Step {i+1}: Research agent has completed. Results: {content[:300]}...")
                
                elif not has_code and any(indicator in content_lower for indicator in 
                    ["code", "coder", "python", "executed", "calculated", "validation"]):
                    has_code = True
                    summary_parts.append(f"Step {i+1}: Coder agent has completed. Results: {content[:300]}...")
                
                elif not has_reporter and any(indicator in content_lower for indicator in 
                    ["reporter", "synthesized", "final answer", "summary"]):
                    has_reporter = True
                    summary_parts.append(f"Step {i+1}: Reporter agent has completed. Results: {content[:300]}...")
                
                else:
                    summary_parts.append(f"Step {i+1}: Agent output - {content[:200]}...")
            
            elif isinstance(message, HumanMessage):
                if i == 0:
                    summary_parts.append(f"Step {i+1}: User question - {content}")
                else:
                    summary_parts.append(f"Step {i+1}: User/System message - {content[:200]}...")
        
        status = []
        if has_research:
            status.append("Research: ✓ Completed")
        else:
            status.append("Research: ✗ Not completed")
        
        if has_code:
            status.append("Code: ✓ Completed")
        else:
            status.append("Code: ✗ Not completed")
        
        if has_reporter:
            status.append("Reporter: ✓ Completed")
        else:
            status.append("Reporter: ✗ Not completed")
        
        summary = "\n".join(summary_parts) if summary_parts else "Conversation history available but no clear agent outputs detected."
        summary += f"\n\nCompletion Status:\n" + "\n".join(status)
        
        return summary

    def _fallback_routing(
        self, 
        user_question: str, 
        conversation_history: List[BaseMessage],
        error: str,
        research_results: Dict[str, Any] = None,
        coder_results: Dict[str, Any] = None,
        reporter_results: Dict[str, Any] = None
    ) -> RoutingDecision:
        """Fallback routing logic when structured output fails - uses state variables."""
        has_research = research_results is not None
        has_coder = coder_results is not None
        has_reporter = reporter_results is not None
        
        if has_reporter:
            return RoutingDecision(
                next_agent="finish",
                reasoning=f"Error in structured output: {error}. Reporter has completed (reporter_results exists), finishing workflow.",
                task_description=None,
                is_complete=True
            )
        
        question_lower = user_question.lower()
        needs_research = any(keyword in question_lower for keyword in 
            ["what", "find", "search", "research", "latest", "news", "information", "about", "tell me", "who", "when", "where", "how"])
        needs_code = any(keyword in question_lower for keyword in 
            ["calculate", "compute", "code", "python", "function", "algorithm", "solve", "write code"])
        
        if has_research and not has_reporter:
            if needs_code and not has_coder:
                return RoutingDecision(
                    next_agent="coder",
                    reasoning=f"Error in structured output: {error}. Research complete (research_results exists), but code execution is still needed.",
                    task_description=user_question,
                    is_complete=False
                )
            else:
                return RoutingDecision(
                    next_agent="reporter",
                    reasoning=f"Error in structured output: {error}. Research is complete (research_results exists). {'Code execution is not needed.' if not needs_code else 'Code execution is complete.'} Routing to reporter.",
                    task_description="Synthesize research findings into final answer",
                    is_complete=False
                )
        
        if has_research and has_coder and not has_reporter:
            return RoutingDecision(
                next_agent="reporter",
                reasoning=f"Error in structured output: {error}. Both research and code are complete (both state variables exist), routing to reporter.",
                task_description="Synthesize research and code results",
                is_complete=False
            )
        
        if not has_research and needs_research:
            return RoutingDecision(
                next_agent="researcher",
                reasoning=f"Error in structured output: {error}. Research not yet completed (research_results does not exist), defaulting to research agent.",
                task_description=user_question,
                is_complete=False
            )
        
        if not has_coder and needs_code:
            return RoutingDecision(
                next_agent="coder",
                reasoning=f"Error in structured output: {error}. Code execution may be needed (coder_results does not exist), routing to coder.",
                task_description=user_question,
                is_complete=False
            )
        
        return RoutingDecision(
            next_agent="researcher",
            reasoning=f"Error in structured output: {error}. Defaulting to research agent.",
            task_description=user_question,
            is_complete=False
        )

    def route_task(self, task: str, conversation_history: List[BaseMessage] = None) -> RoutingDecision:
        return self.decide_next_step(task, conversation_history)

    def should_route_to_research(self, task: str, conversation_history: List[BaseMessage] = None) -> bool:
        """
        Determine if task requires research agent using LLM-based intent understanding.
        
        This method uses decide_next_step and checks if next_agent is "researcher".
        Kept for backward compatibility with existing code.
        """
        decision = self.decide_next_step(task, conversation_history)
        return decision.next_agent == "researcher"

    def should_route_to_coder(self, task: str, conversation_history: List[BaseMessage] = None) -> bool:
        """
        Determine if task requires coder agent using LLM-based intent understanding.
        
        This method uses decide_next_step and checks if next_agent is "coder".
        Kept for backward compatibility with existing code.
        """
        decision = self.decide_next_step(task, conversation_history)
        return decision.next_agent == "coder"
