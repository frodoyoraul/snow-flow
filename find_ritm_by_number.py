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
                
                # Buscar RITM por número
                print("Buscando RITM0010046 por número...")
                ritms = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_req_item",
                    "query": "number=RITM0010046",
                    "limit": 1,
                    "display_value": False
                })
                ritm_data = json.loads(ritms.content[0].text)
                records = ritm_data["data"]["records"]
                print(f"Encontrados: {len(records)}\n")
                if records:
                    print(json.dumps(records[0], indent=2))
                
                # Buscar los últimos RITMs del catálogo User Onboarding
                cat_id = "68a7f85d472f7290a3978f59e16d43af"
                print(f"\nBuscando RITMs recientes del catálogo {cat_id}...")
                recent = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_req_item",
                    "query": f"cat_item={cat_id}",
                    "limit": 5,
                    "display_value": False
                })
                recent_data = json.loads(recent.content[0].text)
                recent_recs = recent_data["data"]["records"]
                print(f"Encontrados: {len(recent_recs)}\n")
                for r in recent_recs:
                    print(f"sys_id: {r.get('sys_id')}, number: {r.get('number')}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
