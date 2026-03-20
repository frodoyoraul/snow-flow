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
                
                print("🔍 Buscando los 10 RITMs más recientes...")
                recent = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_req_item",
                    "limit": 10,
                    "display_value": True,
                    "orderBy": "sys_created_on:desc"
                })
                recent_data = json.loads(recent.content[0].text)
                records = recent_data["data"]["records"]
                
                print(f"📋 RITMs encontrados: {len(records)}\n")
                for r in records:
                    num = r.get("number")
                    state = r.get("state")
                    cat = r.get("sc_cat_item", {}).get("display_value") if isinstance(r.get("sc_cat_item"), dict) else r.get("sc_cat_item")
                    req_for = r.get("requested_for", {}).get("display_value") if isinstance(r.get("requested_for"), dict) else r.get("requested_for")
                    created = r.get("sys_created_on")
                    print(f"  {num} | Estado: {state} | Creado: {created} | Catálogo: {cat} | Para: {req_for}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
