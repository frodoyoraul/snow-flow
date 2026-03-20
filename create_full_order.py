#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    cat_item_id = "68a7f85d472f7290a3978f59e16d43af"
    abraham_id = "a8f98bb0eb32010045e1a5115206fe3a"
    admin_id = "6816f79cc0a8016401c5a33be04be441"
    department_id = "a581ab703710200044e0bfc8bcbe5de8"  # Finance
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # 1. Obtener un location (cmn_location)
                print("1. Buscando un location válido...")
                locs = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "cmn_location",
                    "limit": 1,
                    "display_value": False
                })
                locs_data = json.loads(locs.content[0].text)
                loc_records = locs_data["data"]["records"]
                if not loc_records:
                    print("❌ No se encontraron locaciones")
                    return
                location_id = loc_records[0].get("sys_id")
                print(f"   Location seleccionado: {location_id}")
                
                # 2. Construir diccionario de variables con valores
                var_values = {
                    # Obligatorias
                    "Personal Email": "abraham.lincoln@example.com",
                    "Location": location_id,
                    "Job Title": "Employee",
                    "Manager": admin_id,
                    "Last Name": "Lincoln",
                    "Corporate Email": "abraham.lincoln@example.com",
                    "Department": department_id,
                    "First Name": "Abraham",
                    "Start Date": "2025-04-01",  # formato yyyy-MM-dd
                    # No obligatorias (vacías o valores de prueba)
                    "Additional Comments": "",
                    "Needs Laptop": "false",
                    "formatter": "",
                    "formatter2": "",
                    "Main": "",
                    "Required Software": "",
                    "Laptop Type": "",
                    "Mobile Device Type": "",
                    "System Access Requirements": "",
                    "Needs Mobile Device": "false"
                }
                
                print("\n2. Variables a enviar:")
                print(json.dumps(var_values, indent=2, ensure_ascii=False))
                
                # 3. Crear orden
                print("\n3. Creando orden para Abraham Lincoln con variables completas...")
                order = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": cat_item_id,
                    "requested_for": abraham_id,
                    "variables": var_values,
                    "quantity": 1
                })
                order_data = json.loads(order.content[0].text)
                print("\nResultado:")
                print(json.dumps(order_data, indent=2, ensure_ascii=False))
                
                if order_data.get("success"):
                    ritm_num = order_data["data"]["ritm_number"]
                    ritm_sys_id = order_data["data"]["ritm_id"]
                    print(f"\n✅ Orden creada: {ritm_num}")
                    print(f"🆔 RITM sys_id: {ritm_sys_id}")
                    print("🔄 Monitor de auto-aprobación está activo.")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
