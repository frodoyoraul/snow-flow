#!/usr/bin/env node

/**
 * SnowFlow Skill - Interfaz simplificada para Snow-Flow MCP
 * Proporciona funciones de alto nivel para operaciones ServiceNow.
 */

const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

const MCSP_SERVER = 'snow-flow';

/**
 * Ejecuta una herramienta Snow-Flow
 */
async function callTool(tool, args = {}, outputJson = true) {
  const argsStr = Object.entries(args)
    .filter(([, v]) => v !== undefined && v !== null)
    .map(([k, v]) => {
      if (Array.isArray(v)) return `${k}=${v.join(',')}`;
      if (typeof v === 'object') return `${k}='${JSON.stringify(v)}'`;
      return `${k}=${JSON.stringify(v)}`;
    })
    .join(' ');
  const cmd = `mcporter call ${MCSP_SERVER}.${tool} ${argsStr} ${outputJson ? '--output json' : ''}`;
  try {
    const { stdout, stderr } = await execPromise(cmd);
    if (stderr) console.error(stderr);
    return JSON.parse(stdout);
  } catch (error) {
    throw new Error(`Error calling ${tool}: ${error.message}\n${error.stdout || ''}\n${error.stderr || ''}`);
  }
}

/**
 * Busca y habilita herramientas
 */
async function searchTools(query, limit = 10) {
  return await callTool('tool_search', { query, limit, enable: true });
}

/**
 * Crea un registro en cualquier tabla
 * Devuelve un objeto plano con campos extraídos de display_value/value cuando aplica.
 */
async function createRecord(table, data) {
  const result = await callTool('snow_record_manage', { action: 'create', table, data });
  if (!result.success) {
    throw new Error(result.error || result?.message || 'Error creando registro');
  }
  const record = result.data?.record || result.data?.result || result;
  // Normalizar: para cada campo, si es objeto con value/display_value, usar value
  const normalized = {};
  for (const [key, val] of Object.entries(record)) {
    if (val && typeof val === 'object' && ('value' in val || 'display_value' in val)) {
      normalized[key] = val.value !== undefined ? val.value : val.display_value;
    } else {
      normalized[key] = val;
    }
  }
  return normalized;
}

/**
 * Obtiene un registro por sys_id
 */
async function getRecord(table, sysId, fields) {
  const result = await callTool('snow_record_manage', { action: 'get', table, sys_id: sysId, fields });
  if (!result.success) throw new Error(result.error || result?.message);
  return result.data?.record || result;
}

/**
 * Actualiza un registro
 */
async function updateRecord(table, sysId, data) {
  const result = await callTool('snow_record_manage', { action: 'update', table, sys_id: sysId, data });
  if (!result.success) throw new Error(result.error || result?.message);
  return result.data?.record || result;
}

/**
 * Elimina un registro
 */
async function deleteRecord(table, sysId, force = false) {
  const result = await callTool('snow_record_manage', { action: 'delete', table, sys_id: sysId, force });
  if (!result.success) throw new Error(result.error || result?.message);
  return result;
}

/**
 * Consulta registros con filtros (snow_record_manage)
 */
async function queryRecords(table, query, options = {}) {
  const args = { action: 'query', table, query, ...options };
  const result = await callTool('snow_record_manage', args);
  if (!result.success) throw new Error(result.error || result?.message);
  return result.data || result;
}

/**
 * Query directa a tabla (snow_query_table)
 * Devuelve { records, count, total, has_more } normalizado.
 */
async function queryTable(table, query, fields, limit, offset, orderBy, displayValue) {
  const result = await callTool('snow_query_table', { table, query, fields, limit, offset, order_by: orderBy, display_value: displayValue });
  // Normalizar: data.records -> records
  return {
    records: result.data?.records || result.records || [],
    count: result.data?.count || result.count || 0,
    total: result.data?.total || result.total,
    has_more: result.data?.has_more || result.has_more || false,
    truncated: result.data?.truncated || result.truncated || false,
    raw: result
  };
}

/**
 * Crea una orden de catálogo (RITM) - IMPLEMENTACIÓN CORREGIDA
 * Garantiza que los valores de variables se almacenen en sc_item_option correctamente.
 */
