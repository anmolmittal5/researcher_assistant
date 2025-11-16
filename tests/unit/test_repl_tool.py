"""Unit tests for Python REPL tool."""

import pytest
from unittest.mock import Mock, patch
from research_assistant.tools.repl import get_python_repl_tool


@pytest.mark.unit
class TestPythonREPLToolInitialization:
    """Test Python REPL tool initialization."""
    
    def test_get_python_repl_tool_success(self):
        """Test successful Python REPL tool initialization."""
        with patch('research_assistant.tools.repl.PythonREPLTool') as mock_repl:
            mock_instance = Mock()
            mock_instance.name = "python_repl"
            mock_instance.description = "A Python shell"
            mock_repl.return_value = mock_instance
            
            tool = get_python_repl_tool()
            
            assert tool is not None
            mock_repl.assert_called_once()
    
    def test_python_repl_tool_has_correct_attributes(self):
        """Test that Python REPL tool has correct attributes."""
        with patch('research_assistant.tools.repl.PythonREPLTool') as mock_repl:
            mock_instance = Mock()
            mock_instance.name = "python_repl"
            mock_instance.description = "A Python shell"
            mock_instance.invoke = Mock(return_value="Code executed")
            mock_repl.return_value = mock_instance
            
            tool = get_python_repl_tool()
            
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "invoke")

