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
                
                # 1. Obtener la categoría del catálogo
                cat = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": cat_item_id,
                    "display_value": False,
                    "fields": ["category"]
                })
                cat_data = json.loads(cat.content[0].text)
                record = cat_data["data"]["record"]
                category_ref = record.get("category")
                if isinstance(category_ref, dict):
                    category_id = category_ref.get("value")
                else:
                    category_id = category_ref
                
                print(f"Categoría detectada: {category_id}")
                
                if category_id:
                    cat_cat = await session.call_tool("snow_record_manage", {
                        "action": "get",
                        "table": "sc_category",
                        "sys_id": category_id,
                        "display_value": False
                    })
                    cat_cat_data = json.loads(cat_cat.content[0].text)
                    cat_cat_record = cat_cat_data["data"]["record"]
                    
                    # Buscar variable_set en la categoría
                    cat_var_set = cat_cat_record.get("variable_set") or cat_cat_record.get("variable_set_id")
                    if cat_var_set:
                        if isinstance(cat_var_set, dict):
                            cat_var_set = cat_var_set.get("value")
                        print(f"Categoría tiene variable_set: {cat_var_set}")
                
                # 2. Buscar item_option_new que tengan cat_item directamente (asociación posible)
                print(f"\nBuscando item_option_new con cat_item={cat_item_id}...")
                direct_vars = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 100,
                    "display_value": True
                })
                direct_data = json.loads(direct_vars.content[0].text)
                direct_records = direct_data["data"]["records"]
                print(f"Variables directas encontradas: {len(direct_records)}\n")
                
                if direct_records:
                    for v in direct_records:
                        def get(val):
                            if isinstance(val, dict):
                                return val.get("display_value") or val.get("value") or ""
                            return val or ""
                        
                        name = get(v.get("name") or v.get("question_text"))
                        dtype = get(v.get("type") or v.get("data_type"))
                        required = get(v.get("required"))
                        default = get(v.get("default_value"))
                        print(f"🔸 {name or v.get('sys_id')} (tipo: {dtype}, required: {required})")
                    
                    var_template = {}
                    for v in direct_records:
                        name = get(v.get("name") or v.get("question_text"))
                        if name:
                            var_template[name] = ""
                    print("\n💡 Plantilla de variables para ordenar:")
                    print(json.dumps(var_template, indent=2, ensure_ascii=False))
                else:
                    print("No se encontraron variables directas item_option_new con cat_item.")
                    
                # 3. Si aún no hay, buscar todas las item_option_new y filtrar por sys_id específico dado
                specific_id = "70c6a0ff47c73e50a3978f59e16d4324"
                print(f"\nBuscando la variable específica {specific_id}...")
                spec = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "item_option_new",
                    "sys_id": specific_id,
                    "display_value": True
                })
                spec_data = json.loads(spec.content[0].text)
                if spec_data.get("success"):
                    spec_rec = spec_data["data"]["record"]
                    def get(val):
                        if isinstance(val, dict):
                            return val.get("display_value") or val.get("value") or ""
                        return val or ""
                    name = get(spec_rec.get("name") or spec_rec.get("question_text"))
                    print(f"Variable específica encontrada: {name or specific_id}")
                else:
                    print(f"No se encontró la variable específica: {spec_data.get('error')}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
