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
    ritm_sys_id = "03a2d09447f73e14a3978f59e16d43de"  # RITM0010045
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"🔍 Revisando RITM {ritm_sys_id} (RITM0010045)...\n")
                
                # 1. Estado del RITM
                print("1. Datos del RITM:")
                ritm = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_req_item",
                    "sys_id": ritm_sys_id,
                    "display_value": True
                })
                ritm_data = json.loads(ritm.content[0].text)
                ritm_rec = ritm_data["data"]["record"]
                for key in ["number", "state", "cat_item", "requested_for", "opened_by"]:
                    val = ritm_rec.get(key)
                    if isinstance(val, dict):
                        print(f"  {key}: {val.get('display_value')} (sys_id: {val.get('value')})")
                    else:
                        print(f"  {key}: {val}")
                print()
                
                # 2. Approvals asociadas
                print("2. Buscando approvals (sysapproval_approver)...")
                apps = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sysapproval_approver",
                    "query": f"sysapproval={ritm_sys_id}",
                    "limit": 20,
                    "display_value": True
                })
                apps_data = json.loads(apps.content[0].text)
                app_records = apps_data["data"]["records"]
                print(f"   Approvals encontradas: {len(app_records)}\n")
                
                if app_records:
                    for a in app_records:
                        state = get_val(a.get("state"))
                        approver = get_val(a.get("approver"))
                        sysapproval = get_val(a.get("sysapproval"))
                        print(f"  - Approver: {approver} | Estado: {state} | RITM: {sysapproval}")
                    print()
                
                # 3. Tareas (sc_task)
                print("3. Buscando sc_task...")
                tasks = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_task",
                    "query": f"request_item={ritm_sys_id}",
                    "limit": 20,
                    "display_value": True
                })
                tasks_data = json.loads(tasks.content[0].text)
                task_records = tasks_data["data"]["records"]
                print(f"   Tareas encontradas: {len(task_records)}\n")
                
                if task_records:
                    for t in task_records:
                        number = t.get("number")
                        state = get_val(t.get("state"))
                        short_desc = get_val(t.get("short_description"))
                        print(f"  - {number}: {short_desc} (estado: {state})")
                    print()
                else:
                    print("  No hay tareas.\n")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
