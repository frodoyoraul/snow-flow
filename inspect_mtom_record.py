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
                
                # Obtener un registro de sc_item_option_mtom para ver sus campos completos
                print("Obteniendo un registro de sc_item_option_mtom con display_value=True...")
                rec = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option_mtom",
                    "query": "cat_item=68a7f85d472f7290a3978f59e16d43af",
                    "limit": 1,
                    "display_value": True
                })
                
                rec_data = json.loads(rec.content[0].text)
                record = rec_data["data"]["records"][0] if rec_data["data"]["records"] else {}
                
                print("\n📄 Registro completo:")
                print(json.dumps(record, indent=2, ensure_ascii=False))
                
                # Ver si existe campo 'sc_item_option' y 'cat_item'
                if "sc_item_option" in record:
                    opt_ref = record["sc_item_option"]
                    if isinstance(opt_ref, dict):
                        opt_id = opt_ref.get("value")
                    else:
                        opt_id = opt_ref
                    print(f"\n🔗 Este registro apunta a sc_item_option: {opt_id}")
                    
                    # Obtener esa variable
                    if opt_id:
                        var = await session.call_tool("snow_record_manage", {
                            "action": "get",
                            "table": "sc_item_option",
                            "sys_id": opt_id,
                            "display_value": False
                        })
                        var_data = json.loads(var.content[0].text)
                        var_record = var_data["data"]["record"]
                        print("\n📦 Variable (sc_item_option):")
                        print(json.dumps(var_record, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
