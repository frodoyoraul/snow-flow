#!/usr/bin/env python3
import asyncio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                print("Connected. Listing tools...")
                tools = await session.list_tools()
                print(f"Tools available: {len(tools.tools)}")
                for t in tools.tools:
                    print(f"- {t.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
