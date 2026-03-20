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
                
                cat_item_id = "68a7f85d472f7290a3978f59e16d43af"
                
                # 1. Obtener el catálogo nuevamente, pidiendo todos los campos relevantes
                print("1. Catálogo completo...")
                cat = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": cat_item_id,
                    "display_value": False
                })
                cat_data = json.loads(cat.content[0].text)
                record = cat_data["data"]["record"]
                
                # Buscar campos que puedan contener variable_set
                var_set_fields = ["variable_set", "variable_set_id", "item_option_new_set", "option_set"]
                var_set_id = None
                for f in var_set_fields:
                    val = record.get(f)
                    if val:
                        if isinstance(val, dict):
                            var_set_id = val.get("value")
                        else:
                            var_set_id = val
                        print(f"   Encontrado {f}: {var_set_id}")
                        break
                
                if not var_set_id:
                    print("   No se encontró variable_set en el catálogo.")
                    # Tal vez el catálogo no necesita variables? Pero dices que son obligatorias.
                    return
                
                # 2. Buscar item_option_new que tengan ese variable_set
                print(f"\n2. Buscando item_option_new con variable_set={var_set_id}...")
                vars_q = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"variable_set={var_set_id}",
                    "limit": 100,
                    "display_value": True
                })
                vars_data = json.loads(vars_q.content[0].text)
                var_records = vars_data["data"]["records"]
                print(f"   Variables encontradas: {len(var_records)}\n")
                
                if not var_records:
                    print("❌ No se encontraron variables en ese set.")
                    return
                
                # 3. Mostrar cada variable con su nombre
                for v in var_records:
                    def get(val):
                        if isinstance(val, dict):
                            return val.get("display_value") or val.get("value") or ""
                        return val or ""
                    
                    name = get(v.get("name") or v.get("question_text"))
                    dtype = get(v.get("type") or v.get("data_type"))
                    required = get(v.get("required"))
                    default = get(v.get("default_value"))
                    
                    if not name:
                        name = v.get("sys_id", "N/A")
                    print(f"🔸 {name}")
                    print(f"   Tipo: {dtype}, Required: {required}, Default: {default}")
                
                # 4. Crear plantilla de variables
                var_template = {}
                for v in var_records:
                    name = get(v.get("name") or v.get("question_text"))
                    if name:
                        var_template[name] = ""
                
                if var_template:
                    print("\n💡 Plantilla para 'variables' (valores vacíos):")
                    print(json.dumps(var_template, indent=2, ensure_ascii=False))
                else:
                    print("\n⚠️ No se encontraron nombres legibles.")
                
                # 5. Probar orden con esta plantilla
                print("\n5. Creando orden de prueba con Abraham Lincoln y variables vacías...")
                # Obtener Abraham
                abraham = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=abraham.lincoln",
                    "limit": 1,
                    "display_value": False,
                    "fields": ["sys_id"]
                })
                abr_data = json.loads(abraham.content[0].text)
                abr_records = abr_data["data"]["records"]
                if not abr_records:
                    print("❌ Abraham no encontrado")
                    return
                abr_sys_id = abr_records[0].get("sys_id")
                
                order = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": cat_item_id,
                    "requested_for": abr_sys_id,
                    "variables": var_template
                })
                order_data = json.loads(order.content[0].text)
                print("\n📦 Resultado de la orden:")
                print(json.dumps(order_data, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
