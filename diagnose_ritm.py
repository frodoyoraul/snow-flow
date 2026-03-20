#!/usr/bin/env python3
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

def get_val(field):
    if not field:
        return None
    if isinstance(field, dict):
        return field.get("display_value") or field.get("value")
    return field

async def main():
    url = "http://127.0.0.1:8765/sse"
    auth = ("admin", "Qwer123443")
    # Probar con varios RITMs recientes
    ritm_ids = [
        "c2c0949a47f73e14a3978f59e16d4351",  # RITM0010046 (manual)
        # Agregar otros sys_id recientes si los conocemos
    ]
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                for ritm_sys_id in ritm_ids:
                    print(f"\n=== Revisando RITM {ritm_sys_id} ===\n")
                    
                    # 1. Datos del RITM
                    print("1. RITM sc_req_item:")
                    ritm = await session.call_tool("snow_record_manage", {
                        "action": "get",
                        "table": "sc_req_item",
                        "sys_id": ritm_sys_id,
                        "display_value": True
                    })
                    ritm_data = json.loads(ritm.content[0].text)
                    if ritm_data.get("success"):
                        rec = ritm_data["data"]["record"]
                        print(f"  number: {rec.get('number')}")
                        print(f"  state: {rec.get('state')}")
                        print(f"  cat_item: {rec.get('cat_item')}")
                        print(f"  requested_for: {rec.get('requested_for')}")
                    else:
                        print("  RITM no encontrado o sin permisos")
                    
                    # 2. Variables del RITM (item_option_new con request_item)
                    print("\n2. Variables (item_option_new):")
                    vars_q = await session.call_tool("snow_record_manage", {
                        "action": "query",
                        "table": "item_option_new",
                        "query": f"request_item={ritm_sys_id}",
                        "limit": 50,
                        "display_value": True,
                        "fields": ["sys_id", "name", "question_text", "conversational_label", "type", "reference", "mandatory", "value", "order"]
                    })
                    vars_data = json.loads(vars_q.content[0].text)
                    var_recs = vars_data["data"]["records"]
                    print(f"   Total: {len(var_recs)}\n")
                    
                    if var_recs:
                        # Mostrar cada variable con todos los campos clave
                        for i, v in enumerate(var_recs, 1):
                            label = (get_val(v.get("conversational_label")) or
                                     get_val(v.get("question_text")) or
                                     get_val(v.get("name")) or
                                     v.get("sys_id"))
                            dtype = get_val(v.get("type"))
                            ref = get_val(v.get("reference"))
                            mand = v.get("mandatory")
                            mand_str = "false"
                            if mand:
                                if isinstance(mand, dict):
                                    mand_str = mand.get("value") or mand.get("display_value") or "false"
                                else:
                                    mand_str = str(mand).lower()
                            val = get_val(v.get("value")) or ""
                            order = v.get("order") or ""
                            print(f"{i}. {label}")
                            print(f"   sys_id: {v.get('sys_id')}")
                            print(f"   type: {dtype}, reference: {ref}, mandatory: {mand_str}, order: {order}")
                            print(f"   value: {val}")
                            print()
                    
                    # 3. Variables del catálogo (para comparar)
                    print("3. Variables del catálogo (item_option_new con cat_item del catálogo):")
                    # Primero obtener el cat_item del RITM
                    cat_item_id = None
                    if ritm_data.get("success"):
                        rec = ritm_data["data"]["record"]
                        cat_field = rec.get("cat_item")
                        if cat_field:
                            cat_item_id = get_val(cat_field)
                    
                    if cat_item_id:
                        cat_vars = await session.call_tool("snow_record_manage", {
                            "action": "query",
                            "table": "item_option_new",
                            "query": f"cat_item={cat_item_id}",
                            "limit": 50,
                            "display_value": True,
                            "fields": ["sys_id", "name", "question_text", "conversational_label", "type", "reference", "mandatory", "order"]
                        })
                        cat_data = json.loads(cat_vars.content[0].text)
                        cat_recs = cat_data["data"]["records"]
                        print(f"   Total: {len(cat_recs)}\n")
                        
                        for i, v in enumerate(cat_recs, 1):
                            label = (get_val(v.get("conversational_label")) or
                                     get_val(v.get("question_text")) or
                                     get_val(v.get("name")) or
                                     v.get("sys_id"))
                            dtype = get_val(v.get("type"))
                            ref = get_val(v.get("reference"))
                            mand = v.get("mandatory")
                            mand_str = "false"
                            if mand:
                                if isinstance(mand, dict):
                                    mand_str = mand.get("value") or mand.get("display_value") or "false"
                                else:
                                    mand_str = str(mand).lower()
                            order = v.get("order") or ""
                            print(f"{i}. {label} (sys_id: {v.get('sys_id')})")
                            print(f"   type: {dtype}, reference: {ref}, mandatory: {mand_str}, order: {order}")
                            print()
                    else:
                        print("  No se pudo obtener cat_item del RITM")
                    
                    # 4. Comparativa: variables del RITM vs catálogo
                    if var_recs and cat_item_id and cat_recs:
                        print("4. Comparativa:")
                        ritm_sysids = {v.get('sys_id') for v in var_recs}
                        cat_sysids = {v.get('sys_id') for v in cat_recs}
                        print(f"   Variables del RITM que NO están en catálogo: {ritm_sysids - cat_sysids}")
                        print(f"   Variables del catálogo que NO están en RITM: {cat_sysids - ritm_sysids}")
                        print()
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
