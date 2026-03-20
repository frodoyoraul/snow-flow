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
                
                ritm_sys_id = "6452009447f33e14a3978f59e16d43ee"
                
                print(f"🔍 Revisando RITM {ritm_sys_id}...\n")
                
                # 1. Estado del RITM
                ritm = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_req_item",
                    "sys_id": ritm_sys_id,
                    "display_value": True
                })
                ritm_data = json.loads(ritm.content[0].text)
                ritm_record = ritm_data["data"]["record"]
                
                print("📦 RITM Estado:")
                print(f"  Número: {ritm_record.get('number')}")
                print(f"  Estado: {ritm_record.get('state')}")
                print(f"  Catalog Item: {ritm_record.get('sc_cat_item')}")
                print(f"  Requested for: {ritm_record.get('requested_for')}")
                print()
                
                # 2. Aprobaciones pendientes
                print("🔍 Approvals asociadas...")
                approvals = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sysapproval_approver",
                    "query": f"sysapproval={ritm_sys_id}",
                    "limit": 10,
                    "display_value": True
                })
                app_data = json.loads(approvals.content[0].text)
                app_records = app_data["data"]["records"]
                
                if app_records:
                    print(f"📋 {len(app_records)} approvals encontradas:")
                    for a in app_records:
                        state = a.get("state", {}).get("value") if isinstance(a.get("state"), dict) else a.get("state")
                        approver = a.get("approver", {}).get("display_value") if isinstance(a.get("approver"), dict) else a.get("approver")
                        print(f"  - {a.get('sys_id')} | Estado: {state} | Approver: {approver}")
                else:
                    print("✅ No hay approvals pendientes (o ya fueron procesadas)")
                
                # 3. Tareas (sc_task)
                print("\n🔍 Tareas (sc_task) asociadas...")
                tasks = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_task",
                    "query": f"request_item={ritm_sys_id}",
                    "limit": 10,
                    "display_value": True
                })
                tasks_data = json.loads(tasks.content[0].text)
                task_records = tasks_data["data"]["records"]
                
                if task_records:
                    print(f"📋 {len(task_records)} tareas encontradas:")
                    for t in task_records:
                        number = t.get("number")
                        state = t.get("state")
                        short_desc = t.get("short_description")
                        print(f"  - {number} | Estado: {state} | {short_desc}")
                else:
                    print("✅ No hay tareas pendientes (o ya se cerraron)")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
