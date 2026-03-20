#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    cat_item_id = "68a7f85d472f7290a3978f59e16d43af"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # Obtener catálogo con TODOS los campos (sin display_value para ver valores crudos)
                print("1. Catálogo completo (all fields)...")
                cat = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": cat_item_id,
                    "display_value": False
                })
                cat_data = json.loads(cat.content[0].text)
                record = cat_data["data"]["record"]
                
                # Mostrar campos que contengan 'variable' o 'option' o 'set'
                print("\nCampos relevantes (variable/option/set):")
                for key, val in record.items():
                    key_low = key.lower()
                    if any(word in key_low for word in ["variable", "option", "set", "template", "widget"]):
                        print(f"  {key}: {val}")
                
                # 2. Buscar variable_set en la categoría
                category_ref = record.get("category")
                if category_ref:
                    if isinstance(category_ref, dict):
                        category_id = category_ref.get("value")
                    else:
                        category_id = category_ref
                    
                    if category_id:
                        print(f"\n2. Categoría: {category_id}")
                        cat_cat = await session.call_tool("snow_record_manage", {
                            "action": "get",
                            "table": "sc_category",
                            "sys_id": category_id,
                            "display_value": False
                        })
                        cat_cat_data = json.loads(cat_cat.content[0].text)
                        cat_cat_record = cat_cat_data["data"]["record"]
                        
                        for key, val in cat_cat_record.items():
                            key_low = key.lower()
                            if any(word in key_low for word in ["variable", "option", "set"]):
                                print(f"  {key}: {val}")
                
                # 3. Buscar en item_option_new con cat_item (ya lo hicimos, pero vamos a confirmar número total)
                print("\n3. Contando item_option_new con cat_item...")
                count_q = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 1,
                    "display_value": False
                })
                count_data = json.loads(count_q.content[0].text)
                total = count_data["data"].get("count", 0)
                print(f"   Total item_option_new: {total}")
                
                if total > 0:
                    # Obtener todos los sys_id de esas variables
                    all_vars = await session.call_tool("snow_record_manage", {
                        "action": "query",
                        "table": "item_option_new",
                        "query": f"cat_item={cat_item_id}",
                        "limit": total,
                        "display_value": False,
                        "fields": ["sys_id"]
                    })
                    all_data = json.loads(all_vars.content[0].text)
                    var_sys_ids = [v.get("sys_id") for v in all_data["data"]["records"]]
                    print(f"   IDs: {var_sys_ids}")
                
                # 4. Buscar en sc_item_option (tabla antigua) con cat_item
                print("\n4. Contando sc_item_option con cat_item...")
                old_count = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 1,
                    "display_value": False
                })
                old_data = json.loads(old_count.content[0].text)
                old_total = old_data["data"].get("count", 0)
                print(f"   Total sc_item_option: {old_total}")
                
                # 5. Posible variable set: buscar en sp_widget si el catálogo tiene widget con option_schema
                widget_ref = record.get("sp_widget") or record.get("widget")
                if widget_ref:
                    if isinstance(widget_ref, dict):
                        widget_id = widget_ref.get("value")
                    else:
                        widget_id = widget_ref
                    
                    if widget_id:
                        print(f"\n5. Catálogo tiene widget: {widget_id}")
                        widget = await session.call_tool("snow_record_manage", {
                            "action": "get",
                            "table": "sp_widget",
                            "sys_id": widget_id,
                            "display_value": False
                        })
                        widget_data = json.loads(widget.content[0].text)
                        widget_record = widget_data["data"]["record"]
                        option_schema = widget_record.get("option_schema")
                        if option_schema:
                            try:
                                schema = json.loads(option_schema)
                                print("   Widget option_schema properties:")
                                print(json.dumps(schema.get("properties", {}), indent=2))
                            except:
                                print(f"   option_schema raw: {option_schema[:200]}...")
                
                # 6. Buscar variable_set directamente en item_option_new_set u otras tablas
                # Preguntar si existe una tabla que almacene sets de variables: item_option_new_set?
                # Probemos: listar tablas que contengan 'variable_set' en el nombre? Mejor no.
                
                # Conclusión: mostrar todas las variables encontradas en item_option_new con sus etiquetas
                if total > 0:
                    print(f"\n6. Listando {min(10, total)} variables de item_option_new con etiquetas:")
                    all_vars_full = await session.call_tool("snow_record_manage", {
                        "action": "query",
                        "table": "item_option_new",
                        "query": f"cat_item={cat_item_id}",
                        "limit": 10,
                        "display_value": True
                    })
                    all_full_data = json.loads(all_vars_full.content[0].text)
                    for v in all_full_data["data"]["records"]:
                        # Extraer posibles etiquetas
                        label_candidates = ["conversational_label", "label", "name", "question_text", "description"]
                        label = None
                        for cand in label_candidates:
                            val = v.get(cand)
                            if val:
                                if isinstance(val, dict):
                                    lbl = val.get("display_value") or val.get("value")
                                else:
                                    lbl = val
                                if lbl:
                                    label = lbl
                                    break
                        if not label:
                            label = "(sin etiqueta)"
                        print(f"  - {label} (sys_id: {v.get('sys_id')})")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
