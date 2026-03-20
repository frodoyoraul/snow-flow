#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

def get_val(field):
    if not field:
        return None
    if isinstance(field, dict):
        return field.get("display_value") or field.get("value")
    return field

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    cat_item_id = "68a7f85d472f7290a3978f59e16d43af"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"Buscando item_option_new con cat_item={cat_item_id}...\n")
                
                # Query directa
                result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 100,
                    "display_value": True
                })
                
                data = json.loads(result.content[0].text)
                records = data["data"]["records"]
                
                print(f"Total variables encontradas: {len(records)}\n")
                print("="*80)
                
                for i, v in enumerate(records, 1):
                    sys_id = get_val(v.get("sys_id"))
                    
                    # Intentar obtener una etiqueta legible
                    label = None
                    for field in ["conversational_label", "label", "name", "question_text", "description"]:
                        val = get_val(v.get(field))
                        if val:
                            label = val
                            break
                    if not label:
                        label = "(sin etiqueta)"
                    
                    dtype = get_val(v.get("type")) or "string"
                    ref = get_val(v.get("reference")) or ""
                    mand = v.get("mandatory")
                    mand_str = "false"
                    if mand:
                        if isinstance(mand, dict):
                            mand_str = mand.get("value") or mand.get("display_value") or "false"
                        else:
                            mand_str = str(mand).lower()
                    
                    print(f"{i}. {label}")
                    print(f"   sys_id: {sys_id}")
                    print(f"   type: {dtype}, reference: {ref}, mandatory: {mand_str}")
                    print()
                
                # Construir diccionario para usar en snow_order_catalog_item
                print("="*80)
                print("Diccionario de variables a enviar (clave=etiqueta o sys_id):\n")
                var_dict = {}
                for v in records:
                    sys_id = get_val(v.get("sys_id"))
                    label = None
                    for field in ["conversational_label", "label", "name", "question_text", "description"]:
                        val = get_val(v.get(field))
                        if val:
                            label = val
                            break
                    if not label:
                        label = sys_id
                    
                    # Determinar valor según tipo y mandatory
                    dtype = get_val(v.get("type"))
                    ref = get_val(v.get("reference"))
                    mand = v.get("mandatory")
                    is_mandatory = False
                    if mand:
                        if isinstance(mand, dict):
                            is_mandatory = mand.get("value") == "true" or mand.get("display_value") == "true"
                        else:
                            is_mandatory = str(mand).lower() in ["true", "1"]
                    
                    # Asignar valor de ejemplo
                    if is_mandatory and dtype == "reference" and ref == "sys_user":
                        var_dict[label] = "a8f98bb0eb32010045e1a5115206fe3a"  # Abraham Lincoln
                    elif is_mandatory:
                        # Para otras mandatory, poner valor de ejemplo
                        var_dict[label] = "valor_ejemplo"
                    else:
                        var_dict[label] = ""
                
                print(json.dumps(var_dict, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
