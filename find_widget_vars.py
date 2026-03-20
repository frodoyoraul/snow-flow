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
                
                # Obtener cat item con todos los campos posibles
                cat_item = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": "68a7f85d472f7290a3978f59e16d43af",
                    "display_value": False
                })
                
                cat_data = json.loads(cat_item.content[0].text)
                record = cat_data["data"]["record"]
                
                print("Campos del cat item (pueden contener widget o variable set):\n")
                for key, val in record.items():
                    if key.startswith("sp_") or key.startswith("variable") or key in ["widget", "template", "sc_template", "flow_designer_flow"]:
                        print(f"{key}: {val}")
                
                # Buscar sp_widget directamente
                widget_id = record.get("sp_widget") or record.get("widget")
                if widget_id:
                    if isinstance(widget_id, dict):
                        widget_id = widget_id.get("value")
                    print(f"\n🔧 Widget encontrado: {widget_id}")
                    
                    widget = await session.call_tool("snow_record_manage", {
                        "action": "get",
                        "table": "sp_widget",
                        "sys_id": widget_id,
                        "display_value": False
                    })
                    
                    widget_data = json.loads(widget.content[0].text)
                    widget_record = widget_data["data"]["record"]
                    
                    print("\n📦 Widget details:")
                    for k, v in widget_record.items():
                        if k in ["name", "option_schema", "html", "client_script", "data"]:
                            print(f"  {k}: {v}")
                    
                    # Parsear option_schema si existe
                    option_schema = widget_record.get("option_schema")
                    if option_schema:
                        try:
                            schema = json.loads(option_schema)
                            print("\n📋 Variables del widget (option_schema):")
                            print(json.dumps(schema, indent=2))
                        except:
                            print("\n⚠️ option_schema no es JSON válido")
                
                # Buscar variable_set
                var_set = record.get("variable_set") or record.get("variable_set_id")
                if var_set:
                    if isinstance(var_set, dict):
                        var_set = var_set.get("value")
                    print(f"\n📦 Variable Set encontrado: {var_set}")
                    vs = await session.call_tool("snow_record_manage", {
                        "action": "get",
                        "table": "sp_widget",
                        "sys_id": var_set,
                        "display_value": False
                    })
                    vs_data = json.loads(vs.content[0].text)
                    vs_record = vs_data["data"]["record"]
                    option_schema = vs_record.get("option_schema")
                    if option_schema:
                        try:
                            schema = json.loads(option_schema)
                            print("\n📋 Variables del variable set:")
                            print(json.dumps(schema, indent=2))
                        except:
                            pass
                            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
