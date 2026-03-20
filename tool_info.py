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
                
                # Obtener información detallada de la herramienta
                tools = await session.list_tools()
                tool = next((t for t in tools.tools if t.name == "snow_order_catalog_item"), None)
                
                if not tool:
                    print("❌ Herramienta no encontrada")
                    return
                
                print("=" * 60)
                print("SNOW_ORDER_CATALOG_ITEM - INFORMACIÓN COMPLETA")
                print("=" * 60)
                print(f"\n🔹 Nombre: {tool.name}")
                print(f"🔹 Descripción: {tool.description}")
                print("\n🔹 Parámetros de entrada (JSON Schema):")
                print(json.dumps(tool.inputSchema, indent=2, ensure_ascii=False))
                
                print("\n🔹 Campos obligatorios:")
                for field in tool.inputSchema.get("required", []):
                    prop = tool.inputSchema["properties"][field]
                    print(f"  - {field}: {prop.get('description', '')} (tipo: {prop.get('type', 'any')})")
                
                print("\n🔹 Campos opcionales:")
                for field, prop in tool.inputSchema["properties"].items():
                    if field not in tool.inputSchema.get("required", []):
                        print(f"  - {field}: {prop.get('description', '')} (tipo: {prop.get('type', 'any')})")
                
                print("\n" + "=" * 60)
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
