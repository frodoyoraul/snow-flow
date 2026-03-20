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
                print("✅ Conectado al MCP proxy")
                
                # Obtener el catalog item usando snow_record_manage
                result = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": "68a7f85d472f7290a3978f59e16d43af",
                    "display_value": True
                })
                
                print("\n📦 Registro de sc_cat_item:")
                print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
