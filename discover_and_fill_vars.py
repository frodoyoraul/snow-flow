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
                
                # Traer TODOS los campos de la variable con display_value=True para ver label, etc.
                var_id = "70c6a0ff47c73e50a3978f59e16d4324"
                var = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "item_option_new",
                    "sys_id": var_id,
                    "display_value": True
                })
                
                var_data = json.loads(var.content[0].text)
                record = var_data["data"]["record"]
                
                print("📦 Variable completa (display_value=True):\n")
                for key, val in record.items():
                    if key not in ["_url"]:
                        if isinstance(val, dict):
                            print(f"{key}: {val.get('display_value')} (value: {val.get('value')})")
                        else:
                            print(f"{key}: {val}")
                
                # Extraer cualquier campo que sirva como etiqueta
                label_candidates = ["conversational_label", "label", "name", "question_text", "description"]
                label = None
                for cand in label_candidates:
                    val = record.get(cand)
                    if val:
                        if isinstance(val, dict):
                            lbl = val.get("display_value") or val.get("value")
                        else:
                            lbl = val
                        if lbl:
                            label = lbl
                            break
                
                print(f"\n🔖 Etiqueta seleccionada: {label or '(ninguna)'}")
                print(f"🔗 Reference: {record.get('reference')}")
                print(f"🔒 Mandatory: {record.get('mandatory')}")
                
                # Ahora, construir la plantilla de variables necesarias
                # Tenemos al menos 1 variable. Buscar todas las variables del catálogo
                cat_item_id = "68a7f85d472f7290a3978f59e16d43af"
                direct_vars = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"cat_item={cat_item_id}",
                    "limit": 100,
                    "display_value": True
                })
                direct_data = json.loads(direct_vars.content[0].text)
                var_records = direct_data["data"]["records"]
                
                print(f"\n📚 Variables totales del catálogo: {len(var_records)}")
                
                var_template = {}
                for v in var_records:
                    # Extraer etiqueta
                    lbl = None
                    for cand in label_candidates:
                        val = v.get(cand)
                        if val:
                            if isinstance(val, dict):
                                l = val.get("display_value") or val.get("value")
                            else:
                                l = val
                            if l:
                                lbl = l
                                break
                    if not lbl:
                        # Usar sys_id como fallback
                        lbl = v.get("sys_id")
                    if lbl:
                        var_template[lbl] = ""
                
                print("\n💡 Plantilla de variables a completar:")
                print(json.dumps(var_template, indent=2, ensure_ascii=False))
                
                # Preparar valores para la orden - para referencia tipo sys_user, necesitamos el sys_id del usuario
                # Abraham Lincoln ya tiene sys_id: a8f98bb0eb32010045e1a5115206fe3a
                # Asignaremos a la variable que referencia sys_user el usuario Abraham
                var_values = {}
                for v in var_records:
                    ref = v.get("reference")
                    if ref and ref.get("value") == "sys_user":
                        # Encontrar etiqueta de esta variable
                        lbl = None
                        for cand in label_candidates:
                            val = v.get(cand)
                            if val:
                                if isinstance(val, dict):
                                    l = val.get("display_value") or val.get("value")
                                else:
                                    l = val
                                if l:
                                    lbl = l
                                    break
                        if lbl:
                            var_values[lbl] = "a8f98bb0eb32010045e1a5115206fe3a"  # sys_id de Abraham
                    else:
                        # Para otras variables, dejamos vacío? O necesitamos valores por defecto?
                        # Si son mandatory, necesitamos valor. Por ahora las dejamos vacías y veremos error.
                        lbl = None
                        for cand in label_candidates:
                            val = v.get(cand)
                            if val:
                                if isinstance(val, dict):
                                    l = val.get("display_value") or val.get("value")
                                else:
                                    l = val
                                if l:
                                    lbl = l
                                    break
                        if lbl:
                            var_values[lbl] = ""
                
                print("\n📝 Valores propuestos para la orden:")
                print(json.dumps(var_values, indent=2, ensure_ascii=False))
                
                # Crear orden con estos valores
                print("\n🛒 Creando orden para Abraham con variables...")
                order = await session.call_tool("snow_order_catalog_item", {
                    "cat_item": cat_item_id,
                    "requested_for": "a8f98bb0eb32010045e1a5115206fe3a",
                    "variables": var_values
                })
                order_data = json.loads(order.content[0].text)
                print("\n📦 Resultado:")
                print(json.dumps(order_data, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
