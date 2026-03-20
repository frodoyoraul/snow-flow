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
                print(f"🔍 Buscando variable en sc_item_option con sys_id={var_id}...")
                
                var = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_item_option",
                    "sys_id": var_id,
                    "display_value": True
                })
                
                var_data = json.loads(var.content[0].text)
                
                if not var_data.get("success"):
                    print(f"❌ No encontrada: {var_data.get('error')}")
                    return
                
                record = var_data["data"]["record"]
                print("\n📦 Variable encontrada:")
                print(json.dumps(record, indent=2, ensure_ascii=False))
                
                # Extraer nombre, tipo, requerida
                def get_field(val):
                    if isinstance(val, dict):
                        return val.get("display_value") or val.get("value") or ""
                    return val or ""
                
                name = get_field(record.get("name") or record.get("question_text"))
                dtype = get_field(record.get("type") or record.get("data_type"))
                required = get_field(record.get("required"))
                default = get_field(record.get("default_value"))
                reference = get_field(record.get("reference"))
                
                print(f"\n🔹 Nombre: {name}")
                print(f"🔹 Tipo: {dtype}")
                print(f"🔹 Required: {required}")
                print(f"🔹 Default: {default}")
                if reference:
                    print(f"🔹 Reference: {reference}")
                
                # Si es una referencia, podríamos buscar valores de ejemplo
                if reference:
                    print(f"\n🔍 Buscando valores de ejemplo en tabla {reference}...")
                    try:
                        sample = await session.call_tool("snow_record_manage", {
                            "action": "query",
                            "table": reference,
                            "limit": 5,
                            "display_value": True
                        })
                        sample_data = json.loads(sample.content[0].text)
                        samples = sample_data["data"]["records"]
                        print(f"📋 Muestras de {reference}:")
                        for s in samples:
                            display = s.get("name") or s.get("sys_id")
                            print(f"  - {display}")
                    except Exception as e:
                        print(f"❌ Error buscando muestras: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
