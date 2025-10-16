from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.services.progress_manager import progress_manager
import logging
import json
import asyncio
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Gestiona conexiones WebSocket"""
    
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, batch_id: str, websocket: WebSocket, connection_id: str):
        """Acepta una conexión y la registra"""
        await websocket.accept()
        
        if batch_id not in self.active_connections:
            self.active_connections[batch_id] = {}
        
        self.active_connections[batch_id][connection_id] = websocket
        await progress_manager.register_connection(batch_id, connection_id)
        logger.info(f"Conexión aceptada: batch={batch_id}, connection={connection_id}")
    
    async def disconnect(self, batch_id: str, connection_id: str):
        """Desconecta un cliente"""
        if batch_id in self.active_connections:
            self.active_connections[batch_id].pop(connection_id, None)
            if not self.active_connections[batch_id]:
                del self.active_connections[batch_id]
        
        await progress_manager.unregister_connection(batch_id, connection_id)
        logger.info(f"Desconectado: batch={batch_id}, connection={connection_id}")
    
    async def broadcast_progress(self, batch_id: str, progress_data: dict):
        """Envía actualización a todos los clientes conectados"""
        if batch_id in self.active_connections:
            disconnected = []
            
            for connection_id, websocket in self.active_connections[batch_id].items():
                try:
                    await websocket.send_json(progress_data)
                except Exception as e:
                    logger.warning(f"Error enviando a {connection_id}: {e}")
                    disconnected.append(connection_id)
            
            # Limpiar desconexiones
            for connection_id in disconnected:
                await self.disconnect(batch_id, connection_id)


# Instancia global
manager = ConnectionManager()


@router.websocket("/ws/progress/{batch_id}")
async def websocket_progress(websocket: WebSocket, batch_id: str):
    """
    WebSocket para recibir actualizaciones de progreso en tiempo real
    
    Uso:
    - Conectarse a: ws://localhost:8000/ws/progress/{batch_id}
    - Recibir actualizaciones automáticas mientras se procesa
    """
    connection_id = str(uuid.uuid4())
    
    try:
        # Aceptar conexión
        await manager.connect(batch_id, websocket, connection_id)
        
        # Enviar estado inicial
        initial_progress = progress_manager.get_progress(batch_id)
        if initial_progress:
            await websocket.send_json({
                "type": "initial",
                "data": initial_progress
            })
        
        # Loop de escucha
        while True:
            # Recibir mensaje (para mantener conexión viva)
            data = await websocket.receive_text()
            
            if data:
                try:
                    message = json.loads(data)
                    
                    # Comando: obtener estado actual
                    if message.get("command") == "get_status":
                        progress = progress_manager.get_progress(batch_id)
                        if progress:
                            await websocket.send_json({
                                "type": "status",
                                "data": progress
                            })
                    
                    # Comando: cancelar (opcional)
                    elif message.get("command") == "cancel":
                        await websocket.send_json({
                            "type": "info",
                            "message": "Cancelación no implementada aún"
                        })
                
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Mensaje inválido"
                    })
    
    except WebSocketDisconnect:
        await manager.disconnect(batch_id, connection_id)
        logger.info(f"Cliente desconectado: {connection_id}")
    
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        await manager.disconnect(batch_id, connection_id)


async def notify_progress_update(batch_id: str):
    """
    Función auxiliar para notificar actualización de progreso
    Se llama desde progress_manager cuando hay cambios
    """
    progress = progress_manager.get_progress(batch_id)
    if progress:
        await manager.broadcast_progress(batch_id, {
            "type": "progress",
            "data": progress
        })