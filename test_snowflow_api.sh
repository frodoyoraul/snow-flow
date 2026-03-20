#!/bin/bash
# Test de la API REST de Snow-Flow

SNOW_URL="http://127.0.0.1:3000"
USERNAME="admin"
PASSWORD="Qwer123443"

echo "Probando conexión a Snow-Flow en ${SNOW_URL}..."
echo ""

# 1. Probar endpoint simple: /api/now/table/sys_user
echo "1. GET /api/now/table/sys_user?sysparm_limit=1"
curl -v -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/sys_user?sysparm_limit=1" 2>&1 | head -40

echo ""
echo "=========================================="
echo ""

# 2. Probar con usuario Abraham
echo "2. GET /api/now/table/sys_user?sysparm_query=user_name=abraham.lincoln"
curl -s -u "${USERNAME}:${PASSWORD}" \
  "${SNOW_URL}/api/now/table/sys_user?sysparm_query=user_name=abraham.lincoln&sysparm_fields=sys_id,user_name" | python3 -m json.tool 2>/dev/null || echo "Error en la respuesta"
