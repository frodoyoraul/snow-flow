#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # Query crudo para ver estructura
                result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option_mtom",
                    "query": "cat_item=68a7f85d472f7290a3978f59e16d43af",
                    "limit": 5,
                    "display_value": False
                })
                
                data = json.loads(result.content[0].text)
                print("Estructura de sc_item_option_mtom:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
