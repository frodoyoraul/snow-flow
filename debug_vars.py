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
                
                # Obtener todas las variables con display_value=False para ver campos crudos
                print("Buscando item_option_new con cat_item (display_value=False, todos campos)...")
                result = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 50,
                    "display_value": False
                })
                
                data = json.loads(result.content[0].text)
                records = data["data"]["records"]
                print(f"Total encontradas: {len(records)}\n")
                
                if records:
                    # Mostrar las primeras 3 variables con todos sus campos
                    for i, v in enumerate(records[:3], 1):
                        print(f"=== Variable {i} ===")
                        for key, val in v.items():
                            if key not in ["_url"]:
                                print(f"{key}: {val}")
                        print()
                    
                    # Contar cuántas tienen campo 'question_text' o 'name' o 'conversational_label'
                    print("=== Resumen de campos ===")
                    for field in ["question_text", "name", "conversational_label", "label", "description"]:
                        count = sum(1 for r in records if field in r and r[field])
                        print(f"Campo '{field}' presente en {count} registros")
                    
                    # Mostrar los valores de 'question_text' presentes
                    print("\nquestion_text presentes:")
                    for r in records:
                        if "question_text" in r and r["question_text"]:
                            print(f"  - {r['question_text']}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
