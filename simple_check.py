#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    ritm_sys_id = "c2c0949a47f73e14a3978f59e16d4351"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"Variables del RITM {ritm_sys_id}:")
                result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"request_item={ritm_sys_id}",
                    "limit": 50,
                    "display_value": True
                })
                data = json.loads(result.content[0].text)
                records = data["data"]["records"]
                print(f"Total: {len(records)}\n")
                
                for v in records:
                    name = v.get("name") or v.get("question_text") or v.get("conversational_label") or v.get("sys_id")
                    val = v.get("value") or ""
                    print(f"- {name}: {val}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
