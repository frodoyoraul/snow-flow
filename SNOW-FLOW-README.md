# Snow-Flow - Guías y Skill

Esta carpeta contiene toda la documentación y skill personalizada para trabajar con ServiceNow a través del MCP Snow-Flow.

## Contenido

- `docs/snow-flow/SNOW-FLOW-MCP-GUIDE.md` - Guía completa de referencia (235+ herramientas)
- `skills/snowflow/` - Skill personalizada que envuelve Snow-Flow MCP
  - `SKILL.md` - Documentación de la skill
  - `snowflow.js` - Implementación modular + CLI

## Configuración rápida

```bash
# Configurar el MCP Snow-Flow (una vez)
mcporter config add snow-flow http://127.0.0.1:8765/sse --basic-auth admin:Qwer123443
```

## Usar la skill

### Como módulo Node.js

```javascript
const snow = require('./skills/snowflow/snowflow');

// Crear un RITM
const order = await snow.orderCatalogItem(
  '68a7f85d472f7290a3978f59e16d43af', // catálogo
  'usuario',
  { first_name: 'Juan', last_name: 'Perez', ... }
);
```

### Desde CLI

```bash
# Crear un incidente
snowflow-cli incident "Servidor caído" "Descripción" abraham.lincoln

# Consultar valores de un RITM
snowflow-cli ritm-values <sys_id_del_ritm>

# Query directa
snowflow-cli query sc_req_item "number=RITM0010048" "sys_id,number,cat_item"
```

## Recorrido de tablas de catálogo

- `sc_req` → solicitud principal
- `sc_req_item` (RITM) → ítem, referencia a `sc_cat_item`
- `item_option_new` → definición de variables del catálogo
- `sc_item_option_mtom` → vincula RITM con definiciones
- `sc_item_option` → **valores** de variables para ese RITM (filtrar por `request_item`)

## Véase también

- Guía completa: `docs/snow-flow/SNOW-FLOW-MCP-GUIDE.md`
- OpenClaw docs: https://docs.openclaw.ai
- Snow-Flow MCP: https://github.com/openclaw/snow-flow
