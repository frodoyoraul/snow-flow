# Snow-Flow MCP - Guía de Referencia Completa

## Introducción

Snow-Flow es un conector MCP que proporciona acceso a ServiceNow a través de 235+ herramientas. Esta guía文档 todas las herramientas disponibles y cómo usarlas.

## Configuración

```bash
mcporter config add snow-flow http://127.0.0.1:8765/sse --basic-auth admin:Qwer123443
```

## Herramientas Principales

### 1. `snow_record_manage` (PRIMARIA)

**Descripción:** Herramienta principal para TODAS las operaciones CRUD en ServiceNow.

**Acciones:** `create`, `get`, `update`, `delete`, `query`

**Tablas soportadas (nombres amigables):**
- ITSM: `incident`, `problem`, `change`, `change_request`, `change_task`, `request`, `task`
- CMDB: `ci`, `server`, `computer`, `ci_relationship`
- Users: `user`, `group`, `group_member`
- Assets: `asset`, `hardware_asset`, `software_license`
- HR/CSM: `hr_case`, `hr_task`, `customer_case`, `customer_account`
- Projects: `project`, `project_task`
- Other: `purchase_order`, `knowledge_article`
- Y muchas más...

**Parámetros comunes:**
- `action`: create | get | update | delete | query
- `table`: nombre de tabla opreset
- `sys_id`: para get/update/delete
- `number`: para get por número (INC0010001, etc.)
- `data`: objeto con campos para create/update

**Parámetros específicos por tabla:**

**Incident:**
- `short_description`, `description`, `caller_id`
- `urgency`: 1=High, 2=Medium, 3=Low
- `impact`: 1=High, 2=Medium, 3=Low
- `priority`: 1-5
- `category`, `subcategory`
- `assignment_group`, `assigned_to`
- `configuration_item`
- `work_notes`, `comments`
- `state`: 1=New, 2=InProgress, 3=OnHold, 6=Resolved, 7=Closed
- `auto_assign`: boolean

**Change:**
- `type`, `risk`: 1-4
- `start_date`, `end_date`: YYYY-MM-DD HH:mm:ss
- `justification`, `implementation_plan`, `backout_pl
- `test_plan`, `cab_required`

**User:**
- `user_name`, `first_name`, `last_name`, `email`
- `active`, `department`, `location`, `manager`, `title`, `phone`

**CI/Asset:**
- `ip_address`, `mac_address`, `os`, `os_version`
- `operational_status`: 1-4
- `install_status`: 1,2,3,6,7
- `support_group`, `manufacturer`, `model_id`
- `serial_number`, `cpu_count`, `ram`, `disk_space`
- `parent`, `child`, `relationship_type`

**Ejemplos:**

```bash
# Crear incidente
mcporter call snow-flow.snow_record_manage action="create" table="incident" short_description="Test" urgency=2

# Consultar incidentes
mcporter call snow-flow.snow_record_manage action="query" table="incident" query="state=1^priority=1" limit=10

# Obtener por número
mcporter call snow-flow.snow_record_manage action="get" table="incident" number="INC0010001"

