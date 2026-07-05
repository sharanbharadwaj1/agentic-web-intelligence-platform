from state import AgentState


def dict_to_state(d: dict) -> AgentState:
    state = AgentState(goal=d.get("goal"))
    for k, v in d.items():
        setattr(state, k, v)
    return state


def state_to_dict(state: AgentState) -> dict:
    return state.__dict__

