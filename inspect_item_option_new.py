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
                
                # Inspeccionar una variable para ver todos sus campos
                var_id = "70c6a0ff47c73e50a3978f59e16d4324"
                print(f"Inspeccionando item_option_new {var_id} con display_value=False...")
                var = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "item_option_new",
                    "sys_id": var_id,
                    "display_value": False
                })
                
                var_data = json.loads(var.content[0].text)
                record = var_data["data"]["record"]
                
                print("\n📦 Todos los campos de la variable:")
                for key, val in sorted(record.items()):
                    print(f"{key}: {val}")
                
                # También describir la tabla item_option_new
                print("\n🔍 Descubriendo estructura de item_option_new...")
                schema = await session.call_tool("snow_discover_table_fields", {
                    "table_name": "item_option_new"
                })
                schema_data = json.loads(schema.content[0].text)
                print(json.dumps(schema_data, indent=2, ensure_ascii=False))
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
