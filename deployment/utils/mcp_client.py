# utils/mcp_client.py
import asyncio
import logging
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def call_mcp_agent(url: str, tool_name: str, arguments: dict) -> dict:
    try:
        async with streamablehttp_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                if result is None:
                    logger.error(f"No result from {tool_name} at {url}")
                    return {"summary": "Error: No response from server", "error": "No result"}
                return result.structuredContent if result.structuredContent else {"summary": "No structured content available", "error": "Empty response"}
    except Exception as e:
        logger.error(f"Error calling {tool_name} at {url}: {str(e)}")
        return {"summary": f"Error: {str(e)}", "error": str(e)}

def sync_call_mcp_agent(url: str, tool_name: str, arguments: dict) -> dict:
    return asyncio.run(call_mcp_agent(url, tool_name, arguments))


