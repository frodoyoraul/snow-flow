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
                
                # 1. Descubrir la estructura de sc_item_option_mtom
                print("🔍 Descubriendo estructura de sc_item_option_mtom...")
                schema = await session.call_tool("snow_discover_table_fields", {
                    "table_name": "sc_item_option_mtom",
                    "include_relationships": True
                })
                
                schema_data = json.loads(schema.content[0].text)
                print(json.dumps(schema_data, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
