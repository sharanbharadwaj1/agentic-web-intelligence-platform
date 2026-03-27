from state import AgentState


def dict_to_state(d: dict) -> AgentState:
    state = AgentState(goal=d.get("goal"))
    for k, v in d.items():
        setattr(state, k, v)
    return state


def state_to_dict(state: AgentState) -> dict:
    return state.__dict__

# from state import AgentState
# from tools.fetch_static import FetchStaticTool
# from tools.fetch_selenium import FetchSeleniumTool
# from tools.extract_rule import ExtractRuleTool
# from tools.extract_llm import ExtractLLMTool
# from tools.summarizer import SummarizeTool
# from orchestrator.manager import WorkflowManager


# manager = WorkflowManager()


# # -------- Full Pipeline --------

# def run_pipeline(state_dict: dict):
#     return manager.run_url_task(state_dict)


# # -------- Atomic Tools --------

# def fetch_static(state_dict: dict):
#     state = AgentState.from_dict(state_dict)
#     tool = FetchStaticTool()
#     tool.run(state)
#     return state.to_dict()


# def fetch_selenium(state_dict: dict):
#     state = AgentState.from_dict(state_dict)
#     tool = FetchSeleniumTool()
#     tool.run(state)
#     return state.to_dict()


# def extract_rule(state_dict: dict):
#     state = AgentState.from_dict(state_dict)
#     tool = ExtractRuleTool()
#     tool.run(state)
#     return state.to_dict()


# def extract_llm(state_dict: dict):
#     state = AgentState.from_dict(state_dict)
#     tool = ExtractLLMTool()
#     tool.run(state)
#     return state.to_dict()


# def summarize(state_dict: dict):
#     state = AgentState.from_dict(state_dict)
#     tool = SummarizeTool()
#     tool.run(state)
#     return state.to_dict()
