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
    # RITM más reciente creado manualmente: RITM0010046, sys_id c2c0949a47f73e14a3978f59e16d4351
    ritm_sys_id = "c2c0949a47f73e14a3978f59e16d4351"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"Revisando RITM {ritm_sys_id} (RITM0010046) - creado manualmente...\n")
                
                # Variables asociadas
                vars_q = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"request_item={ritm_sys_id}",
                    "limit": 50,
                    "display_value": True,
                    "fields": ["sys_id", "name", "type", "reference", "mandatory", "value"]
                })
                vars_data = json.loads(vars_q.content[0].text)
                var_recs = vars_data["data"]["records"]
                print(f"Variables encontradas: {len(var_recs)}\n")
                
                if var_recs:
                    for v in var_recs[:30]:
                        label = get_val(v.get("name")) or v.get("sys_id")
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
                        print()
                else:
                    print("No se encontraron variables para este RITM.")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
