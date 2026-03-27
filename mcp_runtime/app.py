from mcp.server.fastmcp import FastMCP

from mcp_runtime.adapter import dict_to_state, state_to_dict

from tools.fetch_static import FetchStaticTool
from tools.fetch_selenium import FetchSeleniumTool
from tools.extract_rule import ExtractRuleTool
from tools.extract_llm import ExtractLLMTool
from tools.summarizer import SummarizeTool

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = FastMCP("aiagent")

# ---------------- FETCH ----------------

@server.tool()
async def fetch_static(state: dict) -> dict:
    agent_state = dict_to_state(state)
    FetchStaticTool().run(agent_state)
    return state_to_dict(agent_state)


@server.tool()
async def fetch_selenium(state: dict) -> dict:
    agent_state = dict_to_state(state)
    FetchSeleniumTool().run(agent_state)
    return state_to_dict(agent_state)


# ---------------- EXTRACT ----------------

@server.tool()
async def extract_rule(state: dict) -> dict:
    agent_state = dict_to_state(state)
    ExtractRuleTool().run(agent_state)
    return state_to_dict(agent_state)


@server.tool()
async def extract_llm(state: dict) -> dict:
    agent_state = dict_to_state(state)
    ExtractLLMTool().run(agent_state)
    return state_to_dict(agent_state)


# ---------------- SUMMARIZE ----------------

@server.tool()
async def summarize(state: dict) -> dict:
    agent_state = dict_to_state(state)
    SummarizeTool().run(agent_state)
    return state_to_dict(agent_state)


if __name__ == "__main__":
    logger.info(">>> AIAGENT MCP SERVER STARTED <<<")
    server.run()