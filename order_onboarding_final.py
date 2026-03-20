#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('snow_order_onboarding')

# Constantes
SNOW_MCP_URL = "http://127.0.0.1:8765/sse"
SNOW_MCP_AUTH = ("admin", "Qwer123443")
CATALOG_NAME = "User Onboarding"
ABRAHAM_USERNAME = "abraham.lincoln"
ABRAHAM_EMAIL = "abraham.lincoln@example.com"
ABRAHAM_FIRST_NAME = "Abraham"
ABRAHAM_LAST_NAME = "Lincoln"
DEFAULT_DEPARTMENT_SYS_ID = "a581ab703710200044e0bfc8bcbe5de8"  # Finance
MANAGER_SYS_ID = "6816f79cc0a8016401c5a33be04be441"  # admin
START_DATE = "2025-04-01"

def get_val(field):
    if not field:
        return None
    if isinstance(field, dict):
        return field.get("display_value") or field.get("value")
    return field

async def get_location(session):
    try:
        result = await session.call_tool("snow_record_manage", {
            "action": "query",
            "table": "cmn_location",
            "limit": 1,
            "display_value": False
        })
        data = json.loads(result.content[0].text)
        records = data["data"]["records"]
        if records:
            return records[0].get("sys_id")
    except Exception as e:
        logger.error("Error obtaining location: %s", e)
    return None

async def find_user_by_username(session, username):
    try:
        result = await session.call_tool("snow_record_manage", {
            "action": "query",
            "table": "sys_user",
            "query": f"user_name={username}",
            "limit": 1,
            "display_value": False,
            "fields": ["sys_id"]
        })
        data = json.loads(result.content[0].text)
        records = data["data"]["records"]
        if records:
            return records[0].get("sys_id")
    except Exception as e:
        logger.error("Error finding user %s: %s", username, e)
    return None

async def get_catalog_item(session, catalog_name):
    try:
        result = await session.call_tool("snow_record_manage", {
            "action": "query",
            "table": "sc_cat_item",
            "query": f"name={catalog_name}^active=true",
            "limit": 1,
            "display_value": False,
            "fields": ["sys_id", "name"]
        })
        data = json.loads(result.content[0].text)
        records = data["data"]["records"]
        if records:
            return records[0].get("sys_id")
    except Exception as e:
        logger.error("Error finding catalog '%s': %s", catalog_name, e)
    return None

async def get_catalog_variables(session, cat_item_sys_id):
    try:
        result = await session.call_tool("snow_record_manage", {
            "action": "query",
            "table": "item_option_new",
            "query": f"cat_item={cat_item_sys_id}",
            "limit": 100,
            "display_value": True,
            "fields": ["sys_id", "conversational_label", "question_text", "name", "type", "reference", "mandatory"]
        })
        data = json.loads(result.content[0].text)
        records = data["data"]["records"]
        logger.info("Found %d variables for catalog", len(records))
        return records
    except Exception as e:
        logger.error("Error getting catalog variables: %s", e)
        return []