# Actualizar
mcporter call snow-flow.snow_record_manage action="update" table="incident" sys_id="..." state=6
```

### 2. `snow_query_table`

**Descripción:** Consulta cualquier tabla con filtros, paginación y selección de campos.

**Parámetros:**
- `table`: nombre de tabla
- `query`: query codificada (ej: `active=true^priority=1`)
- `fields`: array de campos o string separado por comas
- `limit`, `offset`
- `order_by`: campo (prefijo `-` para descendente)
- `display_value`: devolver display values en lugar de sys_ids
- `truncate_output`: truncar campos grandes

**Ejemplo:**

```bash
mcporter call snow-flow.snow_query_table table="sc_req_item" query="number=RITM0010048" fields="sys_id,number,cat_item,request" --output json
```

### 3. `snow_order_catalog_item`

**Descripción:** Crea una orden de catálogo (RITM) con variables.

**Parámetros:**
- `cat_item`: sys_id del catálogo
- `requested_for`: username o sys_id del usuario
- `variables`: objeto JSON con pares clave-valor de las variables del catálogo

**Ejemplo:**

```bash
mcporter call snow-flow.snow_order_catalog_item cat_item="68a7f85d472f7290a3978f59e16d43af" requested_for="abraham.lincoln" variables='{"first_name":"Abraham","last_name":"Lincoln","corporate_email":"abraham.lincoln@example.com","personal_email":"abraham.personal@example.com","department":"a581ab703710200044e0bfc8bcbe5de8","location":"0002c0a93790200044e0bfc8bcbe5df5","job_title":"Software Engineer","manager":"6816f79cc0a8016401c5a33be04be441","start_date":"2025-05-01"}' --output json
```

### 4. `snow_get_catalog_item_details`

**Descripción:** Obtiene detalles de un catálogo, incluyendo variables.

**Parámetros:**
- `sys_id`: sys_id del catálogo
- `include_variables`: true/false

**Ejemplo:**

```bash
mcporter call snow-flow.snow_get_catalog_item_details sys_id="68a7f85d472f7290a3978f59e16d43af" include_variables=true --output json
```

### 5. `snow_catalog_item_search`

**Descripción:** Busca catálogos.

**Parámetros:**
- `query`: texto a buscar
- `active_only`: true/false
- `category`: sys_id de categoría
- `limit`

### 6. `tool_search`

**Descripción:** Busca herramientas disponibles y las habilita para la sesión.

**Parámetros:**
- `query`: términos de búsqueda
- `limit`: máximo resultados
- `enable`: habilitar herramientas encontradas

**Flujo de trabajo:**

1. Buscar herramientas: `tool_search({query: "incident", limit: 10})`
2. Las herramientas se habilitan automáticamente.
3. Ejecutar: `tool_execute({tool: "snow_query_incidents", args: {state:1}})` o usar los nombres directos.

### 7. Otras herramientas útiles

- `snow_discover_table_fields`: descubre esquema de tabla
- `snow_get_by_sysid`: obtiene registro por sys_id
- `snow_create_business_rule`, `snow_disable_business_rule`
- `snow_create_workflow`, `snow_workflow_manage`
- `snow_send_email`
- `snow_get_logs`, `snow_trace_execution`
- `snow_impact_analysis`, `snow_get_ci_impact`
- `snow_create_ci`, `snow_update_ci`
- `snow_asset_*`, `snow_user_manage`, `snow_group_manage`

## Relaciones de Tablas en Service Catalog

Cuando se crea una orden de catálogo:

1. **sc_req** (request): registro principal de la solicitud
2. **sc_req_item** (RITM): registro ítem, referencia a `sc_cat_item`
3. **item_option_new**: definición de variables del catálogo (no valores)
4. **sc_item_option_mtom**: tabla intermedia que vincula `sc_req_item` con `item_option_new` (la definición)
5. **sc_item_option**: valores reales de las variables para esa orden específica

Para consultar los valores de una orden:

```bash
# 1. Obtener el sc_req_item
mcporter call snow-flow.snow_record_manage action="get" table="sc_req_item" number="RITM0010048" fields="sys_id,cat_item,request" --output json

# 2. Obtener sc_item_option_mtom para ese sc_req_item
mcporter call snow-flow.snow_record_manage action="query" table="sc_item_option_mtom" query="request_item=<sys_id_del_ritm>" fields="sys_id,item_option" --output json

