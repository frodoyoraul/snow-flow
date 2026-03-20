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
                
                # Obtener relaciones de variables
                direct_vars = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option_mtom",
                    "query": f"cat_item=68a7f85d472f7290a3978f59e16d43af",
                    "limit": 100,
                    "display_value": False
                })
                
                direct_data = json.loads(direct_vars.content[0].text)
                var_records = direct_data["data"]["records"]
                print(f"📚 Variables encontradas en sc_item_option_mtom: {len(var_records)}\n")
                
                # Recolectar sys_ids de las variables
                var_sys_ids = []
                for var in var_records:
                    option_ref = var.get("sc_item_option", {}).get("value") if isinstance(var.get("sc_item_option"), dict) else var.get("sc_item_option")
                    if option_ref:
                        var_sys_ids.append(option_ref)
                
                if not var_sys_ids:
                    print("❌ No se encontraron referencias a variables")
                    return
                
                # Obtener detalles de todas las variables en batch
                var_details = []
                for var_id in var_sys_ids[:20]:  # Limitar a 20 para no saturar
                    var_detail = await session.call_tool("snow_record_manage", {
                        "action": "get",
                        "table": "sc_item_option",
                        "sys_id": var_id,
                        "display_value": False
                    })
                    var_detail_data = json.loads(var_detail.content[0].text)
                    var_record = var_detail_data["data"]["record"]
                    var_details.append(var_record)
                
                print("📋 Detalle de variables (primeras 20):\n")
                for var in var_details:
                    name = var.get("name") or var.get("question_text") or var.get("sys_id")
                    req = var.get("required", False)
                    dtype = var.get("type") or var.get("data_type") or "string"
                    default = var.get("default_value")
                    choices = var.get("choices")  # Puede ser JSON con opciones
                    
                    print(f"🔸 {name}")
                    print(f"   Tipo: {dtype}")
                    print(f"   Required: {req}")
                    if default:
                        print(f"   Default: {default}")
                    if choices:
                        try:
                            choices_json = json.loads(choices) if isinstance(choices, str) else choices
                            print(f"   Opciones: {list(choices_json.keys())[:5]}...")
                        except:
                            pass
                    print()
                
                # Buscar también 'variable_set' del cat item
                cat_item_result = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": "68a7f85d472f7290a3978f59e16d43af",
                    "display_value": False
                })
                cat_item_data = json.loads(cat_item_result.content[0].text)
                cat_item = cat_item_data["data"]["record"]
                
                var_set = cat_item.get("variable_set", cat_item.get("variable_set_id"))
                if var_set:
                    if isinstance(var_set, dict):
                        var_set = var_set.get("value")
                    if var_set:
                        print(f"📦 El item tiene variable_set: {var_set}")
                        vs_vars = await session.call_tool("snow_record_manage", {
                            "action": "query",
                            "table": "sp_widget",
                            "query": f"sys_id={var_set}",
                            "display_value": False
                        })
                        vs_data = json.loads(vs_vars.content[0].text)
                        if vs_data["data"]["records"]:
                            vs_record = vs_data["data"]["records"][0]
                            option_schema = vs_record.get("option_schema")
                            if option_schema:
                                try:
                                    schema = json.loads(option_schema)
                                    print("\n📋 Variables definidas en option_schema del variable_set:")
                                    print(json.dumps(schema, indent=2))
                                except Exception as e:
                                    print(f"Error parseando option_schema: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
