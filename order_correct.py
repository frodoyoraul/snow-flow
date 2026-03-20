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
                
                # Obtener el usuario admin primero
                user_result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=admin",
                    "limit": 1,
                    "display_value": False
                })
                
                user_data = json.loads(user_result.content[0].text)
                user = user_data["data"]["records"][0]
                user_sys_id = user["sys_id"]["value"]
                
                print(f"👤 Usuario: {user_sys_id}")
                
                # CORRECTO: usar cat_item (no item_id)
                print("\n🛒 Ordenando User Onboarding con parámetro correcto...")
                order_result = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": "68a7f85d472f7290a3978f59e16d43af",  # <- campo correcto
                    "requested_for": user_sys_id,
                    "quantity": 1
                    # Si el item requiere variables, se añaden aquí:
                    # "variables": {"employee_name": "Juan Perez", "start_date": "2025-04-01"}
                })
                
                result_data = json.loads(order_result.content[0].text)
                print("\n📦 Resultado:")
                print(json.dumps(result_data, indent=2, ensure_ascii=False))
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