def build_variables_dict(variables_records, abraham_id, location_id, department_id, manager_id):
    var_dict = {}
    
    for var in variables_records:
        label = (get_val(var.get("conversational_label")) or
                 get_val(var.get("question_text")) or
                 get_val(var.get("name")) or
                 var.get("sys_id"))
        
        if not label:
            logger.warning("Variable without label, skipping")
            continue
        
        dtype = get_val(var.get("type"))  # Ej: "Email", "Reference", "Single Line Text", "Date/Time"
        ref_table = get_val(var.get("reference"))
        mandatory_raw = var.get("mandatory")
        mandatory = False
        if mandatory_raw:
            if isinstance(mandatory_raw, dict):
                mandatory = mandatory_raw.get("value") == "true" or mandatory_raw.get("display_value") == "true"
            else:
                mandatory = str(mandatory_raw).lower() in ["true", "1"]
        
        value = ""
        lbl_low = label.lower()
        
        if mandatory:
            # References
            if dtype == "Reference" and ref_table:
                if ref_table == "sys_user":
                    if "manager" in lbl_low:
                        value = manager_id
                    else:
                        value = abraham_id
                elif ref_table == "cmn_department":
                    value = department_id
                elif ref_table == "cmn_location":
                    value = location_id
                else:
                    logger.warning("Unhandled reference %s -> %s", label, ref_table)
                    value = ""
            # Email
            elif dtype == "Email":
                if "personal" in lbl_low:
                    value = ABRAHAM_EMAIL
                elif "corporate" in lbl_low:
                    value = ABRAHAM_EMAIL
                else:
                    value = ABRAHAM_EMAIL
            # Date/Time
            elif dtype == "Date/Time":
                value = START_DATE
            # Single Line Text, String, Text
            elif dtype in ["String", "Single Line Text", "Text"]:
                if "first name" in lbl_low:
                    value = ABRAHAM_FIRST_NAME
                elif "last name" in lbl_low:
                    value = ABRAHAM_LAST_NAME
                elif "job title" in lbl_low:
                    value = "Employee"
                else:
                    # Podría ser required pero no tenemos ejemplo; dejamos vacío por ahora
                    value = ""
            else:
                logger.warning("Mandatory variable %s with type %s not handled", label, dtype)
                value = ""
        else:
            value = ""
        
        var_dict[label] = value
    
    return var_dict

async def create_catalog_order(session, cat_item_sys_id, requested_for_sys_id, variables):
    try:
        result = await session.call_tool("snow_order_catalog_item", {
            "cat_item": cat_item_sys_id,
            "requested_for": requested_for_sys_id,
            "variables": variables,
            "quantity": 1
        })
        data = json.loads(result.content[0].text)
        return data
    except Exception as e:
        logger.error("Error creating order: %s", e)
        return None

async def main():
    logger.info("=== Iniciando pedido de User Onboarding ===")
    
    async with sse_client(SNOW_MCP_URL, auth=SNOW_MCP_AUTH) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            logger.info("Conectado a Snow-Flow MCP")
            
            cat_item_sys_id = await get_catalog_item(session, CATALOG_NAME)
            if not cat_item_sys_id:
                logger.error("Catálogo '%s' no encontrado", CATALOG_NAME)
                return
            logger.info("Catálogo: %s", cat_item_sys_id)
            
            abraham_id = await find_user_by_username(session, ABRAHAM_USERNAME)
            if not abraham_id:
                logger.error("Usuario '%s' no encontrado", ABRAHAM_USERNAME)
                return
            logger.info("Usuario Abraham: %s", abraham_id)
            
            location_id = await get_location(session)
            if not location_id:
                logger.warning("Location no encontrada; puede causar error si es mandatory")
            else:
                logger.info("Location: %s", location_id)
            
            var_records = await get_catalog_variables(session, cat_item_sys_id)
            if not var_records:
                logger.warning("No hay variables definidas; se envía diccionario vacío")
                variables = {}
            else:
                variables = build_variables_dict(
                    var_records,
                    abraham_id=abraham_id,
                    location_id=location_id or "",
                    department_id=DEFAULT_DEPARTMENT_SYS_ID,
                    manager_id=MANAGER_SYS_ID
                )
                logger.info("Variables construidas (%d): %s", len(variables), json.dumps(variables, indent=2, ensure_ascii=False))
            
            logger.info("Creando orden para %s...", ABRAHAM_USERNAME)
            order_result = await create_catalog_order(session, cat_item_sys_id, abraham_id, variables)
            
            if order_result and order_result.get("success"):
                data = order_result["data"]
                logger.info("✅ Orden creada: %s (sys_id: %s)", data.get("ritm_number"), data.get("ritm_id"))
                logger.info("Detalles: %s", json.dumps(data, indent=2, ensure_ascii=False))
            else:
                logger.error("❌ Falló la orden: %s", order_result)
    
    logger.info("=== Proceso finalizado ===")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrumpido por el usuario")
