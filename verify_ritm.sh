#!/bin/bash
# Verificar RITM, variables, approvals y sc_task

SNOW_URL="http://127.0.0.1:3000"
USERNAME="admin"
PASSWORD="Qwer123443"
CATALOG_SYS_ID="68a7f85d472f7290a3978f59e16d43af"

echo "=== Verificación de RITM y datos asociados ==="
echo ""

# 1. Obtener los 3 RITMs más recientes del catálogo
echo "1. RITMs recientes del catálogo User Onboarding:"
RITMS_JSON=$(curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/sc_req_item?sysparm_query=cat_item=${CATALOG_SYS_ID}&sysparm_fields=number,sys_id,sys_created_on&sysparm_order_by=sys_created_on_desc&sysparm_limit=3")

echo "$RITMS_JSON" | python3 -m json.tool 2>/dev/null || echo "$RITMS_JSON"

# Tomar el más reciente
RITM_SYS_ID=$(echo "$RITMS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['sys_id'] if data.get('result') else '')")
RITM_NUMBER=$(echo "$RITMS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['number'] if data.get('result') else '')")

if [ -z "$RITM_SYS_ID" ]; then
  echo "No se encontraron RITMs. Terminando."
  exit 1
fi

echo ""
echo "=========================================="
echo "RITM seleccionado: $RITM_NUMBER (sys_id: $RITM_SYS_ID)"
echo "=========================================="

# 2. Variables del RITM
echo ""
echo "2. Variables (item_option_new):"
curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/item_option_new?sysparm_query=request_item=${RITM_SYS_ID}&sysparm_fields=name,value,type&sysparm_limit=50" | python3 -m json.tool 2>/dev/null | head -60

# 3. Approvals
echo ""
echo "3. Approvals (sysapproval_approver):"
curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/sysapproval_approver?sysparm_query=sysapproval=${RITM_SYS_ID}&sysparm_fields=state,approver" | python3 -m json.tool 2>/dev/null

# 4. SC Tasks
echo ""
echo "4. SC Tasks (sc_task):"
curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/sc_task?sysparm_query=request_item=${RITM_SYS_ID}&sysparm_fields=number,state,short_description" | python3 -m json.tool 2>/dev/null

echo ""
echo "=== Fin de verificación ==="
