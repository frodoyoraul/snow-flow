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
                
                # Buscar approvals pendientes relacionadas con el RITM
                print("🔍 Buscando approvals pendientes para RITM0010031...")
                approvals = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sysapproval_approver",
                    "query": "sysapproval=7aeaeb4c477ffa14a3978f59e16d4374^state=pending",
                    "limit": 10,
                    "display_value": True
                })
                
                approvals_data = json.loads(approvals.content[0].text)
                pending_approvals = approvals_data["data"]["records"]
                print(f"📋 Approvals pendientes: {len(pending_approvals)}")
                for appr in pending_approvals:
                    print(f"  - {appr.get('sys_id')} - {appr.get('approver', {}).get('display_value')}")
                
                # Buscar tareas (sc_task) relacionadas con el RITM
                print("\n🔍 Buscando SC_task para el RITM...")
                tasks = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_task",
                    "query": "request_item=7aeaeb4c477ffa14a3978f59e16d4374",
                    "limit": 10,
                    "display_value": True
                })
                
                tasks_data = json.loads(tasks.content[0].text)
                task_list = tasks_data["data"]["records"]
                print(f"📋 Tareas encontradas: {len(task_list)}")
                for task in task_list:
                    print(f"  - {task.get('number')} - {task.get('short_description')} - estado: {task.get('state')}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
