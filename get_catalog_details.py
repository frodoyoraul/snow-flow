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
                print("✅ Conectado al MCP proxy")
                
                # Buscar la herramienta de detalles de catálogo
                tools = await session.list_tools()
                details_tool = next((t for t in tools.tools if "get_catalog_item_details" in t.name), None)
                
                if details_tool:
                    print(f"\n🔍 Obteniendo detalles del item 'User Onboarding'...")
                    result = await session.call_tool(details_tool.name, {
                        "item_id": "68a7f85d472f7290a3978f59e16d43af"
                    })
                    print("\n📦 Detalles del catalog item:")
                    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
                else:
                    print("\n⚠️ No se encontró herramienta para obtener detalles")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
