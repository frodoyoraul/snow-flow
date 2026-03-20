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
                
                # Traer las variables con display_value true para ver etiquetas
                print("🔍 Obteniendo sc_item_option con display_value=True...")
                vars_set = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option",
                    "query": f"variable_set={var_set_id}",
                    "limit": 50,
                    "display_value": True
                })
                
                vars_data = json.loads(vars_set.content[0].text)
                records = vars_data["data"]["records"]
                print(f"📚 Variables encontradas: {len(records)}\n")
                
                # Mostrar cada variable con sus campos clave
                for v in records:
                    # Con display_value true, los campos vienen como {"display_value": "...", "value": "..."}
                    # o como string simple si no es un campo de referencia
                    def get_field(val):
                        if isinstance(val, dict):
                            return val.get("display_value") or val.get("value") or str(val)
                        return val
                    
                    name = get_field(v.get("name") or v.get("question_text") or v.get("sys_id"))
                    dtype = get_field(v.get("type") or v.get("data_type") or "string")
                    required = get_field(v.get("required")) or False
                    default = get_field(v.get("default_value")) if v.get("default_value") else ""
                    
                    print(f"🔸 {name}")
                    print(f"   Tipo: {dtype}")
                    print(f"   Required: {required}")
                    if default:
                        print(f"   Default: {default}")
                    print()
                
                # Crear plantilla de variables con los nombres legibles
                var_template = {}
                for v in records:
                    name = get_field(v.get("name") or v.get("question_text"))
                    if name:
                        var_template[name] = ""
                
                if var_template:
                    print("💡 Plantilla para 'variables':")
                    print(json.dumps(var_template, indent=2, ensure_ascii=False))
                else:
                    print("⚠️ No se encontraron nombres legibles para las variables.")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
