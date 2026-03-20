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
                
                # 1. Obtener el usuario admin para ser manager
                print("🔍 Buscando usuario admin...")
                admin_result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=admin",
                    "limit": 1,
                    "display_value": False
                })
                
                admin_data = json.loads(admin_result.content[0].text)
                admin_users = admin_data["data"]["records"]
                if not admin_users:
                    print("❌ No se encontró usuario admin")
                    return
                
                admin = admin_users[0]
                admin_sys_id = admin.get("sys_id", {}).get("value") if isinstance(admin.get("sys_id"), dict) else admin.get("sys_id")
                print(f"✅ Admin encontrado: sys_id={admin_sys_id}")
                
                # 2. Buscar Abraham Lincoln
                print("\n🔍 Buscando Abraham Lincoln...")
                abraham_result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=abraham.lincoln",
                    "limit": 1,
                    "display_value": False
                })
                
                abraham_data = json.loads(abraham_result.content[0].text)
                abraham_users = abraham_data["data"]["records"]
                if not abraham_users:
                    print("❌ No se encontró Abraham Lincoln")
                    return
                
                abraham = abraham_users[0]
                abraham_sys_id = abraham.get("sys_id", {}).get("value") if isinstance(abraham.get("sys_id"), dict) else abraham.get("sys_id")
                print(f"✅ Abraham encontrado: sys_id={abraham_sys_id}")
                
                # 3. Asignar manager a Abraham
                print(f"\n🔄 Asignando admin como manager de Abraham Lincoln...")
                update_result = await session.call_tool("snow_record_manage", {
                    "action": "update",
                    "table": "sys_user",
                    "sys_id": abraham_sys_id,
                    "manager": admin_sys_id
                })
                
                update_data = json.loads(update_result.content[0].text)
                if update_data.get("success") or update_data.get("updated"):
                    print("✅ Manager asignado correctamente")
                else:
                    print(f"❌ Error asignando manager: {update_data}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
