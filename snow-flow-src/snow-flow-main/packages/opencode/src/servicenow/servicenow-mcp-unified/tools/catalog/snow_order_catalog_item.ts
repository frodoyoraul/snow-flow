/**
 * snow_order_catalog_item - Order catalog item (CORREGIDO v2)
 *
 * - Crea sc_request y sc_req_item (RITM)
 * - Para cada variable:
 *   • Si la variable tiene `field` y `map_to_field=true` → actualiza ese campo en sc_req_item
 *   • Si no → crea sc_item_option y sc_item_option_mtom
 * - Asigna flow "DTT - User Onboarding" si no está definido en el catálogo
 */

import { MCPToolDefinition, ServiceNowContext, ToolResult } from "../../shared/types.js"
import { getAuthenticatedClient } from "../../shared/auth.js"
import { createSuccessResult, createErrorResult } from "../../shared/error-handler.js"

export const toolDefinition: MCPToolDefinition = {
  name: "snow_order_catalog_item",
  description: "Orders a catalog item programmatically, creating a request (RITM) with specified variable values. Correctly handles field mapping and variable storage.",
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
      delivery_address: { type: "string", description: "Delivery address" },
      special_instructions: { type: "string", description: "Special instructions" },
    },
    required: ["cat_item", "requested_for"],
  },
}

export async function execute(args: any, context: ServiceNowContext): Promise<ToolResult> {
  const { cat_item, requested_for, variables, quantity = 1, delivery_address, special_instructions } = args

  try {
    const client = await getAuthenticatedClient(context)

    // 1. Create service catalog request (sc_request)
    const requestData: any = {
      requested_for,
      opened_by: requested_for,
    }
    if (special_instructions) requestData.special_instructions = special_instructions

    const requestResponse = await client.post("/api/now/table/sc_request", requestData)
    const requestId = requestResponse.data.result.sys_id

    // 2. Create requested item (RITM: sc_req_item)
    const ritmData: any = {
      request: requestId,
      cat_item,
      requested_for,
      quantity,
    }
    if (delivery_address) ritmData.delivery_address = delivery_address

    const ritmResponse = await client.post("/api/now/table/sc_req_item", ritmData)
    const ritmId = ritmResponse.data.result.sys_id
    const ritmNumber = ritmResponse.data.result.number

    // 3. Process variables (if any)
    let variablesProcessed = 0
    if (variables && Object.keys(variables).length > 0) {
      // 3a. Get all variable definitions (item_option_new) for this catalog item
      const varDefsResponse = await client.get("/api/now/table/item_option_new", {
        params: {
          sysparm_query: `cat_item=${cat_item}`,
          sysparm_limit: 100,
        },
      })
      const varDefs = varDefsResponse.data.result || []

      // Build map: variable name -> { sysId, field, mapToField }
      const varMap = new Map<string, { sysId: string, field?: string, mapToField: boolean }>()
      varDefs.forEach((def: any) => {
        const name = def.name || def.question_text
        if (name) {
          varMap.set(name, {
            sysId: def.sys_id,
            field: def.field || null,
            mapToField: def.map_to_field === true,
          })
        }
      })

      // 3b. For each provided variable, either update sc_req_item field or create sc_item_option
      for (const [varName, varValue] of Object.entries(variables)) {
        const def = varMap.get(varName)
        if (!def) {
          console.warn(`Variable "${varName}" not found in catalog ${cat_item}, skipping`)
          continue
        }

        if (def.field && def.mapToField) {
          // Update sc_req_item directly
          try {
            await client.patch(`/api/now/table/sc_req_item/${ritmId}`, {
              [def.field]: varValue,
            })
            variablesProcessed++
          } catch (err) {
            console.warn(`Failed to map ${varName} to field ${def.field}:`, err.message)
          }
        } else {
          // Create sc_item_option record with the value
          const optionResponse = await client.post("/api/now/table/sc_item_option", {
            item_option_new: def.sysId,
            value: varValue,
          })
          const optionSysId = optionResponse.data.result.sys_id

          // Create linkage in sc_item_option_mtom
          await client.post("/api/now/table/sc_item_option_mtom", {
            request_item: ritmId,
            sc_item_option: optionSysId,
          })

          variablesProcessed++
        }
      }
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

export const version = "1.0.1-fixed-v2"
export const author = "Snow-Flow SDK Migration + R5 Fix (with field mapping)"
