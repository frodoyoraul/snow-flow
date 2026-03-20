#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    var_id = "70c6a0ff47c73e50a3978f59e16d4324"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"🔍 Buscando en item_option_new con sys_id={var_id}...")
                var = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "item_option_new",
                    "sys_id": var_id,
                    "display_value": True
                })
                
                var_data = json.loads(var.content[0].text)
                
                if not var_data.get("success"):
                    print(f"❌ No encontrada: {var_data.get('error')}")
                    # Probar en 'sp_widget' o 'sys_script'?
                    return
                
                record = var_data["data"]["record"]
                print("\n📦 Variable (item_option_new):")
                print(json.dumps(record, indent=2, ensure_ascii=False))
                
                def get(val):
                    if isinstance(val, dict):
                        return val.get("display_value") or val.get("value") or ""
                    return val or ""
                
                name = get(record.get("name") or record.get("question_text"))
                dtype = get(record.get("type") or record.get("data_type"))
                required = get(record.get("required"))
                default = get(record.get("default_value"))
                reference = get(record.get("reference"))
                
                print(f"\n🔹 Nombre: {name}")
                print(f"🔹 Tipo: {dtype}")
                print(f"🔹 Required: {required}")
                print(f"🔹 Default: {default}")
                if reference:
                    print(f"🔹 Reference: {reference}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
