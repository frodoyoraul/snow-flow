#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    var_id = "e01cab1a4f334200086eeed18110c71f"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"🔍 Buscando sc_item_option con sys_id={var_id}...")
                var = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_item_option",
                    "sys_id": var_id,
                    "display_value": False
                })
                
                var_data = json.loads(var.content[0].text)
                
                if not var_data.get("success"):
                    print(f"❌ Variable no encontrada: {var_data.get('error')}")
                    return
                
                record = var_data["data"]["record"]
                print(f"✅ Variable encontrada: {record.get('name') or record.get('question_text')}")
                
                print("\n📦 Campos de la variable:")
                for key, val in sorted(record.items()):
                    if key not in ["_url"]:
                        print(f"  {key}: {val}")
                
                # Si esta variable es parte de un set, puede haber más variables asociadas
                # Buscar otras variables con el mismo variable_set
                var_set = record.get("variable_set") or record.get("variable_set_id")
                if var_set:
                    if isinstance(var_set, dict):
                        var_set = var_set.get("value")
                    if var_set:
                        print(f"\n🔍 Buscando otras variables en el mismo variable_set: {var_set}")
                        others = await session.call_tool("snow_record_manage", {
                            "action": "query",
                            "table": "sc_item_option",
                            "query": f"variable_set={var_set}",
                            "limit": 50,
                            "display_value": False
                        })
                        others_data = json.loads(others.content[0].text)
                        others_records = others_data["data"]["records"]
                        print(f"📚 Variables en el set: {len(others_records)}\n")
                        
                        for v in others_records:
                            name = v.get("name") or v.get("question_text") or v.get("sys_id")
                            req = v.get("required", False)
                            dtype = v.get("type") or v.get("data_type") or "string"
                            default = v.get("default_value")
                            print(f"🔸 {name} (tipo: {dtype}, required: {req}, default: {default})")
                        
                        print("\n💡 Para ordenar el catálogo, pasa 'variables' con pares nombre:valor para estas variables.")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
