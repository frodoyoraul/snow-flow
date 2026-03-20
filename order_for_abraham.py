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
                
                # Buscar usuario Abraham Lincoln
                print("🔍 Buscando usuario 'Abraham Lincoln'...")
                user_result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=abraham.lincoln^ORname=Abraham Lincoln^ORfirst_name=Abraham^last_name=Lincoln",
                    "limit": 5,
                    "display_value": False
                })
                
                user_data = json.loads(user_result.content[0].text)
                users = user_data["data"]["records"]
                
                if not users:
                    print("❌ No se encontró Abraham Lincoln. Creando usuario...")
                    # Opcional: crear el usuario si no existe
                    create_result = await session.call_tool("snow_record_manage", {
                        "action": "create",
                        "table": "sys_user",
                        "user_name": "abraham.lincoln",
                        "first_name": "Abraham",
                        "last_name": "Lincoln",
                        "email": "abraham.lincoln@example.com",
                        "active": True,
                        "department": "a581ab703710200044e0bfc8bcbe5de8"  # Finance (mismo que admin)
                    })
                    create_data = json.loads(create_result.content[0].text)
                    if create_data.get("success"):
                        new_user = create_data["data"]["record"]
                        user_sys_id = new_user["sys_id"]["value"] if isinstance(new_user.get("sys_id"), dict) else new_user.get("sys_id")
                        print(f"✅ Usuario creado: abraham.lincoln (sys_id: {user_sys_id})")
                    else:
                        print(f"❌ Error creando usuario: {create_data}")
                        return
                else:
                    user = users[0]
                    user_sys_id = user.get("sys_id", {}).get("value") if isinstance(user.get("sys_id"), dict) else user.get("sys_id")
                    user_name = user.get("user_name", {}).get("value") if isinstance(user.get("user_name"), dict) else user.get("user_name")
                    print(f"✅ Usuario encontrado: {user_name} (sys_id: {user_sys_id})")
                
                # Crear orden para Abraham Lincoln
                print(f"\n🛒 Creando orden de 'User Onboarding' para {user_name}...")
                order_result = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": "68a7f85d472f7290a3978f59e16d43af",
                    "requested_for": user_sys_id,
                    "quantity": 1
                })
                
                result_data = json.loads(order_result.content[0].text)
                print("\n📦 Resultado:")
                print(json.dumps(result_data, indent=2, ensure_ascii=False))
                
                if result_data.get("success"):
                    ritm_num = result_data["data"]["ritm_number"]
                    ritm_sys_id = result_data["data"]["ritm_id"]
                    print(f"\n✅ Orden creada: {ritm_num} para {user_name}")
                    print(f"🆔 RITM sys_id: {ritm_sys_id}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
