"""Python REPL tool wrapper using LangChain experimental implementation."""

from langchain_experimental.tools import PythonREPLTool


def get_python_repl_tool() -> PythonREPLTool:
    """Get LangChain Python REPL tool instance."""
    return PythonREPLTool()