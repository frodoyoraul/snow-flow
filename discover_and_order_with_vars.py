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
                
                # Obtener todas las variables del catálogo
                direct_vars = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 100,
                    "display_value": True
                })
                direct_data = json.loads(direct_vars.content[0].text)
                var_records = direct_data["data"]["records"]
                
                print(f"📚 Variables encontradas: {len(var_records)}\n")
                
                var_template = {}
                var_values = {}
                
                for v in var_records:
                    sys_id = v.get("sys_id", "N/A")
                    # Buscar una etiqueta
                    label = None
                    for field in ["conversational_label", "label", "name", "question_text", "description"]:
                        val = v.get(field)
                        if val:
                            if isinstance(val, dict):
                                lbl = val.get("display_value") or val.get("value")
                            else:
                                lbl = val
                            if lbl:
                                label = lbl
                                break
                    if not label:
                        label = sys_id  # fallback
                    
                    # Determinar tipo y mandatory
                    dtype = None
                    ref_table = None
                    mandatory = False
                    
                    # type puede ser un dict con value
                    type_field = v.get("type")
                    if type_field:
                        if isinstance(type_field, dict):
                            dtype = type_field.get("value") or type_field.get("display_value")
                        else:
                            dtype = type_field
                    
                    # reference
                    ref_field = v.get("reference")
                    if ref_field:
                        if isinstance(ref_field, dict):
                            ref_table = ref_field.get("value") or ref_field.get("display_value")
                        else:
                            ref_table = ref_field
                    
                    # mandatory
                    mand_field = v.get("mandatory")
                    if mand_field:
                        if isinstance(mand_field, dict):
                            mandatory = mand_field.get("value") == "true" or mand_field.get("display_value") == "true"
                        else:
                            mandatory = mand_field in [True, "true", "True", 1, "1"]
                    
                    print(f"🔸 {label}")
                    print(f"   sys_id: {sys_id}")
                    print(f"   type: {dtype}, reference: {ref_table}, mandatory: {mandatory}")
                    
                    # Añadir a plantilla
                    var_template[label] = ""
                    
                    # Si es mandatory y tipo reference a sys_user, asignar Abraham
                    if mandatory and dtype == "reference" and ref_table == "sys_user":
                        var_values[label] = "a8f98bb0eb32010045e1a5115206fe3a"  # Abraham Lincoln
                    elif mandatory:
                        # Para otras mandatory, necesitamos un valor de ejemplo; por ahora dejamos cadena vacía (puede fallar)
                        var_values[label] = ""
                    else:
                        # No mandatory, dejar vacío
                        var_values[label] = ""
                
                print("\n💡 Plantilla de variables (con valores vacíos):")
                print(json.dumps(var_template, indent=2, ensure_ascii=False))
                
                print("\n📝 Valores que vamos a enviar:")
                print(json.dumps(var_values, indent=2, ensure_ascii=False))
                
                # Crear orden para Abraham Lincoln
                print("\n🛒 Creando orden con variables...")
                order = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": cat_item_id,
                    "requested_for": "a8f98bb0eb32010045e1a5115206fe3a",
                    "variables": var_values
                })
                order_data = json.loads(order.content[0].text)
                print("\n📦 Resultado:")
                print(json.dumps(order_data, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
