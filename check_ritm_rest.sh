#!/bin/bash
# Verificar approvals y sc_task para el RITM más reciente de "User Onboarding"

SNOW_URL="http://127.0.0.1:3000"
USERNAME="admin"
PASSWORD="Qwer123443"
CATALOG_SYS_ID="68a7f85d472f7290a3978f59e16d43af"

echo "Buscando RITMs recientes del catálogo User Onboarding..."

# Obtener los 5 RITMs más recientes del catálogo
RITMS_JSON=$(curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/sc_req_item?sysparm_query=cat_item=${CATALOG_SYS_ID}&sysparm_fields=number,sys_id,sys_created_on&sysparm_order_by=sys_created_on_desc&sysparm_limit=5")

echo "RITMs recientes:"
echo "$RITMS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"{r['number']} (sys_id: {r['sys_id']})\") for r in data['result']]"

# Tomar el primer RITM (el más reciente)
RITM_SYS_ID=$(echo "$RITMS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result'][0]['sys_id'] if data['result'] else '')")
if [ -z "$RITM_SYS_ID" ]; then
  echo "No se encontraron RITMs"
  exit 1
fi

echo ""
echo "=========================================="
echo "Revisando RITM: $RITM_SYS_ID"
echo "=========================================="

# 1. Aprobaciones
echo ""
echo "1. Approvals (sysapproval_approver):"
APPS_JSON=$(curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/sysapproval_approver?sysparm_query=sysapproval=${RITM_SYS_ID}&sysparm_fields=state,approver,sysapproval")

APP_COUNT=$(echo "$APPS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['result']))")
echo "   Total: $APP_COUNT"

if [ "$APP_COUNT" -gt 0 ]; then
  echo "$APPS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); \
    for a in data['result']: \
      state = a.get('state', {}).get('display_value') or a.get('state'); \
      approver = a.get('approver', {}).get('display_value') or a.get('approver'); \
      print(f\"  - Approver: {approver}, Estado: {state}\")"
fi

# 2. SC Tasks
echo ""
echo "2. SC Tasks (sc_task):"
TASKS_JSON=$(curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/sc_task?sysparm_query=request_item=${RITM_SYS_ID}&sysparm_fields=number,short_description,state")

TASK_COUNT=$(echo "$TASKS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['result']))")
echo "   Total: $TASK_COUNT"

if [ "$TASK_COUNT" -gt 0 ]; then
  echo "$TASKS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); \
    for t in data['result']: \
      number = t.get('number'); \
      state = t.get('state', {}).get('display_value') or t.get('state'); \
      desc = t.get('short_description') or ''; \
      print(f\"  - {number}: {desc} (estado: {state})\")"
fi

# 3. Variables del RITM
echo ""
echo "3. Variables (item_option_new) del RITM:"
VARS_JSON=$(curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/item_option_new?sysparm_query=request_item=${RITM_SYS_ID}&sysparm_fields=name,value,type&sysparm_limit=50")

VAR_COUNT=$(echo "$VARS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['result']))")
echo "   Total: $VAR_COUNT"

if [ "$VAR_COUNT" -gt 0 ]; then
  echo "$VARS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); \
    for v in data['result']: \
      name = v.get('name') or v.get('sys_id'); \
      val = v.get('value') or ''; \
      print(f\"  - {name}: {val}\")"
fi

echo ""
echo "=========================================="
echo "Revisión completada."
