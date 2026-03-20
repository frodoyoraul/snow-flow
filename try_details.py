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
                
                # 1. Listar todos los campos del cat item
                print("1. Listando cat item con todos sus campos...")
                cat_item = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": "68a7f85d472f7290a3978f59e16d43af"
                })
                
                cat_data = json.loads(cat_item.content[0].text)
                record = cat_data["data"]["record"]
                
                # Mostrar campos que podrían contener widget o variable set
                print("\nCampos relevantes:")
                for key in record:
                    if any(x in key for x in ["widget", "variable", "template", "sp_"]):
                        print(f"  {key}: {record[key]}")
                
                # 2. Buscar directamente el widget usando snow_query_table
                print("\n2. Buscando sp_widget vinculado a este catálogo...")
                query = "sys_id=68a7f85d472f7290a3978f59e16d43af^sys_class_name=sc_cat_item"
                # intentar ver si hay un campo 'widget' que almacene referencia
                # tal vez el widget está en `sc_cat_item.w_id` o similar?
                
                # 3. Probar obtener el catalog item con la herramienta snow_get_catalog_item_details
                print("\n3. Probando snow_get_catalog_item_details...")
                details = await session.call_tool("snow_get_catalog_item_details", {
                    "item_id": "68a7f85d472f7290a3978f59e16d43af"
                })
                details_data = json.loads(details.content[0].text)
                print(json.dumps(details_data, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
