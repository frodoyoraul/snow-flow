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
                
                # 1. Obtener el usuario actual (admin)
                user_result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=admin",
                    "limit": 1,
                    "fields": ["sys_id", "user_name", "first_name", "last_name", "email"]
                })
                
                user_data = json.loads(user_result.content[0].text)
                user = user_data["data"]["records"][0] if user_data["data"]["records"] else None
                print(f"👤 Usuario actual: {user}")
                
                if not user:
                    print("❌ No se encontró usuario admin")
                    return
                
                # 2. Ordenar el catalog item "User Onboarding"
                print("\n🛒 Ordenando 'User Onboarding'...")
                order_result = await session.call_tool("snow_order_catalog_item", {
                    "item_id": "68a7f85d472f7290a3978f59e16d43af",
                    "requested_for": user["sys_id"]
                })
                
                print("\n📦 Resultado de la orden:")
                print(json.dumps(json.loads(order_result.content[0].text), indent=2, ensure_ascii=False))
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
