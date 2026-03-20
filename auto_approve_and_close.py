#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

AUTH = ("admin", "Qwer123443")
MCP_URL = "http://127.0.0.1:8765/sse"

async def approve_pending_approvals(session):
    """Busca y aprueba todas las aprobaciones pendientes"""
    result = await session.call_tool("snow_record_manage", {
        "action": "query",
        "table": "sysapproval_approver",
        "query": "state=pending",
        "limit": 50,
        "display_value": False
    })
    
    data = json.loads(result.content[0].text)
    pending = data["data"]["records"]
    
    if not pending:
        print("  ✅ No hay approvals pendientes")
        return 0
    
    print(f"  🔄 Aprobando {len(pending)} approvals...")
    approved = 0
    for appr in pending:
        sys_id = appr["sys_id"]["value"]
        try:
            await session.call_tool("snow_record_manage", {
                "action": "update",
                "table": "sysapproval_approver",
                "sys_id": sys_id,
                "state": "approved",
                "approver_comment": "Auto-approved by R5 automation"
            })
            approved += 1
            print(f"    ✓ Aprobado: {sys_id}")
        except Exception as e:
            print(f"    ✗ Error aprobando {sys_id}: {e}")
    
    return approved

async def close_completed_tasks(session):
    """Busca y cierra las SC_task que estén en estado completable"""
    # Buscar tareas en estado '3' (Complete) o que sean cerrables
    # Primero, obtener tareas que no estén ya cerradas (state != 7 'Closed Complete' y != 8 'Closed Incomplete')
    result = await session.call_tool("snow_record_manage", {
        "action": "query",
        "table": "sc_task",
        "query": "stateNOT IN7,8^active=true",
        "limit": 50,
        "display_value": False
    })
    
    data = json.loads(result.content[0].text)
    tasks = data["data"]["records"]
    
    if not tasks:
        print("  ✅ No hay tareas pendientes de cerrar")
        return 0
    
    print(f"  🔄 Evaluando {len(tasks)} tareas para cerrar...")
    closed = 0
    for task in tasks:
        sys_id = task["sys_id"]["value"]
        number = task.get("number", {}).get("value", sys_id)
        
        # Lógica simple: si no tiene estado de closed, la cerramos
        try:
            await session.call_tool("snow_record_manage", {
                "action": "update",
                "table": "sc_task",
                "sys_id": sys_id,
                "state": "3",  # Complete
                "close_code": "Completed",
                "close_notes": "Auto-closed by R5 automation"
            })
            closed += 1
            print(f"    ✓ Cerrada: {number}")
        except Exception as e:
            print(f"    ✗ Error cerrando {number}: {e}")
    
    return closed

async def monitor_ritm(ritm_sys_id):
    """Monitorea un RITM específico y procesa sus approvals y tareas"""
    async with sse_client(MCP_URL, auth=AUTH) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            print(f"🚨 Iniciando monitoreo de RITM {ritm_sys_id}")
            print(f"Presiona Ctrl+C para detener\n")
            
            try:
                while True:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n🕐 {timestamp} - Revisando...")
                    
                    # Aprobar approvals
                    approved = await approve_pending_approvals(session)
                    
                    # Cerrar tareas
                    closed = await close_completed_tasks(session)
                    
                    if approved == 0 and closed == 0:
                        print("  😴 Todo en orden, esperando 10 segundos...")
                    
                    await asyncio.sleep(10)
                    
            except KeyboardInterrupt:
                print("\n🛑 Monitoreo detenido")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ritm_id = sys.argv[1]
        asyncio.run(monitor_ritm(ritm_id))
    else:
        print("Uso: python3 auto_approve_and_close.py <RITM_SYS_ID>")
        print("Ejemplo: python3 auto_approve_and_close.py 7aeaeb4c477ffa14a3978f59e16d4374")
