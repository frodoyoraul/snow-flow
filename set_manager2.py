#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

def extract_sys_id(record):
    """Extrae el sys_id de un registro, manejando ambos formatos"""
    if not record:
        return None
    # Formato 1: {"sys_id": {"value": "..."}}
    if isinstance(record.get("sys_id"), dict):
        return record["sys_id"].get("value")
    # Formato 2: {"sys_id": "..."}
    return record.get("sys_id")

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # Obtener admin
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
                    print("❌ Admin no encontrado")
                    return
                
                admin = admin_users[0]
                admin_sys_id = extract_sys_id(admin)
                print(f"✅ Admin sys_id: {admin_sys_id}")
                
                # Obtener Abraham Lincoln
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
                    print("❌ Abraham Lincoln no encontrado")
                    return
                
                abraham = abraham_users[0]
                abraham_sys_id = extract_sys_id(abraham)
                print(f"✅ Abraham Lincoln sys_id: {abraham_sys_id}")
                
                # Asignar manager
                print(f"\n🔄 Asignando manager {admin_sys_id} a Abraham...")
                update_result = await session.call_tool("snow_record_manage", {
                    "action": "update",
                    "table": "sys_user",
                    "sys_id": abraham_sys_id,
                    "manager": admin_sys_id
                })
                
                update_data = json.loads(update_result.content[0].text)
                print(json.dumps(update_data, indent=2, ensure_ascii=False))
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
