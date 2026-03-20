# ServiceNow Development — Guía de Contexto para IA

> Este documento contiene todas las normas, patrones y buenas prácticas de desarrollo en ServiceNow. Sigue estas reglas de forma estricta en cualquier código, revisión o generación de scripts para ServiceNow.

---

## REGLA ABSOLUTA: ES5 en Todo Código Server-Side

ServiceNow ejecuta JavaScript en el motor **Mozilla Rhino**, que únicamente soporta **ES5 (2009)**. Cualquier sintaxis ES6+ causará un `SyntaxError` en producción.

### Sintaxis prohibida y su alternativa ES5

| ❌ ES6+ (PROHIBIDO)         | ✅ ES5 (CORRECTO)                              |
|-----------------------------|------------------------------------------------|
| `const x = 5`               | `var x = 5`                                    |
| `let items = []`            | `var items = []`                               |
| `() => {}`                  | `function() {}`                                |
| `` `Hola ${nombre}` ``      | `'Hola ' + nombre`                             |
| `for (x of arr)`            | `for (var i = 0; i < arr.length; i++)`         |
| `{a, b} = obj`              | `var a = obj.a; var b = obj.b;`                |
| `[a, b] = arr`              | `var a = arr[0]; var b = arr[1];`              |
| `...spread`                 | `Array.prototype.slice.call(arr)`              |
| `class MyClass {}`          | Usar funciones constructoras                   |
| `async/await`               | Usar callbacks de GlideRecord                  |
| `Promise`                   | Usar GlideRecord con callbacks                 |
| `Array.from()`              | `Array.prototype.slice.call()`                 |
| `Object.assign()`           | Copiar propiedades manualmente                 |

### Ejemplos de conversión obligatoria

```javascript
// ❌ INCORRECTO
const MAX = 3;
let user = gs.getUser();
var msg = `Hola ${user}`;
var fn = () => 'done';

// ✅ CORRECTO
var MAX = 3;
var user = gs.getUser();
var msg = 'Hola ' + user;
var fn = function() { return 'done'; };
```

```javascript
// ❌ INCORRECTO - Parámetros por defecto
function process(inc, priority = 3) {}

// ✅ CORRECTO
function process(inc, priority) {
  if (typeof priority === 'undefined') { priority = 3; }
}
```

> **Excepción:** Los Client Scripts corren en el navegador y pueden soportar ES6+, pero se recomienda ES5 para máxima compatibilidad.

---

## GlideRecord — API de Base de Datos

GlideRecord es la API principal para operaciones de base de datos en ServiceNow.

### Patrones básicos

```javascript
// Obtener un registro por sys_id
var gr = new GlideRecord('incident');
if (gr.get('sys_id_aqui')) {
  gs.info('Encontrado: ' + gr.getValue('number'));
}

// Obtener por campo específico
var gr = new GlideRecord('sys_user');
if (gr.get('user_name', 'admin')) {
  gs.info('Usuario: ' + gr.getValue('name'));
}

// Consulta múltiple
var gr = new GlideRecord('incident');
gr.addQuery('active', true);
gr.addQuery('priority', '1');
gr.orderByDesc('sys_created_on');
gr.setLimit(100);
gr.query();
while (gr.next()) {
  gs.info(gr.getValue('number'));
}
```

### Queries encodeadas (más eficientes)

```javascript
var gr = new GlideRecord('incident');
gr.addEncodedQuery('active=true^priority=1^assigned_toISEMPTY');
gr.query();
while (gr.next()) {
  // procesar
}
```

### Reglas de rendimiento obligatorias

1. **Siempre usar `setLimit()`** cuando no se necesitan todos los registros.
2. **Usar `getValue()` para strings** — no acceder al campo directamente como objeto.
3. **Usar `addQuery()` antes de `query()`** — nunca iterar sin filtros en tablas grandes.
4. **Seleccionar solo campos necesarios** con `gr.addField()` cuando sea posible.
5. **Evitar queries dentro de bucles** (problema N+1 de base de datos).

