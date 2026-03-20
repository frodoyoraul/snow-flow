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
                
                # 1. Obtener Abraham Lincoln
                print("🔍 Buscando Abraham Lincoln...")
                abraham_result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sys_user",
                    "query": "user_name=abraham.lincoln",
                    "limit": 1,
                    "display_value": False,
                    "fields": ["sys_id", "user_name"]
                })
                
                abraham_data = json.loads(abraham_result.content[0].text)
                abraham_records = abraham_data["data"]["records"]
                if not abraham_records:
                    print("❌ Abraham Lincoln no encontrado")
                    return
                
                abraham = abraham_records[0]
                abraham_sys_id = abraham.get("sys_id")
                abraham_name = abraham.get("user_name")
                print(f"✅ Usuario: {abraham_name} (sys_id: {abraham_sys_id})")
                
                # 2. Ordenar el catálogo con parámetro correcto y variables vacías
                print("\n🛒 Creando orden 'User Onboarding' para Abraham Lincoln...")
                order_result = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": "68a7f85d472f7290a3978f59e16d43af",
                    "requested_for": abraham_sys_id,
                    "quantity": 1,
                    "variables": {}  # <- variables vacías, el catálogo no parece requerirlas
                })
                
                result_data = json.loads(order_result.content[0].text)
                print("\n📦 Resultado:")
                print(json.dumps(result_data, indent=2, ensure_ascii=False))
                
                if result_data.get("success"):
                    ritm_num = result_data["data"]["ritm_number"]
                    ritm_sys_id = result_data["data"]["ritm_id"]
                    print(f"\n✅ Orden creada: {ritm_num}")
                    print(f"🆔 RITM sys_id: {ritm_sys_id}")
                    print("\n⚡ El script de auto-aprobación está corriendo y aprobará las approvals que aparezcan.")
                else:
                    print(f"\n❌ Fallo: {result_data.get('error')}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
