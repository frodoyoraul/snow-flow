#!/usr/bin/env python3
import asyncio
import json
import logging
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('snow_order_onboarding_manual')

SNOW_MCP_URL = "http://127.0.0.1:8765/sse"
SNOW_MCP_AUTH = ("admin", "Qwer123443")
CATALOG_NAME = "User Onboarding"
ABRAHAM_USERNAME = "abraham.lincoln"
ABRAHAM_EMAIL = "abraham.lincoln@example.com"
ABRAHAM_FIRST_NAME = "Abraham"
ABRAHAM_LAST_NAME = "Lincoln"
DEFAULT_DEPARTMENT_SYS_ID = "a581ab703710200044e0bfc8bcbe5de8"
MANAGER_SYS_ID = "6816f79cc0a8016401c5a33be04be441"
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
            "display_value": False,
            "fields": ["sys_id", "type", "reference", "mandatory"]
        })
        data = json.loads(result.content[0].text)
        records = data["data"]["records"]
        logger.info("Found %d variables for catalog", len(records))
        return records
    except Exception as e:
        logger.error("Error getting catalog variables: %s", e)
        return []

def normalize_type(dtype):
    if dtype is None:
        return None
    if isinstance(dtype, dict):
        dtype = dtype.get("display_value") or dtype.get("value")
    if isinstance(dtype, str):
        try:
            return int(dtype)
        except ValueError:
            return dtype
    return dtype

def assign_label_and_value(var, counters):
    """
    Determina etiqueta legible y valor para una variable del catálogo.
    counters: dict con contadores para email, text references, etc.
    Returns: (label, value) o (None, None) si no es mandatory o no se puede asignar.
    """
    dtype_raw = var.get("type")
    dtype = normalize_type(dtype_raw)
    ref_table = get_val(var.get("reference"))
    mandatory_raw = var.get("mandatory")
    mandatory = False
    if mandatory_raw:
        if isinstance(mandatory_raw, dict):
            mandatory = mandatory_raw.get("value") == "true" or mandatory_raw.get("display_value") == "true"
        else:
            mandatory = str(mandatory_raw).lower() in ["true", "1"]
    
    if not mandatory:
        return None, None
    
    # Inicializar contadores si no existen
    if 'email_cnt' not in counters:
        counters['email_cnt'] = 0
    if 'text_cnt' not in counters:
        counters['text_cnt'] = 0
    if 'loc_assigned' not in counters:
        counters['loc_assigned'] = False
    
    label = None
    value = ""
    
    # Reference a sys_user -> Manager
    if dtype == 8 and ref_table == "sys_user":
        label = "Manager"
        value = MANAGER_SYS_ID
    # Reference a cmn_department -> Department
    elif dtype == 8 and ref_table == "cmn_department":
        label = "Department"
        value = DEFAULT_DEPARTMENT_SYS_ID
    # Reference a cmn_location -> Location
    elif dtype == 8 and ref_table == "cmn_location":
        label = "Location"
        # location_id se pasa externamente
        value = counters.get('location_id', "")
        counters['loc_assigned'] = True
    # Email (type 26)
    elif dtype == 26:
        if counters['email_cnt'] == 0:
            label = "Personal Email"
            value = ABRAHAM_EMAIL
        elif counters['email_cnt'] == 1:
            label = "Corporate Email"
            value = ABRAHAM_EMAIL
        else:
            label = None
        counters['email_cnt'] += 1
    # Date/Time (type 10)
    elif dtype == 10:
        label = "Start Date"
        value = START_DATE
    # Text types (6,1,2)
    elif dtype in [6, 1, 2]:
        if counters['text_cnt'] == 0:
            label = "First Name"
            value = ABRAHAM_FIRST_NAME
        elif counters['text_cnt'] == 1:
            label = "Last Name"
            value = ABRAHAM_LAST_NAME
        elif counters['text_cnt'] == 2:
            label = "Job Title"
            value = "Employee"
        else:
            label = None
        counters['text_cnt'] += 1
    else:
        logger.warning("Unhandled mandatory type: %s (ref: %s)", dtype, ref_table)
        return None, None
    
    return label, value

async def create_ritm(session, cat_item_sys_id, requested_for_sys_id):
    """Crea el RITM sin variables."""
    try:
        result = await session.call_tool("snow_order_catalog_item", {
            "cat_item": cat_item_sys_id,
            "requested_for": requested_for_sys_id,
            "variables": {},  # vacío
            "quantity": 1
        })
        data = json.loads(result.content[0].text)
        if data.get("success"):
            return data["data"]["ritm_id"]
        else:
            logger.error("Failed to create RITM: %s", data)
            return None
    except Exception as e:
        logger.error("Error creating RITM: %s", e)
        return None

async def create_variable(session, ritm_id, var_def):
    """
    Crea un registro item_option_new para el RITM.
    var_def: dict con sys_id, type, reference, mandatory, y además label y value.
    """
    try:
        payload = {
            "action": "create",
            "table": "item_option_new",
            "request_item": ritm_id,
            "name": var_def["label"],  # etiqueta legible
            "type": var_def["type"],
            "mandatory": var_def["mandatory"]
        }
        if var_def.get("reference"):
            payload["reference"] = var_def["reference"]
        if var_def.get("value") is not None:
            payload["value"] = var_def["value"]
        
        result = await session.call_tool("snow_record_manage", payload)
        data = json.loads(result.content[0].text)
        if data.get("success") or data.get("created"):
            return True
        else:
            logger.warning("Failed to create variable %s: %s", var_def["label"], data)
            return False
    except Exception as e:
        logger.error("Error creating variable: %s", e)
        return False

async def main():
    logger.info("=== Iniciando pedido de User Onboarding (manual vars) ===")
    
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
                logger.error("No hay variables definidas para el catálogo")
                return
            
            # Paso 1: Crear RITM sin variables
            logger.info("Creando RITM sin variables...")
            ritm_id = await create_ritm(session, cat_item_sys_id, abraham_id)
            if not ritm_id:
                logger.error("No se pudo crear el RITM")
                return
            logger.info("RITM creado: sys_id=%s", ritm_id)
            
            # Paso 2: Para cada variable mandatory, crear item_option_new con etiqueta y valor
            counters = {'email_cnt': 0, 'text_cnt': 0, 'loc_assigned': False, 'location_id': location_id}
            created_vars = 0
            
            logger.info("Creando variables obligatorias...")
            for var in var_records:
                var_sys_id = var.get("sys_id")
                if not var_sys_id:
                    continue
                
                label, value = assign_label_and_value(var, counters)
                if not label:
                    continue  # no mandatory o no manejada
                
                # Obtener tipo y referencia para crear la variable
                dtype_raw = var.get("type")
                dtype = normalize_type(dtype_raw)
                ref_table = get_val(var.get("reference"))
                mandatory = True
                
                var_def = {
                    "label": label,
                    "type": dtype,
                    "reference": ref_table,
                    "mandatory": mandatory,
                    "value": value
                }
                
                success = await create_variable(session, ritm_id, var_def)
                if success:
                    created_vars += 1
                    logger.info("  Creada variable: %s = %s", label, value)
                else:
                    logger.warning("  Falló variable: %s", label)
            
            logger.info("✅ Creadas %d variables para el RITM %s", created_vars, ritm_id)
            logger.info("🔄 El monitor de auto-aprobación está activo.")
            logger.info("=== Proceso finalizado ===")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrumpido por el usuario")
