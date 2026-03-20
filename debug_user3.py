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
                
                # Query con fields específicos
                result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=admin",
                    "limit": 1,
                    "display_value": False,
                    "fields": ["sys_id", "user_name"]  # Forzar incluir sys_id
                })
                
                data = json.loads(result.content[0].text)
                print(json.dumps(data, indent=2, ensure_ascii=False))
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
