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
    ritm_sys_id = "c2c0949a47f73e14a3978f59e16d4351"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"Buscando approvals y sc_task para RITM {ritm_sys_id}...\n")
                
                # 1. Approvals
                apps = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sysapproval_approver",
                    "query": f"sysapproval={ritm_sys_id}",
                    "limit": 20,
                    "display_value": True
                })
                apps_data = json.loads(apps.content[0].text)
                app_recs = apps_data["data"]["records"]
                print(f"Approvals encontradas: {len(app_recs)}\n")
                
                if app_recs:
                    for a in app_recs:
                        state = get_val(a.get("state"))
                        approver = get_val(a.get("approver"))
                        print(f"- Approver: {approver} | Estado: {state}")
                    print()
                
                # 2. SC Task
                tasks = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_task",
                    "query": f"request_item={ritm_sys_id}",
                    "limit": 20,
                    "display_value": True
                })
                tasks_data = json.loads(tasks.content[0].text)
                task_recs = tasks_data["data"]["records"]
                print(f"SC Task encontradas: {len(task_recs)}\n")
                
                if task_recs:
                    for t in task_recs:
                        number = t.get("number")
                        short_desc = get_val(t.get("short_description"))
                        state = get_val(t.get("state"))
                        print(f"- {number}: {short_desc} (estado: {state})")
                else:
                    print("No hay sc_task.\n")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
