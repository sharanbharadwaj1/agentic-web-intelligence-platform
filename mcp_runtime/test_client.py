import asyncio
import json
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_state(result):
    if result.isError:
        raise RuntimeError(f"Tool error: {result}")

    # Case 1: structured JSON (best)
    if result.structuredContent is not None:
        return result.structuredContent

    # Case 2: text JSON
    if result.content and result.content[0].text:
        return json.loads(result.content[0].text)

    # Nothing usable
    raise RuntimeError(f"No state returned from tool: {result}")


async def main():
    server = StdioServerParameters(
        command="python",
        args=["-m", "mcp_runtime.app"],
    )

    state = {
        "url": "https://news.ycombinator.com",
        "goal": "Extract top 5 headlines and summarize",
        "html": None,
        "headlines": None,
        "summary": None,
    }

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool("fetch_static", {"state": state})
            state = extract_state(result)

            result = await session.call_tool("extract_rule", {"state": state})
            state = extract_state(result)

            result = await session.call_tool("summarize", {"state": state})
            state = extract_state(result)

            logger.info("\nFINAL STATE:")
            logger.info(state)


if __name__ == "__main__":
    asyncio.run(main())