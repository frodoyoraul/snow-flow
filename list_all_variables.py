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
                
                # 1. Obtener TODAS las relaciones sc_item_option_mtom para este cat_item (limit alto)
                print("1. Obteniendo relaciones de variables...")
                relations = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option_mtom",
                    "query": f"cat_item=68a7f85d472f7290a3978f59e16d43af",
                    "limit": 200,  # Traer muchas
                    "display_value": False
                })
                
                rel_data = json.loads(relations.content[0].text)
                records = rel_data["data"]["records"]
                print(f"   Relaciones encontradas: {len(records)}")
                
                # 2. Extraer los sys_id de sc_item_option
                option_ids = []
                for r in records:
                    opt = r.get("sc_item_option")
                    if isinstance(opt, dict):
                        opt_id = opt.get("value")
                    else:
                        opt_id = opt
                    if opt_id and opt_id not in option_ids:
                        option_ids.append(opt_id)
                
                print(f"   Variables únicas: {len(option_ids)}")
                
                if not option_ids:
                    print("No se encontraron variables.")
                    return
                
                # 3. Obtener detalles de las variables (en batch)
                print("\n2. Obteniendo detalles de las variables...")
                variables = []
                # Hacer query para traer todas las variables de una vez usando IN
                # Como pueden ser muchas, vamos por lotes
                batch_size = 50
                for i in range(0, len(option_ids), batch_size):
                    batch = option_ids[i:i+batch_size]
                    # Construir query: sys_idIN<lista>
                    query = "sys_id=" + ",".join(batch)
                    var_batch = await session.call_tool("snow_record_manage", {
                        "action": "query",
                        "table": "sc_item_option",
                        "query": query,
                        "limit": batch_size,
                        "display_value": False
                    })
                    var_data = json.loads(var_batch.content[0].text)
                    variables.extend(var_data["data"]["records"])
                
                print(f"   Detalles obtenidos: {len(variables)}\n")
                
                # 4. Mostrar las variables con su información clave
                print("📋 Variables del catalog item 'User Onboarding':\n")
                for var in variables[:50]:  # mostrar primeras 50
                    name = var.get("name") or var.get("question_text") or "N/A"
                    req = var.get("required", False)
                    dtype = var.get("type") or var.get("data_type") or "string"
                    default = var.get("default_value")
                    ref_table = var.get("reference", "")
                    print(f"🔸 {name}")
                    print(f"   Tipo: {dtype}")
                    print(f"   Required: {req}")
                    if default:
                        print(f"   Default: {default}")
                    if ref_table:
                        print(f"   Reference: {ref_table}")
                    print()
                
                # 5. Resumen final
                print(f"\n✅ Total variables: {len(variables)}")
                print("💡 Para ordenar el catálogo, necesitarás pasar un objeto 'variables' con pares nombre-valor.")
                print("   Los nombres de las variables son los mostrados arriba (name/question_text).")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
