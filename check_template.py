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
                
                # Obtener el sc_template asociado
                template_sys_id = "dab9529cbd002010f8775d9559d0dab6"
                print(f"🔍 Obteniendo template {template_sys_id}...")
                template = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_template",
                    "sys_id": template_sys_id,
                    "display_value": False
                })
                
                tpl_data = json.loads(template.content[0].text)
                tpl_record = tpl_data["data"]["record"]
                
                print("\n📦 Campos del template (sc_template):\n")
                for key, val in sorted(tpl_record.items()):
                    if key not in ["_url"]:
                        print(f"{key}: {val}")
                
                # Buscar sp_widget en el template
                widget_id = tpl_record.get("sp_widget") or tpl_record.get("widget")
                if widget_id:
                    if isinstance(widget_id, dict):
                        widget_id = widget_id.get("value")
                    print(f"\n🔧 Widget asociado al template: {widget_id}")
                    
                    widget = await session.call_tool("snow_record_manage", {
                        "action": "get",
                        "table": "sp_widget",
                        "sys_id": widget_id,
                        "display_value": False
                    })
                    
                    widget_data = json.loads(widget.content[0].text)
                    widget_record = widget_data["data"]["record"]
                    
                    print("\n📋 Widget - Campos relevantes:")
                    for k, v in widget_record.items():
                        if k in ["name", "option_schema", "html", "client_script", "description"]:
                            print(f"  {k}: {v}")
                    
                    option_schema = widget_record.get("option_schema")
                    if option_schema:
                        try:
                            schema = json.loads(option_schema)
                            print("\n📋 Variables definidas en option_schema:")
                            print(json.dumps(schema, indent=2, ensure_ascii=False))
                        except Exception as e:
                            print(f"\n⚠️ Error parseando option_schema: {e}")
                
                # Sc_template también puede tener option_schema directamente
                tpl_schema = tpl_record.get("option_schema")
                if tpl_schema:
                    try:
                        t_schema = json.loads(tpl_schema)
                        print("\n📋 Variables definidas en option_schema del template:")
                        print(json.dumps(t_schema, indent=2, ensure_ascii=False))
                    except:
                        pass
                        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
