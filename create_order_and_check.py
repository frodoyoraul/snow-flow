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
                
                print("🛒 Creando nueva orden de 'User Onboarding'...")
                
                # Usar el parámetro CORRECTO: cat_item
                order_result = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": "68a7f85d472f7290a3978f59e16d43af",
                    "requested_for": "admin",  # username del admin
                    "quantity": 1
                })
                
                result_data = json.loads(order_result.content[0].text)
                print("\n📦 Resultado:")
                print(json.dumps(result_data, indent=2, ensure_ascii=False))
                
                if result_data.get("success"):
                    ritm_num = result_data["data"]["ritm_number"]
                    ritm_sys_id = result_data["data"]["ritm_id"]
                    print(f"\n✅ Orden creada: {ritm_num}")
                    print(f"🆔 RITM sys_id: {ritm_sys_id}")
                    print("\n🔍 Buscando approvals generadas...")
                    
                    # Esperar un poco y buscar approvals
                    await asyncio.sleep(3)
                    
                    approvals = await session.call_tool("snow_record_manage", {
                        "action": "query",
                        "table": "sysapproval_approver",
                        "query": f"sysapproval={ritm_sys_id}",
                        "limit": 10,
                        "display_value": True
                    })
                    
                    approvals_data = json.loads(approvals.content[0].text)
                    pending = approvals_data["data"]["records"]
                    print(f"\n📋 Approvals encontradas: {len(pending)}")
                    for appr in pending:
                        state = appr.get("state", {}).get("value") if isinstance(appr.get("state"), dict) else appr.get("state")
                        approver = appr.get("approver", {}).get("display_value") if isinstance(appr.get("approver"), dict) else appr.get("approver")
                        print(f"  - {appr.get('sys_id')} | Estado: {state} | Approver: {approver}")
                    
                    if pending:
                        print("\n⚡ El script de auto-aprobación ya está corriendo y las aprobará automáticamente.")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