async function orderCatalogItem(catItemSysId, requestedFor, variables) {
  console.log(`[orderCatalogItem] cat=${catItemSysId} user=${requestedFor} vars=${Object.keys(variables||{}).length}`);
  // 1. Crear sc_request
  console.log('[orderCatalogItem] Creando sc_request...');
  const request = await createRecord('sc_request', {
    requested_for: requestedFor,
    opened_by: requestedFor
  });
  console.log('[orderCatalogItem] sc_request creado, sys_id:', request.sys_id);
  
  if (!request.sys_id) {
    throw new Error('No se pudo crear sc_request');
  }
  
  // 2. Crear sc_req_item (RITM)
  console.log('[orderCatalogItem] Creando sc_req_item...');
  const ritm = await createRecord('sc_req_item', {
    request: request.sys_id,
    cat_item: catItemSysId,
    requested_for: requestedFor,
    quantity: 1
  });
  console.log('[orderCatalogItem] sc_req_item creado, sys_id:', ritm.sys_id, 'number:', ritm.number);
  
  if (!ritm.sys_id) {
    throw new Error('No se pudo crear sc_req_item');
  }
  
  // 3. Procesar variables (si hay)
  let variablesProcessed = 0;
  if (variables && Object.keys(variables).length > 0) {
    console.log('[orderCatalogItem] Variables a procesar:', Object.keys(variables));
    // Obtener definiciones de variables (item_option_new) para este catálogo
    console.log('[orderCatalogItem] Consultando item_option_new...');
    const varDefsResult = await queryRecords(
      'item_option_new',
      `cat_item=${catItemSysId}`,
      { fields: 'sys_id,name', limit: 100 }
    );
    
    const varDefs = varDefsResult.records || [];
    console.log(`[orderCatalogItem] Variables encontradas en catálogo: ${varDefs.length}`);
    const nameToSysId = {};
    varDefs.forEach(def => {
      const name = def.name?.value || def.name?.display_value || def.name;
      const sysId = def.sys_id?.value || def.sys_id?.display_value || def.sys_id;
      if (name && sysId) nameToSysId[name] = sysId;
    });
    console.log('[orderCatalogItem] Mapa construido. Claves:', Object.keys(nameToSysId).slice(0,5));
    
    // Para cada variable proporcionada, crear sc_item_option y sc_item_option_mtom
    for (const [varName, varValue] of Object.entries(variables)) {
      console.log(`[orderCatalogItem] Procesando variable: ${varName}`);
      const itemOptionId = nameToSysId[varName];
      if (!itemOptionId) {
        console.warn(`Variable "${varName}" no encontrada en catálogo ${catItemSysId}, saltando`);
        continue;
      }
      
      console.log(`[orderCatalogItem] Creando sc_item_option para ${varName} con value="${varValue}"`);
      // Crear sc_item_option con el valor
      const option = await createRecord('sc_item_option', {
        item_option_new: itemOptionId,
        value: varValue
      });
      console.log(`[orderCatalogItem] sc_item_option creado: ${option.sys_id}`);
      
      if (!option.sys_id) {
        console.warn(`No se creó sc_item_option para ${varName}, saltando relación`);
        continue;
      }
      
      console.log(`[orderCatalogItem] Creando sc_item_option_mtom...`);
      // Crear relación en sc_item_option_mtom
      const mtom = await createRecord('sc_item_option_mtom', {
        request_item: ritm.sys_id,
        sc_item_option: option.sys_id
      });
      console.log(`[orderCatalogItem] Relación creada: ${mtom.sys_id}`);
      
      variablesProcessed++;
    }
  } else {
    console.log('[orderCatalogItem] Sin variables procesar');
  }
  
  // 4. Devolver resultado normalizado
  const ritmNumber = ritm.number?.value || ritm.number?.display_value || ritm.number;
  const ritmSysId = ritm.sys_id?.value || ritm.sys_id?.display_value || ritm.sys_id;
  const requestId = request.sys_id?.value || request.sys_id?.display_value || request.sys_id;
  
  return {
    success: true,
    ritm_number: ritmNumber,
    ritm_sys_id: ritmSysId,
    request_id: requestId,
    variables_processed: variablesProcessed
  };
}

