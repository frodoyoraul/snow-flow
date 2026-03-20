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
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                cat_item_id = "68a7f85d472f7290a3978f59e16d43af"
                
                # Obtener variables
                vars_q = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 100,
                    "display_value": True
                })
                vars_data = json.loads(vars_q.content[0].text)
                records = vars_data["data"]["records"]
                
                print(f"Variables del catálogo: {len(records)}\n")
                
                var_assignments = {}
                for v in records:
                    sys_id = get_val(v.get("sys_id"))
                    label = None
                    for f in ["conversational_label", "label", "name", "question_text", "description"]:
                        val = get_val(v.get(f))
                        if val:
                            label = val
                            break
                    if not label:
                        label = sys_id
                    
                    dtype = get_val(v.get("type"))
                    ref = get_val(v.get("reference"))
                    mand = v.get("mandatory")
                    mand_val = False
                    if mand:
                        if isinstance(mand, dict):
                            mand_val = mand.get("value") == "true" or mand.get("display_value") == "true"
                        else:
                            mand_val = mand in [True, "true", "True", 1, "1"]
                    
                    print(f"{label} | type: {dtype} | ref: {ref} | mandatory: {mand_val}")
                    
                    # Si es mandatory y referencia sys_user, asignar Abraham
                    if mand_val and dtype == "reference" and ref == "sys_user":
                        var_assignments[label] = "a8f98bb0eb32010045e1a5115206fe3a"
                    elif mand_val:
                        # Otras mandatory: intentar valor por defecto o dejar valor de ejemplo
                        var_assignments[label] = ""
                    else:
                        var_assignments[label] = ""
                
                print("\nVariables a enviar:")
                print(json.dumps(var_assignments, indent=2, ensure_ascii=False))
                
                # Crear orden
                print("\nCreando orden para Abraham Lincoln...")
                order = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": cat_item_id,
                    "requested_for": "a8f98bb0eb32010045e1a5115206fe3a",
                    "variables": var_assignments
                })
                order_data = json.loads(order.content[0].text)
                print("\nResultado:")
                print(json.dumps(order_data, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
