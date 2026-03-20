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
    example_ritm = "c29091f347e77614a3978f59e16d4318"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"Inspeccionando RITM de ejemplo {example_ritm}...\n")
                
                # Obtener RITM
                ritm = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_req_item",
                    "sys_id": example_ritm,
                    "display_value": True
                })
                ritm_data = json.loads(ritm.content[0].text)
                rec = ritm_data["data"]["record"]
                
                print("📦 RITM de ejemplo:")
                for k in ["number", "state", "cat_item", "requested_for", "opened_by"]:
                    v = rec.get(k)
                    if isinstance(v, dict):
                        print(f"  {k}: {v.get('display_value')} (sys_id: {v.get('value')})")
                    else:
                        print(f"  {k}: {v}")
                print()
                
                # Variables asociadas a este RITM
                print("🔍 Variables del RITM (item_option_new con request_item = ritm_sys_id):")
                vars_ritm = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"request_item={example_ritm}",
                    "limit": 100,
                    "display_value": True,
                    "fields": ["sys_id", "name", "question_text", "conversational_label", "type", "reference", "mandatory", "value"]
                })
                vars_data = json.loads(vars_ritm.content[0].text)
                var_recs = vars_data["data"]["records"]
                print(f"   Variables encontradas: {len(var_recs)}\n")
                
                # Mostrar variables con etiquetas y valores
                for v in var_recs[:20]:
                    label = (get_val(v.get("conversational_label")) or
                             get_val(v.get("question_text")) or
                             get_val(v.get("name")) or
                             v.get("sys_id"))
                    dtype = get_val(v.get("type"))
                    ref = get_val(v.get("reference"))
                    mand = v.get("mandatory")
                    mand_str = "false"
                    if mand:
                        if isinstance(mand, dict):
                            mand_str = mand.get("value") or mand.get("display_value") or "false"
                        else:
                            mand_str = str(mand).lower()
                    val = get_val(v.get("value")) or ""
                    print(f"  - {label}")
                    print(f"      type: {dtype}, ref: {ref}, mandatory: {mand_str}")
                    print(f"      value: {val}")
                    print()
                
                # También ver el catálogo asociado a este RITM
                cat_id = None
                cat_field = rec.get("cat_item")
                if cat_field:
                    if isinstance(cat_field, dict):
                        cat_id = cat_field.get("value")
                    else:
                        cat_id = cat_field
                if cat_id:
                    print(f"Catálogo del RITM: {cat_id}")
                    # Obtener ese catálogo
                    cat = await session.call_tool("snow_record_manage", {
                        "action": "get",
                        "table": "sc_cat_item",
                        "sys_id": cat_id,
                        "display_value": True
                    })
                    cat_data = json.loads(cat.content[0].text)
                    cat_rec = cat_data["data"]["record"]
                    print(f"  Nombre catálogo: {cat_rec.get('name')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