/**
 * Obtiene detalles de un catálogo
 */
async function getCatalogItemDetails(catItemSysId, includeVariables = true) {
  return await callTool('snow_get_catalog_item_details', {
    sys_id: catItemSysId,
    include_variables: includeVariables
  });
}

/**
 * Busca catálogos
 */
async function searchCatalogItems(query, activeOnly = true, category, limit = 20) {
  return await callTool('snow_catalog_item_search', {
    query,
    active_only: activeOnly,
    category,
    limit
  });
}

/**
 * Crea un incidente
 */
async function createIncident(shortDescription, description, urgency = 2, impact = 2, callerId, assignmentGroup, assignedTo) {
  return await createRecord('incident', {
    short_description: shortDescription,
    description,
    urgency,
    impact,
    caller_id: callerId,
    assignment_group: assignmentGroup,
    assigned_to: assignedTo
  });
}

/**
 * Consulta incidentes
 */
async function queryIncidents(query, limit = 20) {
  return await queryRecords('incident', query, { limit });
}

/**
 * Obtiene los valores de variables de un RITM.
 */
async function getRITMVariableValues(ritmSysId) {
  // Paso 1: Obtener sc_item_option_mtom para este RITM
  const mtomResult = await queryRecords('sc_item_option_mtom', `request_item=${ritmSysId}`, {
    fields: 'sc_item_option',
    limit: 100
  });
  
  const mtomRecords = mtomResult.records || [];
  const optionSysIds = mtomRecords
    .map(r => r.sc_item_option?.value || r.sc_item_option)
    .filter(Boolean);
  
  if (optionSysIds.length === 0) {
    return [];
  }
  
  // Paso 2: Obtener sc_item_option por sys_id (consultas individuales)
  const allOptions = [];
  for (const sysId of optionSysIds) {
    const result = await queryRecords('sc_item_option', `sys_id=${sysId}`, {
      fields: 'item_option_new,value',
      limit: 1,
      display_value: true
    });
    if (result.records && result.records.length > 0) {
      allOptions.push(result.records[0]);
    }
  }
  
  // Paso 3: Mapear a formato amigable
  return allOptions.map(rec => ({
    variable_name: rec.item_option_new?.display_value || rec.item_option_new?.value || 'Unknown',
    value: rec.value?.display_value || rec.value?.value || '',
    item_option_sys_id: rec.sys_id
  }));
}

/**
 * Obtiene las definiciones de variables de un catálogo
 */
async function getCatalogVariableDefinitions(catItemSysId) {
  const details = await getCatalogItemDetails(catItemSysId, true);
  return details.data?.variables || [];
}

// Exportar funciones
module.exports = {
  searchTools,
  createRecord,
  getRecord,
  updateRecord,
  deleteRecord,
  queryRecords,
  queryTable,
  orderCatalogItem,
  getCatalogItemDetails,
  searchCatalogItems,
  createIncident,
  queryIncidents,
  getRITMVariableValues,
  getCatalogVariableDefinitions,
  callTool
};

// CLI
if (require.main === module) {
  const [cmd, ...args] = process.argv.slice(2);
  (async () => {
    try {
      let result;
      switch (cmd) {
        case 'order':
          const [catId, user, varsJson] = args;
          result = await orderCatalogItem(catId, user, JSON.parse(varsJson));
          break;
        case 'query':
          const [table, query, fields] = args;
          result = await queryTable(table, query, fields ? fields.split(',') : undefined);
          break;
        case 'incident':
          const [short, desc, caller] = args;
          result = await createIncident(short, desc, 2, 2, caller);
          break;
        case 'ritm-values':
          const [ritmId] = args;
          result = await getRITMVariableValues(ritmId);
          break;
        default:
          console.log(JSON.stringify({
            error: `Comando no reconocido: ${cmd}`,
            available: ['order', 'query', 'incident', 'ritm-values']
          }, null, 2));
          process.exit(1);
      }
      console.log(JSON.stringify(result, null, 2));
    } catch (error) {
      console.error(JSON.stringify({ error: error.message }, null, 2));
      process.exit(1);
    }
  })();
}
