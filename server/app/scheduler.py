from datetime import datetime
from app.database import get_connection

async def verificar_y_emitir_pausas(sio_server):
    """
    Tarea periódica ejecutada por APScheduler.
    Busca pausas programadas para el minuto actual y emite las alertas vía WebSockets.
    """
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM pausas_activas WHERE fecha_hora = ? AND completada = 0",
        (ahora,)
    )
    pausas_pendientes = cursor.fetchall()

    for pausa in pausas_pendientes:
        payload = {
            "id": pausa["id"],
            "area": pausa["area_nombre"],
            "mensaje": pausa["mensaje"],
            "color_fondo": pausa["color_fondo"],
            "imagen_path": pausa["imagen_path"]
        }
        
        print(f" [ ALERTA EMITIDA ] Pausa ID #{pausa['id']} para el área: {pausa['area_nombre']}")
        
        # Enviar alerta a todos los clientes conectados a la red local
        await sio_server.emit("alerta_pausa", payload)
        
        # Marcar la pausa como emitida
        cursor.execute("UPDATE pausas_activas SET completada = 1 WHERE id = ?", (pausa["id"],))
        conn.commit()

    conn.close()