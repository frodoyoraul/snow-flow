/**
 * snow_order_catalog_item - Order catalog item
 *
 * Estrategia:
 *   1. Obtener definiciones de variables del catálogo
 *   2. Crear sc_request + sc_req_item
 *   3. Crear TODAS las variables en paralelo (Promise.all) para minimizar
 *      la ventana entre la creación del RITM y el arranque del flow
 */

import { MCPToolDefinition, ServiceNowContext, ToolResult } from "../../shared/types.js"
import { getAuthenticatedClient } from "../../shared/auth.js"
import { createSuccessResult, createErrorResult } from "../../shared/error-handler.js"

export const toolDefinition: MCPToolDefinition = {
  name: "snow_order_catalog_item",
  description: "Orders a catalog item programmatically, creating a request (RITM) with specified variable values.",
  category: "itsm",
  subcategory: "service-catalog",
  use_cases: ["ordering", "automation", "ritm"],
  complexity: "intermediate",
  frequency: "high",
  permission: "write",
  allowedRoles: ["developer", "admin"],
  inputSchema: {
    type: "object",
    properties: {
      cat_item: { type: "string", description: "Catalog item sys_id" },
      requested_for: { type: "string", description: "User sys_id or username" },
      variables: { type: "object", description: "Variable name-value pairs" },
      quantity: { type: "number", description: "Quantity to order", default: 1 },
    },
    required: ["cat_item", "requested_for"],
  },
}

export async function execute(args: any, context: ServiceNowContext): Promise<ToolResult> {
  const { cat_item, requested_for, variables = {}, quantity = 1 } = args

  try {
    const client = await getAuthenticatedClient(context)

    // 1. Obtener definiciones de variables ANTES de crear el RITM
    const varDefsResponse = await client.get("/api/now/table/item_option_new", {
      params: {
        sysparm_query: `cat_item=${cat_item}`,
        sysparm_fields: "sys_id,name",
        sysparm_limit: 100,
      },
    })
    const varDefs = varDefsResponse.data.result || []
    const varMap = new Map<string, string>() // name -> sys_id
    varDefs.forEach((def: any) => {
      if (def.name) varMap.set(def.name, def.sys_id)
    })

    // 2. Crear sc_request
    const requestResponse = await client.post("/api/now/table/sc_request", {
      requested_for,
      opened_by: requested_for,
    })
    const requestId = requestResponse.data.result.sys_id

    // 3. Crear sc_req_item (RITM) — el flow arranca aquí
    const ritmResponse = await client.post("/api/now/table/sc_req_item", {
      request: requestId,
      cat_item,
      requested_for,
      quantity,
    })
    const ritmId = ritmResponse.data.result.sys_id
    const ritmNumber = ritmResponse.data.result.number

    // 4. Crear TODAS las variables en paralelo para minimizar la ventana temporal
    let variablesProcessed = 0
    if (Object.keys(variables).length > 0) {
      const varEntries = Object.entries(variables).filter(([name]) => varMap.has(name))
      const skipped = Object.keys(variables).filter(name => !varMap.has(name))
      if (skipped.length > 0) {
        console.warn(`Variables no encontradas en catálogo: ${skipped.join(', ')}`)
      }

      await Promise.all(
        varEntries.map(async ([varName, varValue]) => {
          const defSysId = varMap.get(varName)!
          // Crear sc_item_option
          const optResp = await client.post("/api/now/table/sc_item_option", {
            item_option_new: defSysId,
            value: varValue,
          })
          const optionSysId = optResp.data.result.sys_id
          // Vincular al RITM
          await client.post("/api/now/table/sc_item_option_mtom", {
            request_item: ritmId,
            sc_item_option: optionSysId,
          })
        })
      )
      variablesProcessed = varEntries.length
    }

    return createSuccessResult(
      {
        ordered: true,
        request_id: requestId,
        ritm_id: ritmId,
        ritm_number: ritmNumber,
        quantity,
        variables_processed: variablesProcessed,
      },
      {
        operation: "order_catalog_item",
        item: cat_item,
        requested_for,
      },
    )
  } catch (error: any) {
    return createErrorResult(error.message)
  }
}

export const version = "3.0.0-parallel-vars"
export const author = "R5 - parallel variable creation"