```javascript
// ✅ CORRECTO - getValue() devuelve string
var number = gr.getValue('number');
var assignedTo = gr.getValue('assigned_to');

// ❌ INCORRECTO - puede devolver objeto GlideElement
var number = gr.number;
```

### Insert, Update y Delete

```javascript
// INSERT
var gr = new GlideRecord('incident');
gr.initialize();
gr.setValue('short_description', 'Error en servidor');
gr.setValue('priority', 2);
gr.setValue('caller_id', gs.getUserID());
var sysId = gr.insert();

// UPDATE
var gr = new GlideRecord('incident');
if (gr.get(sysId)) {
  gr.setValue('state', 2);
  gr.update();
}

// DELETE (usar con precaución)
var gr = new GlideRecord('incident');
gr.addQuery('active', false);
gr.addQuery('sys_created_on', '<', '2020-01-01 00:00:00');
gr.query();
while (gr.next()) {
  gr.deleteRecord();
}
```

### Aggregate queries (más eficiente que iterar)

```javascript
var agg = new GlideAggregate('incident');
agg.addQuery('active', true);
agg.addAggregate('COUNT');
agg.query();
if (agg.next()) {
  var total = agg.getAggregate('COUNT');
}
```

---

## Business Rules

Los Business Rules son scripts server-side que se ejecutan cuando los registros se muestran, insertan, actualizan o eliminan.

### Cuándo usar cada tipo

| Tipo        | Momento                        | Uso                                         | Impacto de rendimiento |
|-------------|-------------------------------|---------------------------------------------|------------------------|
| **Before**  | Antes de escribir en BD        | Validar, modificar `current`                | Bajo                   |
| **After**   | Después de escribir en BD      | Crear registros relacionados, notificaciones | Medio                  |
| **Async**   | En segundo plano (tras commit) | Procesos pesados, integraciones             | Ninguno (background)   |
| **Display** | Al cargar el formulario        | Modificar display, valores por defecto      | Bajo                   |

### Objetos disponibles en Business Rules

```javascript
current   // El registro siendo operado
previous  // El registro ANTES de los cambios (solo en update/delete)
gs        // GlideSystem — utilidades del sistema
```

### Before Business Rule — validación y modificación

```javascript
(function executeRule(current, previous) {
  // Prevenir cierre sin resolver
  if (current.state == 7 && previous.state != 6) {
    current.setAbortAction(true);
    gs.addErrorMessage('Debe resolver antes de cerrar');
  }
})(current, previous);
```

```javascript
(function executeRule(current, previous) {
  // Auto-poblar campos en nuevo registro
  if (current.isNewRecord()) {
    current.setValue('caller_id', gs.getUserID());
    current.setValue('opened_by', gs.getUserID());
  }
})(current, previous);
```

**Prohibido en Before Rules:**
- Llamar `current.update()` → causa recursión infinita
- Queries a otras tablas (mantenerlo rápido)
- Llamadas a APIs externas

### After Business Rule — registros relacionados

```javascript
(function executeRule(current, previous) {
  if (current.priority.changesTo(1)) {
    var task = new GlideRecord('task');
    task.initialize();
    task.setValue('short_description', 'Seguimiento P1: ' + current.number);
    task.setValue('parent', current.sys_id);
    task.insert();
  }
})(current, previous);
```

### Async Business Rule — procesos pesados

```javascript
(function executeRule(current, previous) {
  gs.eventQueue('incident.priority.high', current, current.assigned_to, gs.getUserID());
})(current, previous);
```

### Detección de cambios en campos

```javascript
current.priority.changes()         // Campo cambió (cualquier valor)
current.priority.changesTo(1)      // Cambió A este valor
current.priority.changesFrom(3)    // Cambió DESDE este valor
current.priority.nil()             // Campo está vacío
current.operation()                // 'insert', 'update', 'delete'
current.isNewRecord()              // True si es inserción
```

### Buenas prácticas de Business Rules

