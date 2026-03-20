# MEMORY.md - Conocimientos Duraderos de R5

## ServiceNow Buenas Prácticas (2026-03-18)

### Regla fundamental: ES5
- Todo código server-side debe usar ES5 (Mozilla Rhino).
- Prohibido: `const`, `let`, `=>`, template literals, destructuring, spread, async/await, Promise.
- Usar `var`, `function()`, concatenación de strings.

### GlideRecord
- `setLimit()` siempre que no necesites todos los registros.
- `getValue()` para obtener strings; no usar acceso directo `gr.field`.
- Evitar queries dentro de bucles (problema N+1).
- Usar `addEncodedQuery()` para queries complejas más eficientes.
- `insert()`, `update()`, `deleteRecord()`.

### Business Rules
- **Before**: validar/modificar `current`, rápido, sin queries ni APIs externas. No llamar `current.update()`.
- **After**: crear registros relacionados, notificaciones.
- **Async**: procesos pesados, integraciones, eventos.
- **Display**: evitar, ralentiza carga.
- Usar condiciones para limitar ejecución.
- Orden 100-500 (menor = antes).

### Script Includes
- Patrón `Class.create()` con `type: 'Nombre'`.
- `initialize` como constructor.
- Devolver `{ success: bool, data/message }`.
- No hardcodear valores; usar `gs.getProperty()`.

### Client Scripts
- Tipos: onLoad, onChange, onSubmit, onCellEdit.
- `if (isLoading) return;` en onChange.
- API `g_form` para manipular formulario.
- Llamadas servidor con `GlideAjax`.

### Seguridad
- Sanitizar entradas de usuario (`GlideStringUtil.escapeQueryTermChars`).
- Escapar HTML (`GlideStringUtil.escapeHTML`) antes de mostrar datos de usuario.
- Verificar roles (`gs.hasRole()`).
- No almacenar credenciales en scripts; usar Credential Aliases.
- Minimizar `gs.elevatePrivilege()`.

### Update Sets
- Un feature/bug por Update Set.
- Nomenclatura: `[TICKET]-descripción-breve`.
- Nunca trabajar en "Default".
- Preview antes de Commit.
- Documentar cambios.

### Flow Designer vs Business Rules
- Flow Designer: procesos multi-paso, aprobaciones, integraciones complejas.
- Business Rules: validaciones simples, creación de registros relacionados, notificaciones event-driven.

### Integraciones REST
- Nunca hardcodear URLs/credenciales.
- Usar System Properties y Credential Aliases.
- Verificar `statusCode` antes de parsear.
- Usar Business Rules Async para no bloquear usuario.
- Implementar retry logic.

### Scheduled Jobs
- Loguear inicio y fin con número de registros procesados.
- Usar `setLimit()` para evitar timeouts.
- Procesar en lotes si >1000 registros.
- Preferir Async Business Rules sobre polling.

### ATF
- Tests aislados, cada test crea y limpia sus datos.
- No depender del orden de ejecución.
- Usar prefijo "TEST-" en datos de prueba.
- Probar casos negativos.

### UI Builder
- Data Resource: función `(function(inputs, outputs){...})(inputs, outputs)`.
- Usar `outputs` para devolver resultados.
- Mantener lógica server-side ES5.

### Referencia Rápida
- `gs.getUserID()`, `gs.hasRole()`, `gs.getProperty()`, `gs.info()`, `gs.error()`, `gs.eventQueue()`.
- `gr.getValue('field')`, `gr.setValue('field', val)`, `gr.addQuery()`, `gr.addEncodedQuery()`, `gr.setLimit()`, `gr.query()`, `gr.next()`.
- `g_form.getValue()`, `g_form.setValue()`, `g_form.setReadOnly()`, `g_form.setMandatory()`, `g_form.showFieldMsg()`.

---

## Notas adicionales
- ServiceNow ejecuta JavaScript ES5 únicamente en server-side. Cualquier sintaxis moderna romperá en producción.
- Priorizar rendimiento: evitar queries innecesarias, usar límites, agregados.
- Seguridad primero: nunca confiar en entradas de usuario, siempre escapar.

## Órdenes de Catálogo (2026-03-19)
- Catálogo "User Onboarding": sys_id `68a7f85d472f7290a3978f59e16d43af`
- Herramienta MCP: `snow_order_catalog_item` (crea RITM con variables)
- Variables obligatorias del catálogo:
  - `personal_email` (email)
  - `location` (reference cmn_location) → Headquarters: `0002c0a93790200044e0bfc8bcbe5df5`
  - `job_title` (string)
  - `manager` (reference sys_user) → admin: `6816f79cc0a8016401c5a33be04be441`
  - `last_name` (string)
  - `corporate_email` (email)
  - `department` (reference cmn_department) → Finance: `a581ab703710200044e0bfc8bcbe5de8`
  - `first_name` (string)
  - `start_date` (date, formato YYYY-MM-DD)
- Flujo asociado: "DTT - User Onboarding" (sys_id: `3398a4f39303b610b4ecfa95dd03d6ba`)
- Ejemplo de orden exitosa: RITM0010048 para abraham.lincoln con todas las variables completas.

## Snow-Flow MCP (2026-03-19)
- **Configuración:** `mcporter config add snow-flow http://127.0.0.1:8765/sse --basic-auth admin:Qwer123443`
- **Herramienta principal:** `snow_record_manage` (CRUD para todas las tablas)
- **Consulta:** `snow_query_table` (filtros, paginación, campos)
- **Catálogo:** `snow_order_catalog_item`, `snow_get_catalog_item_details`, `snow_catalog_item_search`
- **Discovery:** `tool_search` para encontrar herramientas (235+ disponibles)
- **Documentación completa:** `/home/openclaw/.openclaw/workspace/docs/snow-flow/SNOW-FLOW-MCP-GUIDE.md`
- **Skill personalizada:** `snowflow` (wrapper JavaScript) en `/home/openclaw/.openclaw/workspace/skills/snowflow/`
  - Uso como módulo: `const snow = require('./skills/snowflow/snowflow');`
  - Uso CLI: `snowflow-cli order <cat_id> <user> '{"vars":...}'`
  - Funciones: `orderCatalogItem`, `getRITMVariableValues`, `createIncident`, `queryRecords`, `queryTable`, etc.

### Relaciones de Service Catalog
- `sc_req` → solicitud principal
- `sc_req_item` (RITM) → ítem, referencia a `sc_cat_item`
- `item_option_new` → definición de variables del catálogo
- `sc_item_option_mtom` → vincula RITM con definiciones de variables
- `sc_item_option` → **valores** de variables para un RITM específico

**Nota crítica:** Para obtener los valores de variables de un RITM, filtrar `sc_item_option` por `request_item=<sys_id_del_ritm>`, no por `item_option`. La tabla `sc_item_option_mtom` muestra la relación RITM→definición, pero los valores están en `sc_item_option`.

### Consulta de valores de un RITM
```bash
# 1. Obtener sc_req_item
mcporter call snow-flow.snow_record_manage action="query" table="sc_req_item" query="number=RITM0010048" fields="sys_id" --output json

# 2. Obtener valores (directo desde sc_item_option)
mcporter call snow-flow.snow_query_table table="sc_item_option" query="request_item=<sys_id>" fields="name,value" --output json
```
