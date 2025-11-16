"""Base ReAct agent class implementing Thought → Act → Observation pattern."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class BaseReActAgent:
    """Base class for ReAct agents following Thought → Act → Observation pattern."""

    def __init__(
        self,
        llm: ChatOpenAI,
        system_prompt: str,
        tools: List[Any] = None,
        max_iterations: int = 5,
    ):
        """Initialize agent with LLM, prompt, and tools."""
        self.llm = llm
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.max_iterations = max_iterations
        self.traces: List[Dict[str, Any]] = []
        
        self.tool_map = {tool.name: tool for tool in self.tools} if self.tools else {}

    def _execute_tool(self, tool_name: str, tool_input: Any) -> str:
        """Execute a tool and return formatted result."""
        if tool_name not in self.tool_map:
            return f"Tool {tool_name} not found. Available tools: {list(self.tool_map.keys())}"
        
        try:
            tool = self.tool_map[tool_name]
            if isinstance(tool_input, str):
                result = tool.invoke(tool_input)
            else:
                result = tool.invoke(tool_input)
            
            if isinstance(result, str):
                return result
            elif isinstance(result, list) and len(result) > 0:
                return "\n".join([str(item) for item in result])
            else:
                return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute ReAct loop: Thought → Act → Observation."""
        context = context or {}
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_system_prompt = self.system_prompt.replace("{time}", current_time) if "{time}" in self.system_prompt else self.system_prompt
        
        tool_descriptions = ""
        if self.tools:
            tool_list = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            tool_descriptions = f"\n\nAvailable tools:\n{tool_list}\n\nWhen you need to use a tool, respond with:\nThought: [your reasoning]\nAction: [tool_name]\nAction Input: [input to tool]\n"
        
        initial_prompt = f"""{formatted_system_prompt}{tool_descriptions}

Task: {task}
Context: {context}

Follow this format:
Thought: [think about what to do]
Action: [tool_name or 'finish']
Action Input: [input if using tool]

After each action, you'll receive an Observation. Continue until you have the answer, then use Action: finish."""
        
        messages = [SystemMessage(content=initial_prompt)]
        all_traces = []
        
        for iteration in range(self.max_iterations):
            response = self.llm.invoke(messages)
            response_text = response.content
            
            thought, action, action_input = self._parse_response(response_text)
            
            trace = {
                "iteration": iteration + 1,
                "thought": thought,
                "act": f"{action}: {action_input}" if action_input else action,
                "observation": "",
            }
            
            observation = ""
            if action and action.lower() != "finish":
                observation = self._execute_tool(action, action_input)
                trace["observation"] = observation
            
            all_traces.append(trace)
            
            # Check for finish
            if action and action.lower() == "finish":
                final_answer = thought or response_text
                return {
                    "result": final_answer,
                    "traces": all_traces,
                    "final_act": "finish",
                }
            
            messages.append(AIMessage(content=response_text))
            if observation:
                messages.append(HumanMessage(content=f"Observation: {observation}"))
        
        return {
            "result": all_traces[-1].get("thought", "Max iterations reached"),
            "traces": all_traces,
            "final_act": "max_iterations",
        }
    
    def _parse_response(self, response: str) -> tuple[str, str, str]:
        """Parse LLM response into thought, action, and action_input."""
        thought = ""
        action = ""
        action_input = ""
        
        lines = response.split("\n")
        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith("thought:"):
                thought = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line_lower.startswith("action:"):
                action_part = line.split(":", 1)[1].strip() if ":" in line else ""
                # Try to split action and input
                if " " in action_part:
                    parts = action_part.split(" ", 1)
                    action = parts[0].strip()
                    action_input = parts[1].strip() if len(parts) > 1 else ""
                else:
                    action = action_part
            elif line_lower.startswith("action input:"):
                action_input = line.split(":", 1)[1].strip() if ":" in line else ""
            elif thought and not action:
                thought += " " + line.strip()
        
        return thought.strip(), action.strip(), action_input.strip()