# 3. Para cada item_option, obtener el valor desde sc_item_option
# (o hacer join consultando sc_item_option donde request_item=<sys_id_ritm>)
```

**Filtro correcto para sc_item_option_mtom:**
- Por `request_item` (sys_id del sc_req_item)

**Filtro para sc_item_option:**
- Directamente por `request_item` (sys_id del sc_req_item) NO por item_option.
- Ejemplo: `query="request_item=d7772494473f3e14a3978f59e16d43ed"`

## Consejos y Mejores Prácticas

1. **Usar `snow_record_manage` como principal**: cubre la mayoría de casos.
2. **Para consultas complejas**, usar `snow_query_table` es más directo.
3. **Siempre incluir `fields`** para limitar datos y mejorar performance.
4. **Usar `display_value=true`** cuando se necesiten nombres en lugar de sys_ids.
5. **Paginación**: usar `limit` y `offset` en tablas grandes.
6. **Orden**: `order_by="-sys_created_on"` para más recientes primero.
7. **Catálogos**: antes de ordenar, usar `snow_get_catalog_item_details` para ver variables requeridas.
8. **Variables de catálogo**: pasar todas las obligatorias en el JSON de `variables`.
9. **Referencias**: para campos reference, usar sys_id. Si se tiene solo el nombre,consultar first.
10. **Fechas**: formato `YYYY-MM-DD HH:mm:ss` (24h).

## Ejemplos Completos

### Crear y consultar un RITM

```bash
# Paso 1: Obtener detalles del catálogo
mcporter call snow-flow.snow_get_catalog_item_details sys_id="68a7f85d472f7290a3978f59e16d43af" include_variables=true

# Paso 2: Crear la orden
mcporter call snow-flow.snow_order_catalog_item cat_item="68a7f85d472f7290a3978f59e16d43af" requested_for="abraham.lincoln" variables='{"first_name":"Abraham","last_name":"Lincoln","personal_email":"abraham.personal@example.com","corporate_email":"abraham.lincoln@example.com","department":"a581ab703710200044e0bfc8bcbe5de8","location":"0002c0a93790200044e0bfc8bcbe5df5","job_title":"Software Engineer","manager":"6816f79cc0a8016401c5a33be04be441","start_date":"2025-05-01"}' --output json

# Paso 3: Consultar el RITM creado (obtener sys_id)
mcporter call snow-flow.snow_record_manage action="query" table="sc_req_item" query="number=RITM0010048" fields="sys_id,number,cat_item,request" --output json

# Paso 4: Ver valores de variables (sc_item_option)
mcporter call snow-flow.snow_query_table table="sc_item_option" query="request_item=<sys_id_ritm>" fields="name,value" --output json
```

### Crear un incidente

```bash
mcporter call snow-flow.snow_record_manage action="create" table="incident" short_description="Mi servidor no responde" description="El servidor web-01 no está respondiendo a ping" urgency=1 impact=1 caller_id="abraham.lincoln" --output json
```

### Consultar CIs por ubicación

```bash
mcporter call snow-flow.snow_query_table table="cmn_location" query="name=Headquarters" fields="sys_id,name" --output json
# Luego usar el sys_id en ci query
mcporter call snow-flow.snow_query_table table="ci" query="location=<sys_id>" fields="sys_id,name,ip_address" limit=20 --output json
```

## Notas sobre la API MCP

- Todas las herramientas están bajo el namespace `snow-flow`.
- Se puede llamar directamente con `mcporter call snow-flow.<tool_name>`.
- `tool_search` habilita herramientas dinámicamente.
- Respuestas en JSON con `--output json`.
- Para tablas grandes, resultados se truncan; usar `offset` para paginar.

## Apéndice: Todas las Categorías de Herramientas

- **Catalog**: Gestión de catálogo, variables, ítems
- **Incident**: Análisis, resolución automática, métricas
- **Change**: Gestión de cambios, sprints ágiles, implementación
- **CMDB**: Discovery,Health, relaciones, impacto
- **User**: Gestión de usuarios, grupos, notificaciones, roles
- **Asset**: Compliance, discovery, licencias, ciclo de vida
- **Business Rules**: Creación y gestión de reglas de negocio
- **Service Portfolio**: (vacío en versión actual)
- **Project**: Gestión de proyectos
- **Knowledge**: Artículos, bases de conocimiento
- **HR**: Casos HR, onboarding, amenazas
- **CSM**: Casos de cliente
- **Security**: Políticas, compliance, escaneo, playbooks
- **Reporting**: Dashboards, reports, KPIs
- **Automation**: Jobs programados, eventos, flujos, logs
- **Deployment**: DevOps, GitHub, validación, rollback
- **Connectors**: Conexiones, salud, batch requests

---

**Última actualización:** 2026-03-19
**Versión Snow-Flow MCP:** 1.0
