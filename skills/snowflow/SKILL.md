---
name: snowflow
description: Interfaz simplificada para Snow-Flow MCP (ServiceNow). Proporciona funciones de alto nivel para crear órdenes, incidentes, consultar datos y gestionar catálogos.
homepage: https://docs.openclaw.ai
metadata:
  {
    "openclaw": {
      "emoji": "❄️",
      "requires": { "bins": ["mcporter"], "node": ">=18" },
      "install": [
        {
          "id": "node",
          "kind": "npm",
          "package": "file://./skills/snowflow",
          "label": "Install SnowFlow skill (local)",
        },
      ],
    },
  }
---

# SnowFlow Skill

Skill que envuelve las herramientas MCP de Snow-Flow para ofrecer una interfaz más amigable y funciones de alto nivel.

## Requisitos

- `mcporter` instalado y configurado con el servidor `snow-flow`.
- Node.js >= 18

## Configuración

Asegúrate de haber configurado el servidor Snow-Flow:

```bash
mcporter config add snow-flow http://127.0.0.1:8765/sse --basic-auth admin:Qwer123443
```

## Funciones disponibles

### `orderCatalogItem(catItemSysId, requestedFor, variables)`

Crea una orden de catálogo (RITM) con las variables especificadas.

**Ejemplo:**

```javascript
const snow = require('./skills/snowflow/snowflow');

const result = await snow.orderCatalogItem(
  '68a7f85d472f7290a3978f59e16d43af', // sys_id del catálogo "User Onboarding"
  'abraham.lincoln',
  {
    first_name: 'Abraham',
    last_name: 'Lincoln',
    personal_email: 'abraham.personal@example.com',
    corporate_email: 'abraham.lincoln@example.com',
    department: 'a581ab703710200044e0bfc8bcbe5de8', // Finance
    location: '0002c0a93790200044e0bfc8bcbe5df5', // Headquarters
    job_title: 'Software Engineer',
    manager: '6816f79cc0a8016401c5a33be04be441', // admin
    start_date: '2025-05-01'
  }
);
console.log(result);
```

### `getRITMVariableValues(ritmSysId)`

Obtiene los valores de todas las variables de un RITM específico.

```javascript
const values = await snow.getRITMVariableValues('d7772494473f3e14a3978f59e16d43ed');
```

### `createIncident(shortDescription, description, options)`

Crea un incidente.

```javascript
const inc = await snow.createIncident(
  'Servidor caído',
  'El servidor web-01 no responde',
  { urgency: 1, impact: 1, callerId: 'abraham.lincoln' }
);
```

### `queryRecords(table, query, options)`

Consulta registros con filtros.

```javascript
const ritms = await snow.queryRecords('sc_req_item', 'number=RITM0010048', { limit: 1 });
```

### `queryTable(table, query, fields, options)`

Consulta directa a tabla más flexible.

```javascript
const users = await snow.queryTable('sys_user', 'active=true', ['sys_id', 'name', 'email'], 10);
```

### `getCatalogItemDetails(catItemSysId, includeVariables)`

Obtiene detalles de un catálogo, incluyendo definiciones de variables.

```javascript
const cat = await snow.getCatalogItemDetails('68a7f85d472f7290a3978f59e16d43af', true);
```

### `searchCatalogItems(query, activeOnly, category, limit)`

Busca catálogos.

```javascript
const cats = await snow.searchCatalogItems('onboarding');
```

## Uso desde CLI

La skill también se puede ejecutar como CLI:

```bash
# Crear un RITM
node skills/snowflow/snowflow.js order <cat_sys_id> <requested_for> '{"var1":"val1","var2":"val2"}'

# Consultar valores de un RITM
node skills/snowflow/snowflow.js ritm-values <ritm_sys_id>

# Crear un incidente
node skills/snowflow/snowflow.js incident "Short desc" "Long desc" [caller_username]

# Query directa
node skills/snowflow/snowflow.js query <table> <query> [fields_csv]
```

**Ejemplo CLI:**

```bash
node skills/snowflow/snowflow.js order 68a7f85d472f7290a3978f59e16d43af abraham.lincoln '{"first_name":"Abraham","last_name":"Lincoln"}'
```

## API Reference

Todas las funciones devuelven una Promise que se resuelve con la respuesta de Snow-Flow (objeto JSON).

### Funciones de catálogo

- `orderCatalogItem(catItemSysId, requestedFor, variables)` → crea RITM
- `getCatalogItemDetails(catItemSysId, includeVariables = true)`
- `searchCatalogItems(query, activeOnly = true, category = null, limit = 20)`
- `getCatalogVariableDefinitions(catItemSysId)` → helper que llama a `getCatalogItemDetails`

### Funciones de RITM

- `getRITMVariableValues(ritmSysId)` → valores de variables desde `sc_item_option`
- `queryRecords(table, query, options = {})` → usa `snow_record_manage`
- `queryTable(table, query, fields, limit, offset, orderBy, displayValue)` → usa `snow_query_table`

### Funciones de incidentes

- `createIncident(shortDescription, description, { urgency, impact, callerId, assignmentGroup, assignedTo })`
- `queryIncidents(query, limit = 20)`

### Funciones de utilidad

- `callTool(tool, args, outputJson = true)` → llamada directa a cualquier herramienta Snow-Flow
- `searchTools(query, limit = 10)` → busca y habilita herramientas

## Notas importantes

- Los campos de referencia (department, location, manager) requiren el `sys_id` del registro referenciado.
- Para obtener los `sys_id` de referencias, usar `queryTable` o `queryRecords` primero.
- El RITM se crea con todas las variables proporcionadas; si faltan obligatorias, ServiceNow puede rechazar.
- Los valores de variables se guardan en `sc_item_option` y la relación en `sc_item_option_mtom`.
- Para filtrar por RITM en `sc_item_option`, usar `request_item=<sys_id_del_ritm>` (no `item_option`).

## Ejemplo completo: Crear y verificar RITM

```javascript
const snow = require('./skills/snowflow/snowflow');

async function crearYVerificarRITM() {
  // 1. Crear la orden
  const order = await snow.orderCatalogItem(
    '68a7f85d472f7290a3978f59e16d43af',
    'abraham.lincoln',
    {
      first_name: 'Abraham',
      last_name: 'Lincoln',
      personal_email: 'abraham.personal@example.com',
      corporate_email: 'abraham.lincoln@example.com',
      department: 'a581ab703710200044e0bfc8bcbe5de8',
      location: '0002c0a93790200044e0bfc8bcbe5df5',
      job_title: 'Software Engineer',
      manager: '6816f79cc0a8016401c5a33be04be441',
      start_date: '2025-05-01'
    }
  );

  console.log('RITM creado:', order.data?.request?.number || order);

  // 2. Obtener el sc_req_item para extraer sys_id
  const ritmNumber = order.data?.request?.number || order?.number;
  if (ritmNumber) {
    const ritm = await snow.queryRecords('sc_req_item', `number=${ritmNumber}`, { fields: 'sys_id,number', limit: 1 });
    const ritmSysId = ritm.records?.[0?.sys_id;
    if (ritmSysId) {
      // 3. Obtener valores de variables
      const values = await snow.getRITMVariableValues(ritmSysId);
      console.log('Variables del RITM:', values);
    }
  }
}

crearYVerificarRITM().catch(console.error);
```

---

**Documentación generada:** 2026-03-19  
**Basado en:** Snow-Flow MCP (235+ herramientas)
