# Cognivia

**Your Personal Research Assistant**

Cognivia is an intelligent multi-agent research assistant that leverages the ReAct (Reasoning + Acting) framework to provide comprehensive research capabilities. Built with LangGraph orchestration, Cognivia decomposes complex research queries into actionable tasks, routes them to specialized agents, and synthesizes comprehensive responses.

## Table of Contents

- [About Cognivia](#about-cognivia)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Code Structure](#code-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Example Queries](#example-queries)
- [Project Structure](#project-structure)
- [License](#license)

## About Cognivia

### The ReAct Framework

Cognivia is built on the **ReAct (Reasoning + Acting)** framework, which combines reasoning and acting in language models. The framework follows a pattern of:

1. **Thought**: The agent reasons about what to do next
2. **Act**: The agent takes an action (e.g., using a tool)
3. **Observation**: The agent observes the result of the action
4. **Repeat**: The cycle continues until the task is complete

### Our Implementation

Cognivia implements ReAct through a multi-agent architecture where each agent follows the Thought → Act → Observation pattern:

- **Planner Agent**: Analyzes conversation history and state to decide next steps, routing tasks to specialist agents in a loop-based orchestration
- **Researcher Agent**: Performs web research using Tavily Search, following ReAct cycles to gather comprehensive information
- **Coder Agent**: Executes Python code for validation and data transformation using a sandboxed REPL
- **Reporter Agent**: Synthesizes findings from research and code execution into coherent responses

All agents inherit from a `BaseReActAgent` class that implements the core ReAct loop, ensuring consistent reasoning and action patterns across the system.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Research Assistant System                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         Streamlit UI (Frontend)                      │  │
│  │  • Thought/Act/Observation Traces                    │  │
│  │  • User Input/Output Interface                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │    LangGraph Orchestrator (State Machine)             │  │
│  │  • Agent Routing & State Management                     │  │
│  │  • Checkpoint Persistence                             │  │
│  │  • Trace Replay                                        │  │
│  └─────────────────────────────────────────────────────┘  │
│         │         │         │         │                      │
│         ▼         ▼         ▼         ▼                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Planner  │ │Research  │ │  Coder   │ │ Reporter │      │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│         │         │         │         │                      │
│         │         │         │         │                      │
│         │         ▼         ▼         │                      │
│         │    ┌──────────┐ ┌──────────┐                     │
│         │    │  Tavily   │ │  Python  │                     │
│         │    │  Search   │ │   REPL   │                     │
│         │    │  (Web API)│ │(sandboxed)│                    │
│         │    └──────────┘ └──────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### System Flow

1. **User Input**: User submits a research query through the Streamlit UI
2. **Planner Agent**: Analyzes the goal and conversation history, decides next step using structured routing decisions
3. **Agent Routing**: LangGraph orchestrator routes tasks to appropriate agents:
   - **Researcher Agent**: For information gathering and web research
   - **Coder Agent**: For code execution and validation
   - **Reporter Agent**: For synthesizing final responses
4. **ReAct Execution**: Each agent follows the Thought → Act → Observation cycle:
   - **Thought**: Agent reasons about the next step
   - **Act**: Agent uses tools (Tavily Search or Python REPL)
   - **Observation**: Agent processes tool results
   - **Repeat**: Until task completion
5. **Loop Back to Planner**: After each agent completes, control returns to the Planner which reviews conversation history and decides the next step
6. **Reporter Agent**: Synthesizes all findings into a comprehensive response when planner routes to reporter
7. **Output**: Final response displayed in the chat interface with full execution traces

## Tech Stack

### Core Frameworks
- **LangGraph** (>=0.2.0): State machine orchestration for multi-agent workflows
- **LangChain** (>=0.3.0): Framework for building LLM applications
- **LangChain Core** (>=0.3.36): Core abstractions and interfaces
- **LangChain OpenAI** (>=0.2.0): OpenAI integration for LLM interactions
- **LangChain Community** (>=0.3.0): Community-contributed integrations
- **LangChain Experimental** (>=0.3.0): Experimental features including Python REPL tool

### LLM & AI
- **OpenAI** (^1.12.0): GPT-4o model for agent reasoning and text generation

### Frontend
- **Streamlit** (^1.31.0): Interactive web application framework
- **Streamlit Option Menu** (^0.3.12): Enhanced UI components

### Tools & APIs
- **Tavily Python** (^0.3.0): Web search API for research capabilities

### Development & Quality
- **Pydantic** (^2.6.0): Data validation using Python type annotations
- **Pydantic Settings** (^2.1.0): Settings management
- **Python Dotenv** (^1.0.0): Environment variable management
- **Black** (^24.1.0): Code formatter
- **Ruff** (^0.2.0): Fast Python linter
- **MyPy** (^1.8.0): Static type checker
- **Pytest** (^8.0.0): Testing framework

### Utilities
- **HTTPX** (>=0.26.0): Async HTTP client
- **AioHTTP** (^3.9.0): Async HTTP framework
- **Structlog** (^24.1.0): Structured logging

## Code Structure

### Software Engineering Practices

1. **Modular Architecture**: Clear separation of concerns with dedicated modules for agents, tools, prompts, and UI
2. **Inheritance & Polymorphism**: Base `BaseReActAgent` class provides common ReAct implementation, specialized agents inherit and extend
3. **Type Hints**: Comprehensive type annotations using Python TypedDict and type hints
4. **State Management**: Centralized state management using LangGraph's state machine pattern
5. **Error Handling**: Robust error handling with graceful degradation
6. **Code Quality**: 
   - Black for code formatting (100 char line length)
   - Ruff for linting (pycodestyle, pyflakes, isort, bugbear)
   - MyPy for type checking
   - Pytest for testing with coverage reporting

### Component Breakdown

#### a. Backend

**Agents** (`src/research_assistant/agents/`)
- `base.py`: Base ReAct agent class implementing Thought → Act → Observation pattern
- `planner.py`: Goal decomposition and task routing agent
- `researcher.py`: Web research agent using Tavily Search
- `coder.py`: Code execution agent using Python REPL
- `reporter.py`: Response synthesis agent

**Graphs** (`src/research_assistant/graph/`)
- `state.py`: TypedDict definition for shared agent state
- `workflow.py`: Workflow creation and orchestration logic with loop-based agent routing
- `__init__.py`: Exports for workflow and state

**Tools** (`src/research_assistant/tools/`)
- `tavily.py`: Tavily Search API wrapper
- `repl.py`: Python REPL tool wrapper (sandboxed execution)
- `__init__.py`: Tool exports

#### b. Frontend

**UI** (`src/research_assistant/ui/`)
- `streamlit_app.py`: Main Streamlit application with:
  - Real-time chat interface
  - Agent execution logs display
  - Thought/Act/Observation trace visualization
  - Responsive layout with sidebar settings

#### c. Prompts

**Prompt Engineering** (`src/research_assistant/prompts/`)
- `planner.py`: Planner agent system prompt with ReAct examples
- `research.py`: Research agent prompt with Tavily Search instructions
- `coder.py`: Coder agent prompt with Python REPL guidelines
- `reporter.py`: Reporter agent prompt for response synthesis

Each prompt is carefully engineered to:
- Guide agents through the ReAct pattern
- Provide clear examples of Thought → Act → Observation cycles
- Include tool-specific instructions
- Maintain context awareness

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- API Keys:
  - OpenAI API key
  - Tavily API key

### Step-by-Step Installation

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd researcher_assistant
   ```

2. **Install Dependencies with Poetry**

   ```bash
   poetry install
   ```

   Or using pip:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**

   Create a `.env` file in the root directory:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

   **Getting API Keys:**
   - **OpenAI**: Sign up at [OpenAI Platform](https://platform.openai.com/) and create an API key
   - **Tavily**: Sign up at [Tavily](https://tavily.com/) and get your API key

4. **Verify Installation**

   ```bash
   poetry run python -c "from research_assistant.agents import ResearchAgent; print('Installation successful!')"
   ```

## Usage

### Running the Application

1. **Start the Streamlit App**

   Using Poetry:
   ```bash
   poetry run streamlit run src/research_assistant/ui/streamlit_app.py
   ```

   Or directly:
   ```bash
   streamlit run src/research_assistant/ui/streamlit_app.py
   ```

2. **Access the Application**

   Open your web browser and navigate to:
   ```
   http://localhost:8501
   ```

3. **Using Cognivia**

   - Enter your research query in the chat input at the bottom
   - Click send or press Enter
   - Watch the real-time execution logs as agents process your query
   - View the final synthesized response in the chat interface

### Features

- **Real-time Execution Logs**: See Thought/Act/Observation traces for Research and Coder agents
- **Full Trace Visibility**: Complete execution traces without truncation
- **Chat Interface**: Clean conversation interface with user queries and assistant responses
- **Agent Badges**: Color-coded badges for different agents (Planner, Research, Coder, Reporter)

## Example Queries

Cognivia can handle a wide variety of research queries. Here are some examples:

### Research Queries

**General Research:**
- "What are the latest developments in transformer architectures?"
- "Research the impact of large language models on software development"
- "Find recent papers on reinforcement learning from human feedback"

**Technical Deep Dives:**
- "What is the ReAct framework and how does it work?"
- "Explain the attention mechanism in transformers"
- "What are the differences between GPT-3 and GPT-4?"

### Research with Code Validation

**Combined Queries:**
- "Research gradient descent optimization and validate the algorithm with code"
- "Find information about matrix multiplication and implement it in Python"
- "Research neural network architectures and create a simple feedforward network"

**Code Execution:**
- "Calculate the Fibonacci sequence for the first 20 numbers"
- "Create a function to compute the dot product of two vectors"
- "Validate that softmax function works correctly with a test case"

### Complex Multi-Step Queries

- "Research the history of machine learning, then create a timeline visualization"
- "Find the latest research on attention mechanisms and implement a basic attention layer"
- "What are the key differences between supervised and unsupervised learning? Validate with code examples"

### Best Practices for Queries

1. **Be Specific**: More specific queries yield better results
2. **Combine Research and Code**: Ask for both research and validation for comprehensive answers
3. **Use Natural Language**: Cognivia understands natural language queries
4. **Ask Follow-ups**: The system maintains context for follow-up questions

## Project Structure

```
researcher_assistant/
├── README.md
├── pyproject.toml
├── .env.example
│
├── src/
│   └── research_assistant/
│       ├── __init__.py
│       │
│       ├── agents/              # Agent implementations
│       │   ├── __init__.py
│       │   ├── base.py          # Base ReAct agent
│       │   ├── planner.py       # Planner agent
│       │   ├── researcher.py    # Research agent
│       │   ├── coder.py         # Coder agent
│       │   └── reporter.py      # Reporter agent
│       │
│       ├── graph/               # LangGraph orchestration
│       │   ├── __init__.py      # Exports for workflow and state
│       │   ├── state.py         # State definitions
│       │   └── workflow.py      # Workflow creation and orchestration
│       │
│       ├── prompts/             # Prompt engineering
│       │   ├── __init__.py
│       │   ├── planner.py
│       │   ├── research.py
│       │   ├── coder.py
│       │   └── reporter.py
│       │
│       ├── tools/               # External tool integrations
│       │   ├── __init__.py
│       │   ├── tavily.py        # Tavily Search wrapper
│       │   └── repl.py          # Python REPL wrapper
│       │
│       └── ui/                  # Frontend
│           └── streamlit_app.py # Streamlit application
```

## Acknowledgments

- **LangChain & LangGraph**: For providing excellent frameworks for building LLM applications
- **OpenAI**: For GPT-4o model capabilities
- **Tavily**: For powerful web search API
- **Streamlit**: For the intuitive web framework
- **ReAct Framework**: For the foundational reasoning and acting pattern

---