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
    ritm_sys_id = "03a2d09447f73e14a3978f59e16d43de"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"Buscando variables asociadas al RITM sys_id={ritm_sys_id}...")
                vars_q = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"request_item={ritm_sys_id}",
                    "limit": 50,
                    "display_value": True,
                    "fields": ["sys_id", "name", "question_text", "conversational_label", "type", "reference", "mandatory", "value"]
                })
                vars_data = json.loads(vars_q.content[0].text)
                var_recs = vars_data["data"]["records"]
                print(f"Variables encontradas: {len(var_recs)}\n")
                
                if var_recs:
                    for v in var_recs[:30]:
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
                        print(f"- {label}")
                        print(f"    type: {dtype}, ref: {ref}, mandatory: {mand_str}")
                        print(f"    value: {val}")
                else:
                    print("No se encontraron variables. El RITM puede no tener variables creadas.")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
