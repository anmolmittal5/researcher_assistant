#!/usr/bin/env python3
"""Test execution script for systematic test running and reporting."""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
import json

TEST_DIR = Path(__file__).parent.parent / "tests"
RESULTS_DIR = TEST_DIR / "results"
SCREENSHOTS_DIR = TEST_DIR / "screenshots"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

TEST_SUITES = {
    "Unit Tests": {
        "Base Agent": "tests/unit/test_base_agent.py",
        "Planner Agent": "tests/unit/test_planner_agent.py",
        "Researcher Agent": "tests/unit/test_researcher_agent.py",
        "Coder Agent": "tests/unit/test_coder_agent.py",
        "Reporter Agent": "tests/unit/test_reporter_agent.py",
        "Tavily Tool": "tests/unit/test_tavily_tool.py",
        "Python REPL Tool": "tests/unit/test_repl_tool.py",
    },
    "Integration Tests": {
        "Agent Workflow": "tests/integration/test_agent_workflow.py",
        "Tool Integration": "tests/integration/test_tool_integration.py",
        "State Management": "tests/integration/test_state_management.py",
        "Workflow Orchestration": "tests/integration/test_workflow_orchestration.py",
    },
    "End-to-End Tests": {
        "Full Workflow": "tests/e2e/test_full_workflow.py",
    }
}

INDIVIDUAL_TESTS = [
    ("Base Agent - Initialization", "tests/unit/test_base_agent.py::TestBaseAgentInitialization"),
    ("Base Agent - Tool Execution", "tests/unit/test_base_agent.py::TestToolExecution"),
    ("Base Agent - Response Parsing", "tests/unit/test_base_agent.py::TestResponseParsing"),
    ("Base Agent - ReAct Loop", "tests/unit/test_base_agent.py::TestReActLoop"),
    ("Planner Agent - Initialization", "tests/unit/test_planner_agent.py::TestPlannerAgentInitialization"),
    ("Planner Agent - Plan Method", "tests/unit/test_planner_agent.py::TestPlanMethod"),
    ("Planner Agent - Routing Logic", "tests/unit/test_planner_agent.py::TestRoutingLogic"),
    ("Researcher Agent - Initialization", "tests/unit/test_researcher_agent.py::TestResearcherAgentInitialization"),
    ("Researcher Agent - Research Method", "tests/unit/test_researcher_agent.py::TestResearchMethod"),
    ("Coder Agent - Initialization", "tests/unit/test_coder_agent.py::TestCoderAgentInitialization"),
    ("Coder Agent - Code Method", "tests/unit/test_coder_agent.py::TestCodeMethod"),
    ("Reporter Agent - Initialization", "tests/unit/test_reporter_agent.py::TestReporterAgentInitialization"),
    ("Reporter Agent - Synthesize Method", "tests/unit/test_reporter_agent.py::TestSynthesizeMethod"),
    ("Tavily Tool - Initialization", "tests/unit/test_tavily_tool.py::TestTavilyToolInitialization"),
    ("Python REPL Tool - Initialization", "tests/unit/test_repl_tool.py::TestPythonREPLToolInitialization"),
]

test_results = {
    "execution_date": datetime.now().isoformat(),
    "test_suites": {},
    "individual_tests": {},
    "summary": {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0
    }
}


def run_test(test_path, test_name, category="General"):
    """Run a single test and capture results."""
    print(f"\n{'='*80}")
    print(f"Running: {test_name}")
    print(f"Path: {test_path}")
    print(f"{'='*80}\n")
    
    log_file = RESULTS_DIR / f"{test_name.replace(' ', '_').replace('-', '_').lower()}.log"
    
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_path}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = str(src_path)
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v", "--tb=short", "--color=yes"],
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
            cwd=project_root
        )
        
        with open(log_file, "w") as f:
            f.write(f"Test: {test_name}\n")
            f.write(f"Path: {test_path}\n")
            f.write(f"Category: {category}\n")
            f.write(f"Execution Time: {datetime.now().isoformat()}\n")
            f.write(f"{'='*80}\n\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n\nSTDERR:\n")
            f.write(result.stderr)
            f.write(f"\n\nExit Code: {result.returncode}\n")
        
        output = result.stdout + result.stderr
        passed = output.count("PASSED")
        failed = output.count("FAILED")
        skipped = output.count("SKIPPED")
        errors = output.count("ERROR")
        
        test_result = {
            "status": "PASSED" if result.returncode == 0 else "FAILED",
            "exit_code": result.returncode,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "log_file": str(log_file),
            "output": output[:1000]
        }
        
        print(f"Status: {test_result['status']}")
        print(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}, Errors: {errors}")
        
        return test_result
        
    except subprocess.TimeoutExpired:
        print(f"ERROR: Test timed out after 5 minutes")
        return {
            "status": "TIMEOUT",
            "exit_code": -1,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 1,
            "log_file": str(log_file),
            "output": "Test execution timed out"
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            "status": "ERROR",
            "exit_code": -1,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 1,
            "log_file": str(log_file),
            "output": str(e)
        }


def run_all_tests():
    """Run all test suites systematically."""
    print("\n" + "="*80)
    print("COGNIVIA RESEARCH ASSISTANT - TEST EXECUTION")
    print("="*80)
    print(f"Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Results Directory: {RESULTS_DIR}")
    print(f"Screenshots Directory: {SCREENSHOTS_DIR}")
    print("="*80 + "\n")
    
    for suite_name, tests in TEST_SUITES.items():
        print(f"\n{'#'*80}")
        print(f"# {suite_name}")
        print(f"{'#'*80}\n")
        
        suite_results = {}
        for test_name, test_path in tests.items():
            result = run_test(test_path, f"{suite_name} - {test_name}", suite_name)
            suite_results[test_name] = result
            
            test_results["summary"]["total_tests"] += 1
            test_results["summary"]["passed"] += result["passed"]
            test_results["summary"]["failed"] += result["failed"]
            test_results["summary"]["skipped"] += result["skipped"]
            test_results["summary"]["errors"] += result["errors"]
        
        test_results["test_suites"][suite_name] = suite_results
    
    print(f"\n{'#'*80}")
    print(f"# Individual Test Cases")
    print(f"{'#'*80}\n")
    
    for test_name, test_path in INDIVIDUAL_TESTS:
        result = run_test(test_path, test_name, "Individual")
        test_results["individual_tests"][test_name] = result
    
    print(f"\n{'#'*80}")
    print(f"# Final Comprehensive Test - Overall Functionality")
    print(f"{'#'*80}\n")
    
    final_result = run_test("tests/", "Final Comprehensive Test - All Tests", "Final")
    test_results["final_test"] = final_result
    
    results_json = RESULTS_DIR / "test_results.json"
    with open(results_json, "w") as f:
        json.dump(test_results, f, indent=2)
    
    print("\n" + "="*80)
    print("TEST EXECUTION SUMMARY")
    print("="*80)
    print(f"Total Test Suites: {len(test_results['test_suites'])}")
    print(f"Total Individual Tests: {len(test_results['individual_tests'])}")
    print(f"\nOverall Results:")
    print(f"  Passed: {test_results['summary']['passed']}")
    print(f"  Failed: {test_results['summary']['failed']}")
    print(f"  Skipped: {test_results['summary']['skipped']}")
    print(f"  Errors: {test_results['summary']['errors']}")
    print(f"\nResults saved to: {results_json}")
    print("="*80 + "\n")
    
    return test_results


if __name__ == "__main__":
    try:
        results = run_all_tests()
        sys.exit(0 if results["summary"]["failed"] == 0 and results["summary"]["errors"] == 0 else 1)
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error during test execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

