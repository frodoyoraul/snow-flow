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
                
                # Obtener la categoría
                cat_id = "1c28f8dd472f7290a3978f59e16d4319"
                print(f"🔍 Obteniendo categoría {cat_id}...")
                cat = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_category",
                    "sys_id": cat_id,
                    "display_value": False
                })
                
                cat_data = json.loads(cat.content[0].text)
                cat_record = cat_data["data"]["record"]
                
                print("\n📦 Campos de la categoría:\n")
                for key, val in sorted(cat_record.items()):
                    if key not in ["_url"] and any(x in key for x in ["widget", "sp_", "template", "description", "image"]):
                        print(f"{key}: {val}")
                
                # Buscar widget en la categoría
                widget_id = cat_record.get("sp_widget") or cat_record.get("widget")
                if widget_id:
                    if isinstance(widget_id, dict):
                        widget_id = widget_id.get("value")
                    print(f"\n🔧 Widget de categoría: {widget_id}")
                    
                    widget = await session.call_tool("snow_record_manage", {
                        "action": "get",
                        "table": "sp_widget",
                        "sys_id": widget_id,
                        "display_value": False
                    })
                    
                    widget_data = json.loads(widget.content[0].text)
                    widget_record = widget_data["data"]["record"]
                    
                    print("\n📋 Widget - option_schema:")
                    opt_schema = widget_record.get("option_schema")
                    if opt_schema:
                        try:
                            schema = json.loads(opt_schema)
                            print(json.dumps(schema, indent=2, ensure_ascii=False))
                        except:
                            print(opt_schema)
                
                # También puede haber 'description' con variables HTML
                desc = cat_record.get("description") or cat_record.get("short_description")
                if desc and "<" in desc:
                    print("\n📄 Descripción HTML (puede contener variables):")
                    print(desc[:500])
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
