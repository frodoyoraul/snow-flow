#!/bin/bash
# Crear RITM para User Onboarding directamente via API REST de ServiceNow (Snow-Flow)

SNOW_URL="http://127.0.0.1:3000"
USERNAME="admin"
PASSWORD="Qwer123443"
CATALOG_SYS_ID="68a7f85d472f7290a3978f59e16d43af"
ABRAHAM_USERNAME="abraham.lincoln"
ABRAHAM_EMAIL="abraham.lincoln@example.com"
ABRAHAM_FIRST="Abraham"
ABRAHAM_LAST="Lincoln"
MANAGER_SYS_ID="6816f79cc0a8016401c5a33be04be441"
DEPT_SYS_ID="a581ab703710200044e0bfc8bcbe5de8"

# 1. Obtener sys_id de Abraham
echo "1. Obteniendo sys_id de ${ABRAHAM_USERNAME}..."
ABRAHAM_SYS_ID=$(curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/sys_user?sysparm_query=user_name=${ABRAHAM_USERNAME}&sysparm_fields=sys_id&sysparm_limit=1" \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['sys_id'] if data['result'] else '')")

if [ -z "$ABRAHAM_SYS_ID" ]; then
  echo "No se encontró usuario Abraham"
  exit 1
fi
echo "   Abraham sys_id: $ABRAHAM_SYS_ID"

# 2. Crear RITM (sc_req_item)
echo "2. Creando RITM..."
RITM_RESPONSE=$(curl -s -X POST -u "${USERNAME}:${PASSWORD}" \
  -H "Content-Type: application/json" \
  -d "{\"cat_item\":\"${CATALOG_SYS_ID}\",\"requested_for\":\"${ABRAHAM_SYS_ID}\"}" \
  "${SNOW_URL}/api/now/table/sc_req_item")

RITM_SYS_ID=$(echo "$RITM_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result']['sys_id'] if 'result' in data and 'sys_id' in data['result'] else '')")
if [ -z "$RITM_SYS_ID" ]; then
  echo "Falló la creación del RITM: $RITM_RESPONSE"
  exit 1
fi
echo "   RITM creado: $RITM_SYS_ID"

# 3. Obtener location (primera encontrada)
echo "3. Obteniendo location..."
LOCATION_SYS_ID=$(curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/cmn_location?sysparm_fields=sys_id&sysparm_limit=1" \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['sys_id'] if data['result'] else '')")
echo "   Location: $LOCATION_SYS_ID"

# 4. Obtener variables del catálogo (item_option_new con cat_item)
echo "4. Obteniendo variables del catálogo..."
VARIABLES_JSON=$(curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/item_option_new?sysparm_query=cat_item=${CATALOG_SYS_ID}&sysparm_fields=sys_id,type,reference,mandatory&sysparm_limit=100")

# 5. Crear variables para el RITM (item_option_new con request_item)
echo "5. Creando variables..."
python3 - <<PYTHON
import json, sys, requests, base64
from requests.auth import HTTPBasicAuth

# Parámetros
SNOW_URL = "${SNOW_URL}"
USERNAME = "${USERNAME}"
PASSWORD = "${PASSWORD}"
RITM_SYS_ID = "${RITM_SYS_ID}"
ABRAHAM_SYS_ID = "${ABRAHAM_SYS_ID}"
ABRAHAM_EMAIL = "${ABRAHAM_EMAIL}"
ABRAHAM_FIRST = "${ABRAHAM_FIRST}"
ABRAHAM_LAST = "${ABRAHAM_LAST}"
MANAGER_SYS_ID = "${MANAGER_SYS_ID}"
DEPT_SYS_ID = "${DEPT_SYS_ID}"
LOCATION_SYS_ID = "${LOCATION_SYS_ID}"

# Datos de variables del catálogo
cat_vars = json.loads('''${VARIABLES_JSON}''')['result']

# Conteo para asignar textos
counts = {"email":0, "text":0}

for var in cat_vars:
    var_sys_id = var['sys_id']
    dtype = var.get('type')
    if isinstance(dtype, dict):
        dtype = dtype.get('value') or dtype.get('display_value')
    ref = var.get('reference')
    if isinstance(ref, dict):
        ref = ref.get('value') or ref.get('display_value')
    mand = var.get('mandatory')
    if isinstance(mand, dict):
        mand = mand.get('value') == 'true' or mand.get('display_value') == 'true'
    else:
        mand = str(mand).lower() in ['true', '1']
    
    # Solo crear variables mandatory
    if not mand:
        continue
    
    label = None
    value = ""
    
    # Determinar por tipo y referencia
    if dtype == 8 and ref == "sys_user":  # Reference
        label = "Manager"
        value = MANAGER_SYS_ID
    elif dtype == 8 and ref == "cmn_department":
        label = "Department"
        value = DEPT_SYS_ID
    elif dtype == 8 and ref == "cmn_location":
        label = "Location"
        value = LOCATION_SYS_ID
    elif dtype == 26:  # Email
        if counts["email"] == 0:
            label = "Personal Email"
            value = ABRAHAM_EMAIL
        elif counts["email"] == 1:
            label = "Corporate Email"
            value = ABRAHAM_EMAIL
        counts["email"] += 1
    elif dtype == 10:  # Date/Time
        label = "Start Date"
        value = "2025-04-01"
    elif dtype in [6, 1, 2]:  # Text types
        if counts["text"] == 0:
            label = "First Name"
            value = ABRAHAM_FIRST
        elif counts["text"] == 1:
            label = "Last Name"
            value = ABRAHAM_LAST
        elif counts["text"] == 2:
            label = "Job Title"
            value = "Employee"
        counts["text"] += 1
    else:
        # Otros tipos no manejados, omitir
        continue
    
    if label:
        # Crear variable item_option_new
        payload = {
            "request_item": RITM_SYS_ID,
            "name": label,
            "type": dtype,
            "mandatory": mand,
            "value": value
        }
        if ref:
            payload["reference"] = ref
        
        resp = requests.post(
            f"{SNOW_URL}/api/now/table/item_option_new",
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers={"Content-Type":"application/json"},
            json=payload
        )
        if resp.status_code == 201:
            print(f"  Creada: {label} = {value}")
        else:
            print(f"  Error creando {label}: {resp.status_code} {resp.text}")
PYTHON

echo "6. Finalizado. RITM: $RITM_SYS_ID"
