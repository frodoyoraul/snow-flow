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
                
                # 1. Obtener el catalog item completo (con todos los campos relevantes)
                print("🔍 Obteniendo detalles del catalog item 'User Onboarding'...")
                cat_item_result = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": "68a7f85d472f7290a3978f59e16d43af",
                    "display_value": False
                })
                
                cat_item_data = json.loads(cat_item_result.content[0].text)
                cat_item = cat_item_data["data"]["record"]
                print("\n📦 Campos del catalog item:")
                for key in sorted(cat_item.keys()):
                    if key not in ["_url"] and not key.endswith("_"):
                        val = cat_item[key]
                        if isinstance(val, dict):
                            print(f"  {key}: {val.get('value', val)}")
                        else:
                            print(f"  {key}: {val}")
                
                # 2. Buscar variable sets asociados
                # En ServiceNow, los items de catálogo pueden tener variable sets en 'variables' o usar 'item_option_new'
                # También pueden tener un 'template' que defina variables
                
                cat_item_sys_id = cat_item.get("sys_id")
                if isinstance(cat_item_sys_id, dict):
                    cat_item_sys_id = cat_item_sys_id.get("value")
                
                print(f"\n🔄 Buscando variables asociadas al item {cat_item_sys_id}...")
                
                # Las variables se encuentran en sc_item_option_mtom (relación entre cat_item y variables)
                # O en la tabla sp_widget si el item usa un widget
                
                # Intentar primero: ver si tiene un variable_set
                variable_set = cat_item.get("variable_set") or cat_item.get("variable_set_id")
                if variable_set:
                    if isinstance(variable_set, dict):
                        variable_set = variable_set.get("value")
                    print(f"✅ Tiene variable_set: {variable_set}")
                    
                    # Obtener variables del variable set
                    vs_vars = await session.call_tool("snow_record_manage", {
                        "action": "query",
                        "table": "sp_widget",
                        "query": f"sys_id={variable_set}",
                        "display_value": False
                    })
                    vs_data = json.loads(vs_vars.content[0].text)
                    if vs_data["data"]["records"]:
                        vs_record = vs_data["data"]["records"][0]
                        print("\n📋 Variables del Variable Set:")
                        # Los widgets/plantillas pueden tener opciones en option_schema o en variables directamente
                        option_schema = vs_record.get("option_schema")
                        if option_schema:
                            try:
                                schema = json.loads(option_schema)
                                print(json.dumps(schema, indent=2))
                            except:
                                print(option_schema)
                
                # Intentar segundo: buscar variables directas en sc_item_option_mtom
                print("\n🔍 Buscando variables directas del item...")
                direct_vars = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "sc_item_option_mtom",
                    "query": f"cat_item={cat_item_sys_id}",
                    "limit": 50,
                    "display_value": False
                })
                
                direct_data = json.loads(direct_vars.content[0].text)
                var_records = direct_data["data"]["records"]
                print(f"📚 Variables encontradas en sc_item_option_mtom: {len(var_records)}")
                
                if var_records:
                    print("\n📋 Lista de variables:")
                    for var in var_records:
                        # Cada registro tiene: cat_item, sc_item_option ( referencia a la variable)
                        option_ref = var.get("sc_item_option", {}).get("value") if isinstance(var.get("sc_item_option"), dict) else var.get("sc_item_option")
                        if option_ref:
                            # Obtener detalle de la variable
                            var_detail = await session.call_tool("snow_record_manage", {
                                "action": "get",
                                "table": "sc_item_option",
                                "sys_id": option_ref,
                                "display_value": False
                            })
                            var_detail_data = json.loads(var_detail.content[0].text)
                            var_record = var_detail_data["data"]["record"]
                            
                            name = var_record.get("name") or var_record.get("question_text") or option_ref
                            required = var_record.get("required", False)
                            default = var_record.get("default_value")
                            print(f"  - {name} (required: {required}, default: {default})")
                            
                            # Si la variable es de tipo 'reference', podríamos buscar opciones
                            if var_record.get("type") == "reference":
                                ref_table = var_record.get("reference")
                                print(f"      -> referencia a tabla: {ref_table}")
                                
                # Si no hay variables directas, puede que el item use un widget con variables en el frontend
                # En ese caso, necesitamos inspeccionar el widget asociado
                widget_id = cat_item.get("sp_widget") or cat_item.get("widget")
                if widget_id:
                    if isinstance(widget_id, dict):
                        widget_id = widget_id.get("value")
                    if widget_id:
                        print(f"\n🔧 Item usa widget: {widget_id}")
                        widget_result = await session.call_tool("snow_record_manage", {
                            "action": "get",
                            "table": "sp_widget",
                            "sys_id": widget_id,
                            "display_value": False
                        })
                        widget_data = json.loads(widget_result.content[0].text)
                        widget_record = widget_data["data"]["record"]
                        # El widget puede tener option_schema con definición de variables
                        widget_options = widget_record.get("option_schema")
                        if widget_options:
                            try:
                                options = json.loads(widget_options)
                                print("\n📋 Variables definidas en el widget (option_schema):")
                                print(json.dumps(options, indent=2))
                            except:
                                print(widget_options)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
