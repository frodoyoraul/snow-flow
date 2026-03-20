#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

AUTH = ("admin", "Qwer123443")
MCP_URL = "http://127.0.0.1:8765/sse"

def extract_value(field):
    """Extrae el valor real de un campo, maneje display_value o valor directo."""
    if not field:
        return None
    if isinstance(field, dict):
        return field.get("display_value") or field.get("value")
    return field

async def approve_pending_approvals(session):
    """Busca y aprueba todas las aprobaciones pendientes"""
    result = await session.call_tool("snow_record_manage", {
        "action": "query",
        "table": "sysapproval_approver",
        "query": "state=pending",
        "limit": 50,
        "display_value": False  # valores crudos
    })
    
    data = json.loads(result.content[0].text)
    pending = data["data"]["records"]
    
    if not pending:
        return 0
    
    approved = 0
    for appr in pending:
        sys_id = extract_value(appr.get("sys_id"))
        if not sys_id:
            continue
        try:
            await session.call_tool("snow_record_manage", {
                "action": "update",
                "table": "sysapproval_approver",
                "sys_id": sys_id,
                "state": "approved",
                "approver_comment": "Auto-approved by R5 automation"
            })
            approved += 1
            print(f"    ✓ Aprobado approval {sys_id}")
        except Exception as e:
            print(f"    ✗ Error aprobando {sys_id}: {e}")
    
    return approved

async def close_completed_tasks(session):
    """Busca y cierra las SC_task que estén en estado completable"""
    # Buscar tareas activas que no estén cerradas (state != 7 y != 8)
    result = await session.call_tool("snow_record_manage", {
        "action": "query",
        "table": "sc_task",
        "query": "active=true^stateNOT IN7,8",
        "limit": 50,
        "display_value": False
    })
    
    data = json.loads(result.content[0].text)
    tasks = data["data"]["records"]
    
    if not tasks:
        return 0
    
    closed = 0
    for task in tasks:
        sys_id = extract_value(task.get("sys_id"))
        number = extract_value(task.get("number")) or sys_id
        if not sys_id:
            continue
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
            print(f"    ✓ Cerrada tarea {number}")
        except Exception as e:
            print(f"    ✗ Error cerrando {number}: {e}")
    
    return closed

async def monitor_ritm(ritm_sys_id=None):
    """Monitorea approvals y tareas en todo el sistema"""
    async with sse_client(MCP_URL, auth=AUTH) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            print(f"🚨 Iniciando monitor automático (RITM filter: {ritm_sys_id or 'None'})")
            print(f"Presiona Ctrl+C para detener\n")
            
            try:
                while True:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n🕐 {timestamp} - Revisando...")
                    
                    # Aprobar approvals pendientes (global)
                    approved = await approve_pending_approvals(session)
                    
                    # Cerrar tareas completadas (global)
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
        asyncio.run(monitor_ritm())
