# orchestrator.py
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.critic import CriticAgent
from tools.registry import ToolRegistry
from aiagentplatform2.tools.extract_llm import ExtractLLMTool
from aiagentplatform2.tools.extract_rule import ExtractRuleTool
from aiagentplatform2.tools.fetch_selenium import FetchSeleniumTool
from aiagentplatform2.tools.fetch_static import FetchStaticTool
from aiagentplatform2.tools.summarizer import SummarizeTool
from state import AgentState

registry = ToolRegistry()
registry.register("fetch_static", FetchStaticTool())
registry.register("fetch_selenium", FetchSeleniumTool())
registry.register("extract_rule", ExtractRuleTool())
registry.register("extract_llm", ExtractLLMTool(llm_client))
registry.register("summarize", SummarizeTool())

planner = PlannerAgent()
executor = ExecutorAgent(registry)
critic = CriticAgent()

state = AgentState(goal="Summarize headlines", url="https://news.ycombinator.com")

while True:
    decision = planner.decide(state)
    action = decision["action"]

    if action == "finish":
        break

    try:
        executor.execute(action, state)
    except Exception as e:
        state.errors.append(str(e))
        # fallback path
        if action == "extract_rule":
            executor.execute("extract_llm", state)
        elif action == "fetch_static":
            executor.execute("fetch_selenium", state)

    ok, feedback = critic.validate(state)
    print("[Critic]", feedback)

    if not ok:
        # planner will pick fallback next loop
        continue
print("Final Summary:", state.summary)