1. Usar **condiciones** para limitar cuándo se ejecuta la regla.
2. Mantener los **Before rules rápidos** — sin queries si es posible.
3. Usar **Async para integraciones** — no bloquear transacciones.
4. Evitar **Display rules** — ralentizan la carga del formulario.
5. Establecer **Order** en rango 100-500 (números menores se ejecutan primero).
6. Nunca llamar `current.update()` dentro de un Before rule.

---

## Script Includes

Los Script Includes son clases o funciones reutilizables disponibles desde cualquier script server-side.

### Patrón estándar de clase

```javascript
var MyUtility = Class.create();
MyUtility.prototype = {
  initialize: function() {
    this.log = new GSLog('my.utility', 'MyUtility');
  },

  processIncident: function(incidentId) {
    var gr = new GlideRecord('incident');
    if (!gr.get(incidentId)) {
      return { success: false, message: 'No encontrado' };
    }
    // lógica de negocio
    return { success: true, data: gr.getValue('number') };
  },

  type: 'MyUtility'
};
```

### Llamar un Script Include desde otro script

```javascript
var util = new MyUtility();
var result = util.processIncident(sysId);
if (result.success) {
  gs.info(result.data);
}
```

### Reglas para Script Includes

1. Siempre definir `type` como el nombre de la clase.
2. Usar `initialize` para la lógica del constructor.
3. Devolver objetos con `{ success: bool, data/message }` para manejo de errores.
4. Marcar como **"Client callable"** solo si se necesita desde client scripts.
5. No hardcodear valores — usar System Properties (`gs.getProperty()`).

---

## Client Scripts

Los Client Scripts se ejecutan en el navegador del usuario.

### Tipos de Client Scripts

| Tipo          | Cuándo se ejecuta                        |
|---------------|------------------------------------------|
| `onLoad`      | Al cargar el formulario                  |
| `onChange`    | Al cambiar el valor de un campo          |
| `onSubmit`    | Al guardar el formulario                 |
| `onCellEdit`  | Al editar una celda en lista             |

### Patrón onLoad

```javascript
function onLoad() {
  var state = g_form.getValue('state');
  if (state == '7') {
    g_form.setReadOnly('resolution_notes', false);
    g_form.setMandatory('resolution_notes', true);
  }
}
```

### Patrón onChange

```javascript
function onChange(control, oldValue, newValue, isLoading) {
  if (isLoading) { return; } // No ejecutar en carga inicial
  if (newValue == '1') {
    g_form.showFieldMsg('priority', 'Prioridad crítica — escalar de inmediato', 'error');
    g_form.setMandatory('escalation_notes', true);
  } else {
    g_form.hideFieldMsg('priority');
    g_form.setMandatory('escalation_notes', false);
  }
}
```

### Patrón onSubmit

```javascript
function onSubmit() {
  var priority = g_form.getValue('priority');
  var notes = g_form.getValue('work_notes');
  if (priority == '1' && !notes) {
    g_form.showFieldMsg('work_notes', 'Requerido para prioridad crítica', 'error');
    return false; // Detiene el submit
  }
  return true;
}
```

### API g_form — métodos esenciales

```javascript
g_form.getValue('field')              // Obtener valor
g_form.setValue('field', value)       // Establecer valor
g_form.setReadOnly('field', true)     // Campo de solo lectura
g_form.setMandatory('field', true)    // Campo obligatorio
g_form.setVisible('field', false)     // Mostrar/ocultar campo
g_form.showFieldMsg('field', 'msg', 'error') // Mensaje de error
g_form.hideFieldMsg('field')          // Ocultar mensaje
g_form.addDecoration('field', 'icon-star', 'tooltip') // Icono
```

### Llamadas al servidor desde Client Script (GlideAjax)

```javascript
function onLoad() {
  var ga = new GlideAjax('MyScriptInclude');
  ga.addParam('sysparm_name', 'getAssignmentGroup');
  ga.addParam('sysparm_user_id', g_form.getValue('caller_id'));
  ga.getXMLAnswer(function(answer) {
    g_form.setValue('assignment_group', answer);
  });
}
```

---

## Seguridad y ACLs

### Access Control Lists (ACLs)

