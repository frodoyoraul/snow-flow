#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    var_set_id = "e01cab1a4f334200086eeed18110c71f"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # Probar en sys_script (Variable Set)
                print(f"🔍 Buscando en sys_script con sys_id={var_set_id}...")
                script = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sys_script",
                    "sys_id": var_set_id,
                    "display_value": False
                })
                
                script_data = json.loads(script.content[0].text)
                if script_data.get("success"):
                    record = script_data["data"]["record"]
                    print(f"✅ Encontrado en sys_script: {record.get('name')} (tipo: {record.get('sys_class_name')})")
                    # Los variable sets en sys_script pueden tener un campo 'variable_set' que apunta a otras variables? No.
                    # Normalmente, los variable sets son de tipo 'sys_script' con 'script_type=variable_set'
                    return
                else:
                    print(f"❌ No en sys_script: {script_data.get('error')}")
                
                # Probar en sp_widget de nuevo pero con búsqueda por nombre si conocemos el nombre
                # El enlace que diste es de item_option_new_list.do que muestra sc_item_option que tienen variable_set=<id>
                # Eso significa que en sc_item_option existe un campo 'variable_set' que referencia a un ID.
                # Buscar sc_item_option que tengan ese variable_set
                print(f"\n🔍 Buscando sc_item_option donde variable_set={var_set_id}...")
                vars_set = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option",
                    "query": f"variable_set={var_set_id}",
                    "limit": 50,
                    "display_value": False
                })
                
                vars_data = json.loads(vars_set.content[0].text)
                records = vars_data["data"]["records"]
                print(f"📚 Variables encontradas: {len(records)}\n")
                
                if records:
                    print("📋 Lista de variables:")
                    for v in records:
                        name = v.get("name") or v.get("question_text") or v.get("sys_id")
                        req = v.get("required", False)
                        dtype = v.get("type") or v.get("data_type") or "string"
                        default = v.get("default_value")
                        print(f"  - {name} (tipo: {dtype}, required: {req}, default: {default})")
                    
                    # Crear plantilla de variables
                    var_template = {}
                    for v in records:
                        name = v.get("name") or v.get("question_text")
                        if name:
                            var_template[name] = ""
                    print("\n💡 Plantilla para 'variables':")
                    print(json.dumps(var_template, indent=2, ensure_ascii=False))
                else:
                    print("No se encontraron variables asociadas a ese variable_set.")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
