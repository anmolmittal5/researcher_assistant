from datetime import datetime
from ..prompts import planner as planner_prompt_module

def build_prompt(goal: str, state: str = "", previous_results: str = "") -> str:
    time_str = datetime.utcnow().isoformat() + "Z"
    return planner_prompt_module.PLANNER_PROMPT.format(
        goal=goal,
        state=state,
        previous_results=previous_results,
        time=time_str,
    )

def plan(goal: str, state: str = "", previous_results: str = ""):
    return build_prompt(goal, state, previous_results)

if __name__ == "__main__":
    sample_goal = "Create planner agent v1"
    print(plan(sample_goal))
