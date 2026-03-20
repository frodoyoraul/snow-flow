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
                
                # 1. Obtener el catálogo con campos relacionados (variable_set, etc.)
                print("1. Catálogo completo...")
                cat = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": cat_item_id,
                    "display_value": False,
                    "fields": ["sys_id", "name", "variable_set", "variable_set_id", "sc_template", "sp_widget", "flow_designer_flow"]
                })
                cat_data = json.loads(cat.content[0].text)
                cat_record = cat_data["data"]["record"]
                print(json.dumps(cat_record, indent=2, ensure_ascii=False))
                
                # Extraer variable_set
                var_set = None
                for field in ["variable_set", "variable_set_id"]:
                    val = cat_record.get(field)
                    if val:
                        if isinstance(val, dict):
                            var_set = val.get("value")
                        else:
                            var_set = val
                        break
                
                print(f"\n2. Variable Set detectado: {var_set or 'No tiene'}")
                
                # Si hay variable_set, buscar las variables asociadas (sc_item_option)
                if var_set:
                    print(f"\n3. Buscando sc_item_option con variable_set={var_set}...")
                    vars_q = await session.call_tool("snow_record_manage", {
                        "action": "query",
                        "table": "sc_item_option",
                        "query": f"variable_set={var_set}",
                        "limit": 100,
                        "display_value": True
                    })
                    vars_data = json.loads(vars_q.content[0].text)
                    var_records = vars_data["data"]["records"]
                    print(f"   Variables encontradas: {len(var_records)}\n")
                    
                    for v in var_records:
                        # Con display_value=True, los campos vienen como {"display_value": "...", "value": "..."}
                        def get(val):
                            if isinstance(val, dict):
                                return val.get("display_value") or val.get("value") or ""
                            return val or ""
                        
                        name = get(v.get("name") or v.get("question_text"))
                        dtype = get(v.get("type") or v.get("data_type"))
                        required = get(v.get("required"))
                        default = get(v.get("default_value"))
                        
                        # Saltar si name está vacío
                        if not name:
                            continue
                            
                        print(f"🔸 {name}")
                        print(f"   Tipo: {dtype}, Required: {required}, Default: {default}")
                    
                    # Crear plantilla de variables
                    var_template = {}
                    for v in var_records:
                        name = get(v.get("name") or v.get("question_text"))
                        if name:
                            var_template[name] = ""
                    if var_template:
                        print("\n💡 Para ordenar, usa 'variables':")
                        print(json.dumps(var_template, indent=2, ensure_ascii=False))
                
                # 4. Alternativamente, buscar variables a través de sc_item_option_mtom con cat_item directo
                print("\n4. Buscando variables directamente vinculadas al catálogo (sc_item_option_mtom con cat_item)...")
                mtom_q = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option_mtom",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 200,
                    "display_value": False,
                    "fields": ["sys_id", "sc_item_option"]
                })
                mtom_data = json.loads(mtom_q.content[0].text)
                mtom_records = mtom_data["data"]["records"]
                print(f"   Relaciones encontradas: {len(mtom_records)}")
                
                # Extraer IDs de sc_item_option
                option_ids = []
                for r in mtom_records:
                    opt = r.get("sc_item_option")
                    if isinstance(opt, dict):
                        opt_id = opt.get("value")
                    else:
                        opt_id = opt
                    if opt_id and opt_id not in option_ids:
                        option_ids.append(opt_id)
                
                print(f"   Variables únicas: {len(option_ids)}")
                
                if option_ids:
                    # Obtener detalles de esas variables
                    batch_size = 50
                    all_vars = []
                    for i in range(0, len(option_ids), batch_size):
                        batch = option_ids[i:i+batch_size]
                        query = "sys_id=" + ",".join(batch)
                        var_batch = await session.call_tool("snow_record_manage", {
                            "action": "query",
                            "table": "sc_item_option",
                            "query": query,
                            "limit": batch_size,
                            "display_value": True
                        })
                        var_batch_data = json.loads(var_batch.content[0].text)
                        all_vars.extend(var_batch_data["data"]["records"])
                    
                    print(f"\n5. Detalles de {len(all_vars)} variables desde sc_item_option:\n")
                    for v in all_vars[:30]:
                        def get(val):
                            if isinstance(val, dict):
                                return val.get("display_value") or val.get("value") or ""
                            return val or ""
                        
                        name = get(v.get("name") or v.get("question_text"))
                        dtype = get(v.get("type") or v.get("data_type"))
                        required = get(v.get("required"))
                        if not name:
                            name = v.get("sys_id", "N/A")
                        print(f"🔸 {name} (tipo: {dtype}, req: {required})")
                    
                    var_template2 = {}
                    for v in all_vars:
                        name = get(v.get("name") or v.get("question_text"))
                        if name:
                            var_template2[name] = ""
                    if var_template2:
                        print("\n💡 Plantilla alternativa (desde sc_item_option):")
                        print(json.dumps(var_template2, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
