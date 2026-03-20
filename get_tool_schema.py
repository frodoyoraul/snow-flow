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
                
                # Listar todas las herramientas y sus descripciones
                tools = await session.list_tools()
                
                # Buscar específicamente snow_order_catalog_item
                order_tool = next((t for t in tools.tools if t.name == "snow_order_catalog_item"), None)
                
                if order_tool:
                    print("🔧 Herramienta encontrada:")
                    print(f"  Nombre: {order_tool.name}")
                    print(f"  Descripción: {order_tool.description}")
                    print("\n📋 Parámetros de input:")
                    print(json.dumps(order_tool.inputSchema, indent=2, ensure_ascii=False))
                else:
                    print("❌ No se encontró snow_order_catalog_item")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
