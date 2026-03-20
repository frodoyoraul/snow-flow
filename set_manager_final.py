#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

def get_sys_id(record):
    return record.get("sys_id")

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # Obtener admin (manager)
                admin_result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=admin",
                    "limit": 1,
                    "display_value": False,
                    "fields": ["sys_id"]
                })
                
                admin_data = json.loads(admin_result.content[0].text)
                admin_records = admin_data["data"]["records"]
                if not admin_records:
                    print("❌ Admin no encontrado")
                    return
                
                admin_sys_id = get_sys_id(admin_records[0])
                print(f"✅ Admin sys_id: {admin_sys_id}")
                
                # Obtener Abraham Lincoln
                abraham_result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=abraham.lincoln",
                    "limit": 1,
                    "display_value": False,
                    "fields": ["sys_id"]
                })
                
                abraham_data = json.loads(abraham_result.content[0].text)
                abraham_records = abraham_data["data"]["records"]
                if not abraham_records:
                    print("❌ Abraham Lincoln no encontrado")
                    return
                
                abraham_sys_id = get_sys_id(abraham_records[0])
                print(f"✅ Abraham Lincoln sys_id: {abraham_sys_id}")
                
                # Asignar manager
                print(f"\n🔄 Asignando manager a Abraham Lincoln...")
                update_result = await session.call_tool("snow_record_manage", {
                    "action": "update",
                    "table": "sys_user",
                    "sys_id": abraham_sys_id,
                    "manager": admin_sys_id
                })
                
                update_data = json.loads(update_result.content[0].text)
                print("\n📦 Resultado:")
                print(json.dumps(update_data, indent=2, ensure_ascii=False))
                
                if update_data.get("success") or update_data.get("updated"):
                    print("\n✅ Manager asignado correctamente!")
                else:
                    print(f"\n❌ Error: {update_data.get('error')}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
