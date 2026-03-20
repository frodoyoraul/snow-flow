#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    var_set_id = "e01cab1a4f334200086eeed18110c71f"
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                print(f"🔍 Buscando sp_widget con sys_id={var_set_id}...")
                widget = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sp_widget",
                    "sys_id": var_set_id,
                    "display_value": False
                })
                
                widget_data = json.loads(widget.content[0].text)
                
                if not widget_data.get("success"):
                    print(f"❌ Widget no encontrado: {widget_data.get('error')}")
                    return
                
                record = widget_data["data"]["record"]
                print(f"✅ Widget encontrado: {record.get('name')}")
                
                option_schema = record.get("option_schema")
                if option_schema:
                    try:
                        schema = json.loads(option_schema)
                        print("\n📋 Variables (option_schema):")
                        print(json.dumps(schema, indent=2, ensure_ascii=False))
                        
                        # Preparar diccionario de variables vacío
                        if "properties" in schema:
                            var_template = {k: "" for k in schema["properties"].keys()}
                            print("\n💡 Plantilla para 'variables':")
                            print(json.dumps(var_template, indent=2, ensure_ascii=False))
                        
                    except json.JSONDecodeError:
                        print("\n⚠️ option_schema no es JSON válido:")
                        print(option_schema)
                else:
                    print("\n❌ Este widget no tiene option_schema.")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
