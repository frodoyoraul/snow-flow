#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    cat_item_id = "68a7f85d472f7290a3978f59e16d43af"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                # Obtener variables con fields específicos: sys_id, type, reference, mandatory, question_text, name
                print("Obteniendo detalles de variables (type, reference, mandatory)...\n")
                result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 20,
                    "display_value": False,
                    "fields": ["sys_id", "type", "reference", "mandatory", "question_text", "name", "conversational_label"]
                })
                
                data = json.loads(result.content[0].text)
                records = data["data"]["records"]
                
                print(f"Variables: {len(records)}\n")
                for v in records:
                    sys_id = v.get("sys_id")
                    dtype = v.get("type")
                    ref = v.get("reference")
                    mand = v.get("mandatory")
                    # question_text o name pueden no existir
                    qt = v.get("question_text")
                    nm = v.get("name")
                    cl = v.get("conversational_label")
                    
                    label = qt or nm or cl or "(sin label)"
                    print(f"sys_id: {sys_id}")
                    print(f"  label: {label}")
                    print(f"  type: {dtype}, reference: {ref}, mandatory: {mand}")
                    print()
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
