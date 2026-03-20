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
                
                # Obtener el usuario admin
                user_result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=admin",
                    "limit": 1,
                    "display_value": False
                })
                
                user_data = json.loads(user_result.content[0].text)
                records = user_data["data"]["records"]
                if not records:
                    print("❌ No se encontró usuario admin")
                    return
                
                user = records[0]
                # La estructura puede variar: puede ser sys_id.value o sys_id directamente
                user_sys_id = user.get("sys_id", {}).get("value") if isinstance(user.get("sys_id"), dict) else user.get("sys_id")
                print(f"👤 Usuario sys_id: {user_sys_id}")
                
                # Ordenar con el parámetro correcto
                print("\n🛒 Ordenando User Onboarding...")
                order_result = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": "68a7f85d472f7290a3978f59e16d43af",
                    "requested_for": user_sys_id,
                    "quantity": 1
                })
                
                result_text = order_result.content[0].text
                result_data = json.loads(result_text)
                print("\n📦 Resultado:")
                print(json.dumps(result_data, indent=2, ensure_ascii=False))
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