```javascript
// Verificar roles en scripts
if (!gs.hasRole('itil')) {
  gs.addErrorMessage('Acceso denegado');
  current.setAbortAction(true);
}

// Verificar si el usuario puede ver un registro
var canRead = GlideRecord.canRead('incident');
var canWrite = GlideRecord.canWrite('incident');
```

### Protección contra inyección GlideRecord

```javascript
// ❌ PELIGROSO — entrada de usuario directamente en query
gr.addEncodedQuery(userInput);

// ✅ SEGURO — validar y sanitizar entrada
var safeInput = GlideStringUtil.escapeQueryTermChars(userInput);
gr.addQuery('field', safeInput);
```

### Protección contra XSS

```javascript
// ❌ PELIGROSO
gs.addInfoMessage(userInput);

// ✅ SEGURO
gs.addInfoMessage(GlideStringUtil.escapeHTML(userInput));
```

### Elevar privilegios correctamente

```javascript
// Usar solo cuando sea absolutamente necesario
var gr = new GlideRecord('incident');
gs.elevatePrivilege(true);
gr.query();
gs.elevatePrivilege(false); // SIEMPRE restaurar
```

### Reglas de seguridad obligatorias

1. **Nunca** confiar en entradas del usuario sin sanitizar.
2. **Siempre** escapar HTML al mostrar datos de usuario.
3. **Revisar roles** antes de operaciones sensibles.
4. **Usar ACLs** en lugar de lógica de negocio para control de acceso.
5. **No almacenar credenciales** en scripts — usar Connection & Credential Aliases.
6. **Evitar** `gs.elevatePrivilege()` salvo casos muy justificados.

---

## Update Sets y Ciclo de Desarrollo

### Flujo de trabajo estándar

```
1. Crear Update Set con nombre descriptivo (ej: "STORY-123: Nuevo Widget Incidentes")
2. Activar como Update Set actual antes de desarrollar
3. Desarrollar y probar en instancia DEV
4. Completar el Update Set
5. Exportar XML
6. Importar en TEST → Preview → Commit
7. Importar en PROD → Preview → Commit
```

### Nomenclatura de Update Sets

- Formato: `[TICKET]-[descripción breve]`
- Ejemplo: `INC-456-business-rule-escalacion`
- Nunca trabajar en el Update Set "Default"
- Un Update Set por feature/bug

### Reglas del Update Set

1. **Activar el Update Set** antes de cualquier cambio.
2. **Un Update Set por historia de usuario** — no mezclar funcionalidades.
3. **Documentar** en la descripción qué contiene y cómo probar.
4. **Preview antes de Commit** — revisar conflictos siempre.
5. No commitear Update Sets con errores de preview sin analizar.

---

## Revisión de Código — Checklist

Al revisar cualquier script de ServiceNow, verificar en orden:

### 1. ES5 (CRÍTICO)

