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
                
                # Buscar TODAS las approvals pendientes (sin filtro)
                print("🔍 Buscando TODAS las approvals pendientes en el sistema...")
                all_apps = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sysapproval_approver",
                    "query": "state=pending",
                    "limit": 20,
                    "display_value": True
                })
                apps_data = json.loads(all_apps.content[0].text)
                apps = apps_data["data"]["records"]
                
                print(f"📋 Approvals pendientes: {len(apps)}\n")
                for a in apps:
                    sys_id = a.get("sys_id")
                    state = a.get("state")
                    approver = a.get("approver", {}).get("display_value") if isinstance(a.get("approver"), dict) else a.get("approver")
                    sysapproval = a.get("sysapproval", {}).get("display_value") if isinstance(a.get("sysapproval"), dict) else a.get("sysapproval")
                    print(f"  {sys_id} | Aprobador: {approver} | RITM: {sysapproval} | Estado: {state}")
                
                # Buscar tareas abiertas (no cerradas)
                print("\n🔍 Buscando tareas abiertas (state NOT IN 7,8)...")
                tasks = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_task",
                    "query": "stateNOT IN7,8",
                    "limit": 20,
                    "display_value": True
                })
                tasks_data = json.loads(tasks.content[0].text)
                task_records = tasks_data["data"]["records"]
                
                print(f"📋 Tareas no cerradas: {len(task_records)}\n")
                for t in task_records[:10]:
                    number = t.get("number")
                    state = t.get("state")
                    short_desc = t.get("short_description")
                    ritm = t.get("request_item", {}).get("display_value") if isinstance(t.get("request_item"), dict) else t.get("request_item")
                    print(f"  {number} | Estado: {state} | RITM: {ritm} | {short_desc}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
