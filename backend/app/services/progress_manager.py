from typing import Dict, Set
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class ProgressManager:
    """
    Gestiona el progreso de cargues en memoria
    Mantiene el estado de cada batch y notifica a clientes conectados
    """
    
    def __init__(self):
        self.progress: Dict[str, dict] = {}
        self.websocket_connections: Dict[str, Set] = {}
        self.lock = asyncio.Lock()
    
    async def init_batch(self, batch_id: str, total: int):
        """Inicializa tracking de un batch"""
        async with self.lock:
            self.progress[batch_id] = {
                "total": total,
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "status": "processing",
                "start_time": datetime.now(),
                "errors": [],
                "current_record": None
            }
            self.websocket_connections[batch_id] = set()
    
    async def update_progress(self, batch_id: str, successful: int = 0, 
                             failed: int = 0, error: dict = None, 
                             current_record: str = None):
        """Actualiza progreso de un batch"""
        async with self.lock:
            if batch_id not in self.progress:
                return
            
            progress = self.progress[batch_id]
            progress["processed"] += 1
            progress["successful"] += successful
            progress["failed"] += failed
            progress["current_record"] = current_record
            
            if error:
                progress["errors"].append(error)
    
    async def complete_batch(self, batch_id: str, status: str = "completed", 
                            error_msg: str = None):
        """Marca un batch como completado"""
        async with self.lock:
            if batch_id not in self.progress:
                return
            
            progress = self.progress[batch_id]
            progress["status"] = status
            progress["end_time"] = datetime.now()
            if error_msg:
                progress["error_message"] = error_msg
    
    def get_progress(self, batch_id: str) -> dict:
        """Obtiene estado actual de un batch"""
        if batch_id not in self.progress:
            return None
        
        progress = self.progress[batch_id]
        start_time = progress["start_time"]
        elapsed = (datetime.now() - start_time).total_seconds()
        
        processed = progress["processed"]
        total = progress["total"]
        percentage = (processed / total * 100) if total > 0 else 0
        
        # Calcular velocidad y tiempo estimado
        speed = processed / elapsed if elapsed > 0 else 0
        remaining = total - processed
        eta = remaining / speed if speed > 0 else 0
        
        return {
            "batch_id": batch_id,
            "processed": processed,
            "total": total,
            "successful": progress["successful"],
            "failed": progress["failed"],
            "percentage": round(percentage, 2),
            "status": progress["status"],
            "current_record": progress["current_record"],
            "speed": round(speed, 2),
            "estimated_time_remaining": round(eta, 2),
            "errors": progress["errors"]
        }
    
    async def register_connection(self, batch_id: str, connection_id: str):
        """Registra una conexión WebSocket para un batch"""
        async with self.lock:
            if batch_id not in self.websocket_connections:
                self.websocket_connections[batch_id] = set()
            self.websocket_connections[batch_id].add(connection_id)
    
    async def unregister_connection(self, batch_id: str, connection_id: str):
        """Desregistra una conexión WebSocket"""
        async with self.lock:
            if batch_id in self.websocket_connections:
                self.websocket_connections[batch_id].discard(connection_id)
    
    async def get_connections(self, batch_id: str) -> Set[str]:
        """Obtiene conexiones activas para un batch"""
        async with self.lock:
            return self.websocket_connections.get(batch_id, set()).copy()
    
    async def cleanup_batch(self, batch_id: str):
        """Limpia datos de un batch (opcional, después de cierto tiempo)"""
        async with self.lock:
            self.progress.pop(batch_id, None)
            self.websocket_connections.pop(batch_id, None)


# Instancia global
progress_manager = ProgressManager()