# Test Execution Commands Guide
## Cognivia Research Assistant

This document provides all terminal commands to run individual test cases, test suites, and comprehensive tests.

## Prerequisites

Set the PYTHONPATH before running tests:
```bash
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
```

Or run from project root (commands below assume you're in project root).

---

## 1. Individual Test Cases

### Base Agent Tests

```bash
# Test: Base Agent Initialization
pytest tests/unit/test_base_agent.py::TestBaseAgentInitialization -v

# Test: Tool Execution
pytest tests/unit/test_base_agent.py::TestToolExecution -v

# Test: Response Parsing
pytest tests/unit/test_base_agent.py::TestResponseParsing -v

# Test: ReAct Loop
pytest tests/unit/test_base_agent.py::TestReActLoop -v

# All Base Agent Tests
pytest tests/unit/test_base_agent.py -v
```

### Planner Agent Tests

```bash
# Test: Planner Agent Initialization
pytest tests/unit/test_planner_agent.py::TestPlannerAgentInitialization -v

# Test: Plan Method
pytest tests/unit/test_planner_agent.py::TestPlanMethod -v

# Test: Routing Logic
pytest tests/unit/test_planner_agent.py::TestRoutingLogic -v

# All Planner Agent Tests
pytest tests/unit/test_planner_agent.py -v
```

### Researcher Agent Tests

```bash
# Test: Researcher Agent Initialization
pytest tests/unit/test_researcher_agent.py::TestResearcherAgentInitialization -v

# Test: Research Method
pytest tests/unit/test_researcher_agent.py::TestResearchMethod -v

# All Researcher Agent Tests
pytest tests/unit/test_researcher_agent.py -v
```

### Coder Agent Tests

```bash
# Test: Coder Agent Initialization
pytest tests/unit/test_coder_agent.py::TestCoderAgentInitialization -v

# Test: Code Method
pytest tests/unit/test_coder_agent.py::TestCodeMethod -v

# All Coder Agent Tests
pytest tests/unit/test_coder_agent.py -v
```

### Reporter Agent Tests

```bash
# Test: Reporter Agent Initialization
pytest tests/unit/test_reporter_agent.py::TestReporterAgentInitialization -v

# Test: Synthesize Method
pytest tests/unit/test_reporter_agent.py::TestSynthesizeMethod -v

# All Reporter Agent Tests
pytest tests/unit/test_reporter_agent.py -v
```

### Tool Tests

```bash
# Tavily Tool Tests
pytest tests/unit/test_tavily_tool.py -v

# Python REPL Tool Tests
pytest tests/unit/test_repl_tool.py -v

# All Tool Tests
pytest tests/unit/test_tavily_tool.py tests/unit/test_repl_tool.py -v
```

---

## 2. Test Suites

### Unit Tests (All)

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run all unit tests with coverage
pytest tests/unit/ --cov=research_assistant --cov-report=term-missing -v

# Run all unit tests with HTML coverage report
pytest tests/unit/ --cov=research_assistant --cov-report=html -v
# Then open: htmlcov/index.html
```

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Test: Agent Workflow
pytest tests/integration/test_agent_workflow.py -v

# Test: Tool Integration
pytest tests/integration/test_tool_integration.py -v

# Test: State Management
pytest tests/integration/test_state_management.py -v
```

### End-to-End Tests

```bash
# Run all end-to-end tests
pytest tests/e2e/ -v

# Test: Full Workflow
pytest tests/e2e/test_full_workflow.py -v
```

---

## 3. Comprehensive Test Execution

### Run All Tests

```bash
# Run all tests (unit + integration + e2e)
pytest tests/ -v

# Run all tests with coverage
pytest tests/ --cov=research_assistant --cov-report=term-missing --cov-report=html -v

# Run all tests and save output
pytest tests/ -v > tests/results/all_tests_output.txt 2>&1
```

### Run Tests by Marker

```bash
# Run only unit tests (marked with @pytest.mark.unit)
pytest -m unit -v

# Run only integration tests
pytest -m integration -v

# Run only e2e tests
pytest -m e2e -v
```

### Run Specific Test Categories

```bash
# All agent tests
pytest tests/unit/test_base_agent.py tests/unit/test_planner_agent.py tests/unit/test_researcher_agent.py tests/unit/test_coder_agent.py tests/unit/test_reporter_agent.py -v

# All tool tests
pytest tests/unit/test_tavily_tool.py tests/unit/test_repl_tool.py -v

# All workflow tests
pytest tests/integration/test_agent_workflow.py tests/e2e/test_full_workflow.py -v
```

---

## 4. Automated Test Runner

### Using the Test Runner Script

```bash
# Run automated test suite (runs all tests systematically)
python run_tests.py

# Run and save output
python run_tests.py 2>&1 | tee tests/results/full_execution.log
```

---

## 5. Test Execution with Logging

### Save Individual Test Results

```bash
# Base Agent with log
pytest tests/unit/test_base_agent.py -v > tests/results/base_agent_test.log 2>&1

# Planner Agent with log
pytest tests/unit/test_planner_agent.py -v > tests/results/planner_agent_test.log 2>&1

# Researcher Agent with log
pytest tests/unit/test_researcher_agent.py -v > tests/results/researcher_agent_test.log 2>&1

# Coder Agent with log
pytest tests/unit/test_coder_agent.py -v > tests/results/coder_agent_test.log 2>&1

# Reporter Agent with log
pytest tests/unit/test_reporter_agent.py -v > tests/results/reporter_agent_test.log 2>&1

# Integration tests with log
pytest tests/integration/ -v > tests/results/integration_tests.log 2>&1

# E2E tests with log
pytest tests/e2e/ -v > tests/results/e2e_tests.log 2>&1
```

---

## 6. Final Comprehensive Test

### Complete System Test

```bash
# Final comprehensive test - all tests
pytest tests/ -v --tb=short

# Final test with detailed output
pytest tests/ -v --tb=long

# Final test with coverage report
pytest tests/ --cov=research_assistant --cov-report=term-missing --cov-report=html -v

# Final test and save comprehensive log
pytest tests/ -v --tb=short > tests/results/final_comprehensive_test.log 2>&1
```

### Final Test with Summary

```bash
# Run final test and show summary
pytest tests/ -v --tb=line | tee tests/results/final_test_summary.txt
```

---

## 7. Quick Reference Commands

### Most Common Commands

```bash
# 1. Set PYTHONPATH (run once per terminal session)
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# 2. Run all unit tests
pytest tests/unit/ -v

# 3. Run all integration tests
pytest tests/integration/ -v

# 4. Run all e2e tests
pytest tests/e2e/ -v

# 5. Run everything (final comprehensive test)
pytest tests/ -v

# 6. Run with coverage
pytest tests/ --cov=research_assistant --cov-report=html -v
```

---

## 8. Test Execution for Screenshots

### Commands to Run Before Capturing Screenshots

```bash
# Unit Tests - Base Agent (for screenshot)
pytest tests/unit/test_base_agent.py -v

# Unit Tests - Planner Agent
pytest tests/unit/test_planner_agent.py -v

# Unit Tests - Researcher Agent
pytest tests/unit/test_researcher_agent.py -v

# Unit Tests - Coder Agent
pytest tests/unit/test_coder_agent.py -v

# Unit Tests - Reporter Agent
pytest tests/unit/test_reporter_agent.py -v

# Unit Tests - Tools
pytest tests/unit/test_tavily_tool.py tests/unit/test_repl_tool.py -v

# Integration Tests
pytest tests/integration/ -v

# E2E Tests
pytest tests/e2e/ -v

# Final Comprehensive Test
pytest tests/ -v
```

---

## 9. Advanced Options

### Verbose Output Options

```bash
# Very verbose (show all print statements)
pytest tests/ -vv -s

# Show local variables on failure
pytest tests/ -v --tb=long -l

# Show only failures
pytest tests/ -v --tb=short -q
```

### Parallel Execution

```bash
# Install pytest-xdist first: pip install pytest-xdist
# Then run tests in parallel
pytest tests/ -n auto -v
```

### Stop on First Failure

```bash
# Stop after first failure
pytest tests/ -v -x

# Stop after N failures
pytest tests/ -v --maxfail=3
```

---

## 10. Complete Test Execution Sequence

### Recommended Order for Complete Testing

```bash
# Step 1: Set environment
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Step 2: Run unit tests (one by one)
pytest tests/unit/test_base_agent.py -v
pytest tests/unit/test_planner_agent.py -v
pytest tests/unit/test_researcher_agent.py -v
pytest tests/unit/test_coder_agent.py -v
pytest tests/unit/test_reporter_agent.py -v
pytest tests/unit/test_tavily_tool.py -v
pytest tests/unit/test_repl_tool.py -v

# Step 3: Run integration tests
pytest tests/integration/ -v

# Step 4: Run e2e tests
pytest tests/e2e/ -v

# Step 5: Final comprehensive test
pytest tests/ -v --tb=short

# Step 6: Generate coverage report
pytest tests/ --cov=research_assistant --cov-report=html -v
```

---

## 11. Troubleshooting

### If tests fail with import errors:

```bash
# Make sure PYTHONPATH is set
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Verify imports work
python -c "from research_assistant.agents.base import BaseReActAgent; print('OK')"
```

### If you need to see full error details:

```bash
# Show full traceback
pytest tests/ -v --tb=long

# Show local variables
pytest tests/ -v --tb=long -l
```

---

## Quick Copy-Paste Commands

### For Individual Test Cases:

```bash
# Base Agent
pytest tests/unit/test_base_agent.py::TestBaseAgentInitialization::test_initialization_with_llm_and_prompt -v

# Planner Agent
pytest tests/unit/test_planner_agent.py::TestPlannerAgentInitialization::test_initialization_with_default_llm -v

# Researcher Agent
pytest tests/unit/test_researcher_agent.py::TestResearcherAgentInitialization::test_initialization_with_default_llm -v

# Coder Agent
pytest tests/unit/test_coder_agent.py::TestCoderAgentInitialization::test_initialization_with_default_llm -v

# Reporter Agent
pytest tests/unit/test_reporter_agent.py::TestReporterAgentInitialization::test_initialization_with_default_llm -v
```

### For Final Comprehensive Test:

```bash
# Simple comprehensive test
pytest tests/ -v

# Comprehensive test with coverage
pytest tests/ --cov=research_assistant --cov-report=html --cov-report=term-missing -v

# Comprehensive test with log
pytest tests/ -v > tests/results/final_comprehensive_test.log 2>&1
```

---

**Note:** All commands assume you're in the project root directory:
```bash
cd /Users/anmolmittal/Documents/DataScience/masters/mtech_semester_1/Data\ Engineering/project/researcher_assistant
```