- [ ] No hay `const` ni `let` → usar `var`
- [ ] No hay arrow functions `=>` → usar `function()`
- [ ] No hay template literals `` ` `` → usar concatenación
- [ ] No hay destructuring `{a, b}` → acceso explícito a propiedades
- [ ] No hay `for...of` → usar bucles con índice

### 2. Seguridad

- [ ] Entradas de usuario validadas y sanitizadas
- [ ] Sin inyección posible en queries GlideRecord
- [ ] HTML escapado antes de mostrar datos de usuario
- [ ] Roles verificados antes de operaciones sensibles
- [ ] Sin credenciales hardcodeadas

### 3. Rendimiento

- [ ] `setLimit()` usado en queries que no necesitan todos los registros
- [ ] `getValue()` usado en lugar de acceso directo al campo
- [ ] Sin queries dentro de bucles (N+1)
- [ ] Queries con filtros específicos, no sobre tablas completas
- [ ] Before rules sin queries adicionales si es posible

### 4. Patrones correctos

- [ ] Business Rules con IIFE `(function executeRule(current, previous) {...})(current, previous)`
- [ ] Script Includes con `Class.create()` y `type` definido
- [ ] Client Scripts con chequeo `if (isLoading) { return; }` en onChange
- [ ] Manejo de errores con try/catch o comprobación de `gr.get()`

### 5. Mantenibilidad

- [ ] Sin magia de números — usar constantes nombradas o System Properties
- [ ] Logging apropiado con `gs.info()`, `gs.warn()`, `gs.error()`
- [ ] Funciones pequeñas y con un único propósito
- [ ] Comentarios en lógica compleja

---

## Flow Designer (Automatización sin código)

Flow Designer es la herramienta recomendada por ServiceNow para automatización. Preferir sobre Workflows legacy.

### Cuándo usar Flow Designer vs Business Rules

| Escenario                                  | Usar                    |
|--------------------------------------------|-------------------------|
| Proceso multi-paso con aprobaciones        | Flow Designer           |
| Integración con sistemas externos          | Flow Designer + IntHub  |
| Validación de campo al guardar             | Business Rule (Before)  |
| Creación simple de registro relacionado    | Business Rule (After)   |
| Proceso pesado asíncrono                   | Business Rule (Async)   |
| Notificaciones basadas en eventos          | Flow Designer o Events  |

### Estructura de un Flow

```
Trigger → Conditions → Actions → Error Handling
```

- **Trigger:** Cuándo inicia (Record Created, Schedule, etc.)
- **Conditions:** Filtros de cuándo ejecutar
- **Actions:** Pasos de automatización (crear ticket, enviar email, etc.)
- **Error Handling:** Qué hacer si falla una acción

---

## Eventos y Notificaciones

### Publicar un evento

```javascript
// gs.eventQueue(nombre_evento, registro, param1, param2)
gs.eventQueue('incident.escalated', current, current.assigned_to, gs.getUserID());
```

### Convención de nombres de eventos

- Formato: `[scope].[tabla].[accion]`
- Ejemplo: `x_myapp.incident.escalated`
- Usar minúsculas y puntos como separador

### Desde Business Rule (Async recomendado)

```javascript
(function executeRule(current, previous) {
  if (current.priority.changesTo(1)) {
    gs.eventQueue('incident.priority.critical', current, current.number, gs.getUserID());
  }
})(current, previous);
```

---

## Scheduled Jobs

```javascript
// Script de un Scheduled Job (ES5 obligatorio)
(function runScheduledJob() {
  var gr = new GlideRecord('incident');
  gr.addQuery('active', true);
  gr.addQuery('state', 1); // New
  gr.addEncodedQuery('sys_created_onRELATIVEGE@dayofweek@ago@7');
  gr.query();

  var count = 0;
  while (gr.next()) {
    gr.setValue('state', 3); // On Hold
    gr.setValue('work_notes', 'Auto-cerrado por antigüedad — 7 días sin actividad');
    gr.update();
    count++;
  }
  gs.info('Scheduled Job: ' + count + ' incidentes actualizados');
})();
```

### Buenas prácticas de Scheduled Jobs

1. Siempre loguear inicio y fin con número de registros procesados.
2. Usar `setLimit()` para evitar timeouts en grandes volúmenes.
3. Procesar en lotes si son más de 1000 registros.
4. Usar Async Business Rules para lógica event-driven en lugar de polling.

---

## Integraciones REST

### Consumir API externa (Script Include)

```javascript
var ExternalAPIClient = Class.create();
ExternalAPIClient.prototype = {
  initialize: function(baseUrl) {
    this.baseUrl = baseUrl;
  },

  get: function(endpoint) {
    var request = new sn_ws.RESTMessageV2();
    request.setEndpoint(this.baseUrl + endpoint);
    request.setHttpMethod('GET');
    request.setRequestHeader('Content-Type', 'application/json');
    request.setRequestHeader('Accept', 'application/json');

    // Usar autenticación almacenada, nunca hardcodear
    request.setAuthenticationProfile('basic', 'my_credential_alias');

    var response = request.execute();
    var statusCode = response.getStatusCode();

    if (statusCode != 200) {
      gs.error('API Error: ' + statusCode + ' — ' + response.getBody());
      return null;
    }

    return JSON.parse(response.getBody());
  },

  type: 'ExternalAPIClient'
};
```

### Reglas de integración

1. **Nunca hardcodear URLs ni credenciales** — usar System Properties y Credential Aliases.
2. **Siempre verificar el status code** antes de parsear la respuesta.
3. **Usar async Business Rules** para integraciones que no deben bloquear el usuario.
4. **Implementar retry logic** para fallos transitorios.
5. **Loguear errores** con suficiente contexto para depuración.

---

## ATF — Automated Test Framework

```javascript
// Estructura de un test ATF
describe('Incident Priority Escalation', function() {
  it('should escalate when priority changes to 1', function() {
    var incident = createTestIncident({ priority: 3 });
    incident.setValue('priority', 1);
    incident.update();

    var updated = new GlideRecord('incident');
    updated.get(incident.sys_id);

    expect(updated.getValue('escalation')).toBe('1');
  });
});
```

### Buenas prácticas ATF

1. **Aislar tests** — cada test debe crear sus propios datos y limpiarlos.
2. **No depender del orden** de ejecución entre tests.
3. **Usar datos de prueba** identificables (prefijo "TEST-").
4. **Probar casos negativos** además de los positivos.
5. **Ejecutar ATF en DEV** antes de mover a TEST o PROD.

---

## UI Builder — Patrones

```javascript
// Data Resource en UI Builder (server-side, ES5)
(function getData(inputs, outputs) {
  var gr = new GlideRecord('incident');
  gr.addQuery('assigned_to', inputs.userId);
  gr.addQuery('active', true);
  gr.orderByDesc('priority');
  gr.setLimit(inputs.limit || 10);
  gr.query();

  var results = [];
  while (gr.next()) {
    results.push({
      sys_id: gr.getValue('sys_id'),
      number: gr.getValue('number'),
      short_description: gr.getValue('short_description'),
      priority: gr.getValue('priority'),
      state: gr.getDisplayValue('state')
    });
  }

  outputs.incidents = results;
  outputs.count = results.length;
})(inputs, outputs);
```

---

## Referencia Rápida — Objetos y APIs Clave

### GlideSystem (gs)

```javascript
gs.getUserID()              // sys_id del usuario actual
gs.getUserName()            // username del usuario actual
gs.getUser().getFullName()  // Nombre completo
gs.hasRole('admin')         // Verificar rol
gs.getProperty('prop.name') // Leer System Property
gs.info('msg')              // Log informativo
gs.warn('msg')              // Log de advertencia
gs.error('msg')             // Log de error
gs.addErrorMessage('msg')   // Mensaje de error visible al usuario
gs.addInfoMessage('msg')    // Mensaje informativo al usuario
gs.eventQueue(event, gr, p1, p2) // Publicar evento
gs.now()                    // Timestamp actual
gs.nowDateTime()            // DateTime actual como string
```

### GlideRecord — métodos de instancia

```javascript
gr.initialize()             // Preparar para insert
gr.insert()                 // Insertar y devuelve sys_id
gr.update()                 // Actualizar registro
gr.deleteRecord()           // Eliminar registro
gr.get(sysId)               // Obtener por sys_id
gr.get('field', value)      // Obtener por campo
gr.getValue('field')        // Valor como string
gr.setValue('field', val)   // Establecer valor
gr.getDisplayValue('field') // Valor display (label de choice, etc.)
gr.addQuery(field, op, val) // Añadir condición
gr.addEncodedQuery(str)     // Query encodeada
gr.addOrCondition(field, val) // Condición OR
gr.setLimit(n)              // Limitar resultados
gr.orderBy('field')         // Ordenar ascendente
gr.orderByDesc('field')     // Ordenar descendente
gr.query()                  // Ejecutar consulta
gr.next()                   // Avanzar al siguiente registro
gr.hasNext()                // Comprobar si hay más registros
gr.getRowCount()            // Número de filas (usar con precaución)
gr.isNewRecord()            // True si es inserción
gr.isValidRecord()          // True si existe el registro
gr.setAbortAction(true)     // Cancelar la operación (Before rules)
```
