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
                
                # Obtener cat item con todos los campos
                cat_item = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": "68a7f85d472f7290a3978f59e16d43af",
                    "display_value": False
                })
                
                cat_data = json.loads(cat_item.content[0].text)
                record = cat_data["data"]["record"]
                
                print("📦 Todos los campos del catalog item:\n")
                for key, val in sorted(record.items()):
                    if key not in ["_url"]:
                        print(f"{key}: {val}")
                
                # 2. Chequear si tiene variables a través de la tabla sc_item_option (asociada al catálogo, no al RITM)
                # En algunos casos, las variables se asocian al catálogo mismo via sc_item_option_mtom con cat_item (no request_item)
                # Vamos a ver si existe una relación inversa
                print("\n🔍 Buscando variables directas del catálogo (relación cat_item -> sc_item_option)...")
                # Intentar query: sc_item_option_mtom con cat_item=<sys_id>
                rel = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option_mtom",
                    "query": f"cat_item=68a7f85d472f7290a3978f59e16d43af",  # pero antes ví que no tenía campo cat_item, solo request_item
                    "limit": 5
                })
                rel_data = json.loads(rel.content[0].text)
                print(json.dumps(rel_data, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
