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
    
    try:
        async with sse_client(url, auth=auth) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                
                ritm_sys_id = "c29091f347e77614a3978f59e16d4318"
                
                # 1. Obtener el RITM
                print(f"1. Inspeccionando RITM {ritm_sys_id}...")
                ritm = await session.call_tool("snow_record_manage", {
                    "action": "get",
                    "table": "sc_req_item",
                    "sys_id": ritm_sys_id,
                    "display_value": True
                })
                ritm_data = json.loads(ritm.content[0].text)
                ritm_record = ritm_data["data"]["record"]
                
                print("\n📦 RITM Campos clave:")
                for key in ["number", "state", "cat_item", "requested_for", "opened_by", "sys_class_name"]:
                    val = ritm_record.get(key)
                    if isinstance(val, dict):
                        print(f"  {key}: {val.get('display_value')} (sys_id: {val.get('value')})")
                    else:
                        print(f"  {key}: {val}")
                
                cat_item_id = None
                cat_item_field = ritm_record.get("cat_item")
                if cat_item_field:
                    if isinstance(cat_item_field, dict):
                        cat_item_id = cat_item_field.get("value")
                    else:
                        cat_item_id = cat_item_field
                print(f"\nCatálogo asociado: {cat_item_id}")
                
                # 2. Buscar variables asociadas al RITM (item_option_new con request_item = ritm_sys_id)
                print(f"\n2. Buscando item_option_new vinculados a este RITM (request_item={ritm_sys_id})...")
                vars_ritm = await session.call_tool("snow_record_manage", {
                    "action": "query",
                    "table": "item_option_new",
                    "query": f"request_item={ritm_sys_id}",
                    "limit": 100,
                    "display_value": True,
                    "fields": ["sys_id", "name", "question_text", "conversational_label", "type", "reference", "mandatory"]
                })
                vars_data = json.loads(vars_ritm.content[0].text)
                var_records = vars_data["data"]["records"]
                print(f"   Variables encontradas: {len(var_records)}\n")
                
                if var_records:
                    print("📋 Lista de variables del RITM:")
                    for v in var_records:
                        lbl = (get_val(v.get("conversational_label")) or
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
                        # Valor asignado
                        val_field = v.get("value") or v.get("default_value")
                        val = get_val(val_field) if val_field else ""
                        print(f"  - {lbl}")
                        print(f"      type: {dtype}, reference: {ref}, mandatory: {mand_str}")
                        print(f"      value: {val}")
                        print()
                    
                    # 3. Comparar con las variables del catálogo (cat_item) si las encontramos
                    if cat_item_id:
                        print(f"3. Comparando con variables del catálogo (cat_item={cat_item_id})...")
                        vars_cat = await session.call_tool("snow_record_manage", {
                            "action": "query",
                            "table": "item_option_new",
                            "query": f"cat_item={cat_item_id}",
                            "limit": 100,
                            "display_value": True,
                            "fields": ["sys_id", "name", "question_text", "conversational_label", "type", "reference", "mandatory"]
                        })
                        cats_data = json.loads(vars_cat.content[0].text)
                        cat_vars = cats_data["data"]["records"]
                        print(f"   Variables del catálogo: {len(cat_vars)}\n")
                        
                        # Mostrar variables del catálogo
                        for v in cat_vars:
                            lbl = (get_val(v.get("conversational_label")) or
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
                            print(f"  - {lbl} (type: {dtype}, ref: {ref}, mandatory: {mand_str})")
                        
                else:
                    print("❌ No se encontraron variables para este RITM.")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
