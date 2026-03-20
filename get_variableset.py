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
                
                # 1. Buscar el catálogo para ver su variable_set
                print("1. Verificando variable_set del catálogo 'User Onboarding'...")
                cat_item = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_cat_item",
                    "sys_id": "68a7f85d472f7290a3978f59e16d43af",
                    "display_value": False,
                    "fields": ["sys_id", "name", "variable_set", "variable_set_id"]
                })
                
                cat_data = json.loads(cat_item.content[0].text)
                record = cat_data["data"]["record"]
                var_set = record.get("variable_set", {}).get("value") if isinstance(record.get("variable_set"), dict) else record.get("variable_set")
                var_set_id = record.get("variable_set_id", {}).get("value") if isinstance(record.get("variable_set_id"), dict) else record.get("variable_set_id")
                
                print(f"   variable_set: {var_set}")
                print(f"   variable_set_id: {var_set_id}")
                
                # El usuario dio este ID: e01cab1a4f334200086eeed18110c71f
                target_var_set = var_set or var_set_id or "e01cab1a4f334200086eeed18110c71f"
                print(f"\n2. Usando variable_set: {target_var_set}")
                
                # 2. Buscar sc_item_option vinculados a ese variable_set
                # En ServiceNow, las variables de catálogo están en la tabla 'sp_widget' si es un variable set
                # o en 'sys_script'? No, las variables están en 'sp_widget' con variables en 'option_schema'
                
                # Primero, ver si ese ID es un sp_widget
                widget = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sp_widget",
                    "sys_id": target_var_set,
                    "display_value": False
                })
                
                widget_data = json.loads(widget.content[0].text)
                widget_record = widget_data["data"]["record"]
                
                print("\n3. sp_widget encontrado:")
                print(f"   name: {widget_record.get('name')}")
                
                # Obtener option_schema
                option_schema = widget_record.get("option_schema")
                if option_schema:
                    try:
                        schema = json.loads(option_schema)
                        print("\n4. Variables definidas en option_schema:")
                        print(json.dumps(schema, indent=2, ensure_ascii=False))
                        
                        # Extraer nombres de variables
                        variables = {}
                        if "properties" in schema:
                            for prop_name, prop_def in schema["properties"].items():
                                var_type = prop_def.get("type", "string")
                                # Para simplificar, si es string, damos un ejemplo de valor
                                example = ""
                                if var_type == "string":
                                    example = "Ejemplo: texto"
                                elif var_type == "number":
                                    example = "Ejemplo: 1"
                                elif var_type == "boolean":
                                    example = "Ejemplo: true"
                                elif var_type == "array":
                                    example = "Ejemplo: []"
                                elif "enum" in prop_def:
                                    example = f"Opciones: {prop_def['enum']}"
                                print(f"   - {prop_name} (tipo: {var_type}) {example}")
                                # Añadir a dict con valor vacío para preparar orden
                                variables[prop_name] = ""
                        
                        print(f"\n💡 Para ordenar el catálogo, necesitas pasar 'variables': {variables}")
                        print("   Rellena los valores según lo que requiera el proceso de onboarding.")
                        
                    except json.JSONDecodeError:
                        print("\n⚠️ option_schema no es JSON válido:")
                        print(option_schema)
                else:
                    print("\n❌ Este widget no tiene option_schema.")
                    
                # 3. Alternativa: Buscar en tabla 'sys_script' o 'sc_item_option' directamente
                # Pero si el widget es un variable set, las variables estarían en option_schema
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
