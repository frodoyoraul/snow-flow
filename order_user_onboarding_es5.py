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

# Constantes (ES5 friendly: usar mayúsculas para constantes)
SNOW_MCP_URL = "http://127.0.0.1:8765/sse"
SNOW_MCP_AUTH = ("admin", "Qwer123443")
CATALOG_NAME = "User Onboarding"
ABRAHAM_USERNAME = "abraham.lincoln"
# Datos para Abraham Lincoln
ABRAHAM_EMAIL = "abraham.lincoln@example.com"
ABRAHAM_FIRST_NAME = "Abraham"
ABRAHAM_LAST_NAME = "Lincoln"
# Departamento y location de ejemplo (podrían obtenerse dinámicamente)
DEFAULT_DEPARTMENT_SYS_ID = "a581ab703710200044e0bfc8bcbe5de8"  # Finance
DEFAULT_LOCATION_SYS_ID = None  # Se obtendrá en runtime
MANAGER_SYS_ID = "6816f79cc0a8016401c5a33be04be441"  # admin
START_DATE = "2025-04-01"

def get_val(field):
    """Extrae valor display o value de un campo, compatible con ServiceNow MCP."""
    if not field:
        return None
    if isinstance(field, dict):
        return field.get("display_value") or field.get("value")
    return field

async def get_location(session):
    """Obtiene un location válido de cmn_location."""
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
    """Busca un usuario por user_name y devuelve su sys_id."""
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
    """Obtiene el sc_cat_item por nombre y devuelve su sys_id."""
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
    """Obtiene todas las variables (item_option_new) asociadas al catálogo."""
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
    """
    Construye el diccionario de variables para la orden, cumpliendo obligatoriedades.
    Cada variable se identifica por su etiqueta legible (conversational_label, question_text, name).
    """
    var_dict = {}
    
    for var in variables_records:
        # Extraer etiqueta
        label = (get_val(var.get("conversational_label")) or
                 get_val(var.get("question_text")) or
                 get_val(var.get("name")) or
                 var.get("sys_id"))
        
        if not label:
            logger.warning("Variable without label, skipping")
            continue
        
        dtype = get_val(var.get("type"))
        ref_table = get_val(var.get("reference"))
        mandatory_raw = var.get("mandatory")
        mandatory = False
        if mandatory_raw:
            if isinstance(mandatory_raw, dict):
                mandatory = mandatory_raw.get("value") == "true" or mandatory_raw.get("display_value") == "true"
            else:
                mandatory = str(mandatory_raw).lower() in ["true", "1"]
        
        # Determinar valor
        value = ""
        
        if mandatory:
            if dtype == "8" and ref_table:  # reference
                if ref_table == "sys_user":
                    # Para 'Manager' se usa manager_id; para otros campos de usuario, abraham_id?
                    # Asumimos que si la etiqueta contiene 'Manager', usamos manager_id, si no, abraham_id?
                    if "manager" in label.lower():
                        value = manager_id
                    else:
                        value = abraham_id
                elif ref_table == "cmn_department":
                    value = department_id
                elif ref_table == "cmn_location":
                    value = location_id
                else:
                    logger.warning("Reference type %s not handled for %s", ref_table, label)
                    value = ""
            elif dtype == "10":  # date
                value = START_DATE
            elif dtype == "26":  # email (puede ser string)
                if "email" in label.lower():
                    value = ABRAHAM_EMAIL
                else:
                    value = "example@domain.com"
            elif dtype in ["6", "2"]:  # string o text
                # Asignar según etiqueta
                lbl_low = label.lower()
                if "first name" in lbl_low:
                    value = ABRAHAM_FIRST_NAME
                elif "last name" in lbl_low:
                    value = ABRAHAM_LAST_NAME
                elif "job title" in lbl_low:
                    value = "Employee"
                elif "personal email" in lbl_low:
                    value = ABRAHAM_EMAIL
                elif "corporate email" in lbl_low:
                    value = ABRAHAM_EMAIL
                else:
                    value = ""  # Podría ser requerido pero sin ejemplo; dejamos vacío y confiamos en validación
            else:
                logger.warning("Mandatory variable %s with type %s not specifically handled", label, dtype)
                value = ""
        else:
            # No mandatory, leave empty or provide reasonable default
            value = ""
        
        var_dict[label] = value
    
    return var_dict

async def create_catalog_order(session, cat_item_sys_id, requested_for_sys_id, variables):
    """Crea la orden mediante snow_order_catalog_item."""
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
    logger.info("=== Iniciando proceso de pedido de User Onboarding ===")
    
    async with sse_client(SNOW_MCP_URL, auth=SNOW_MCP_AUTH) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            logger.info("Conectado a Snow-Flow MCP")
            
            # 1. Obtener sys_id del catálogo
            cat_item_sys_id = await get_catalog_item(session, CATALOG_NAME)
            if not cat_item_sys_id:
                logger.error("No se encontró el catálogo '%s'", CATALOG_NAME)
                return
            logger.info("Catálogo encontrado: %s", cat_item_sys_id)
            
            # 2. Obtener sys_id de Abraham Lincoln
            abraham_id = await find_user_by_username(session, ABRAHAM_USERNAME)
            if not abraham_id:
                logger.error("No se encontró el usuario '%s'", ABRAHAM_USERNAME)
                return
            logger.info("Usuario Abraham encontrado: %s", abraham_id)
            
            # 3. Obtener location_id (opsional, pero necesario para variables que lo requieran)
            location_id = await get_location(session)
            if not location_id:
                logger.warning("No se encontró location; puede que falle si es mandatory")
            else:
                logger.info("Location seleccionada: %s", location_id)
            
            # 4. Obtener variables del catálogo
            var_records = await get_catalog_variables(session, cat_item_sys_id)
            if not var_records:
                logger.warning("No se encontraron variables para el catálogo; se enviará diccionario vacío")
                variables = {}
            else:
                # 5. Construir diccionario de variables
                variables = build_variables_dict(
                    var_records,
                    abraham_id=abraham_id,
                    location_id=location_id or "",
                    department_id=DEFAULT_DEPARTMENT_SYS_ID,
                    manager_id=MANAGER_SYS_ID
                )
                logger.info("Variables construidas (%d): %s", len(variables), json.dumps(variables, indent=2))
            
            # 6. Crear la orden
            logger.info("Creando orden para %s (sys_id: %s)...", ABRAHAM_USERNAME, abraham_id)
            order_result = await create_catalog_order(session, cat_item_sys_id, abraham_id, variables)
            
            if order_result and order_result.get("success"):
                data = order_result["data"]
                ritm_number = data.get("ritm_number")
                ritm_sys_id = data.get("ritm_id")
                logger.info("✅ Orden creada exitosamente: %s (sys_id: %s)", ritm_number, ritm_sys_id)
                logger.info("📋 Detalles: %s", json.dumps(data, indent=2))
            else:
                logger.error("❌ Falló la creación de orden: %s", order_result)
    
    logger.info("=== Proceso finalizado ===")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario")
