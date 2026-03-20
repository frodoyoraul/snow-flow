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
                
                var_id = "70c6a0ff47c73e50a3978f59e16d4324"
                print(f"Obteniendo item_option_new {var_id} con todos los campos relevantes...")
                var = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "item_option_new",
                    "sys_id": var_id,
                    "display_value": True,
                    "fields": ["sys_id", "conversational_label", "description", "instructions", "type", "reference", "mandatory", "default_value", "category"]
                })
                
                var_data = json.loads(var.content[0].text)
                record = var_data["data"]["record"]
                
                print("\n📦 Variable (campos clave):")
                for key in ["conversational_label", "description", "instructions", "type", "reference", "mandatory", "default_value", "category"]:
                    val = record.get(key, {})
                    if isinstance(val, dict):
                        display = val.get("display_value") or val.get("value") or ""
                    else:
                        display = val or ""
                    print(f"{key}: {display}")
                
                # También obtener la categoría de la variable (category)
                cat_ref = record.get("category")
                if cat_ref:
                    if isinstance(cat_ref, dict):
                        cat_id = cat_ref.get("value")
                    else:
                        cat_id = cat_ref
                    if cat_id:
                        print(f"\nCategoría de variable: {cat_id}")
                        cat_var = await session.call_tool("snow_record_manage", {
                            "action": "get",
                            "table": "item_option_category",
                            "sys_id": cat_id,
                            "display_value": True
                        })
                        cat_var_data = json.loads(cat_var.content[0].text)
                        cat_var_rec = cat_var_data["data"]["record"]
                        cat_name = cat_var_rec.get("name") or cat_var_rec.get("label") or cat_id
                        print(f"Nombre categoría: {cat_name}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
