"""Router WebSocket pour streaming temps réel."""

import json
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from ...utils.logging import get_logger
from ..task_manager import get_task_manager

logger = get_logger("websocket_router")

router = APIRouter()

# Gestionnaire de connexions WebSocket
class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.task_subscribers: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket):
        """Accepter une nouvelle connexion WebSocket."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"📡 Nouvelle connexion WebSocket - Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Gérer la déconnexion d'un WebSocket."""
        self.active_connections.discard(websocket)
        
        # Nettoyer les souscriptions aux tâches
        for task_id, subscribers in self.task_subscribers.items():
            subscribers.discard(websocket)
        
        # Supprimer les souscriptions vides
        self.task_subscribers = {
            task_id: subs for task_id, subs in self.task_subscribers.items() 
            if subs
        }
        
        logger.info(f"📴 Connexion WebSocket fermée - Total: {len(self.active_connections)}")
        
    async def subscribe_to_task(self, websocket: WebSocket, task_id: str):
        """Abonner un WebSocket aux mises à jour d'une tâche."""
        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = set()
        self.task_subscribers[task_id].add(websocket)
        logger.info(f"🔔 WebSocket abonné à la tâche {task_id}")
        
    async def unsubscribe_from_task(self, websocket: WebSocket, task_id: str):
        """Désabonner un WebSocket d'une tâche."""
        if task_id in self.task_subscribers:
            self.task_subscribers[task_id].discard(websocket)
            if not self.task_subscribers[task_id]:
                del self.task_subscribers[task_id]
        logger.info(f"🔕 WebSocket désabonné de la tâche {task_id}")
        
    async def broadcast_to_all(self, message: dict):
        """Diffuser un message à toutes les connexions actives."""
        if not self.active_connections:
            return
            
        message_json = json.dumps(message)
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message_json)
                else:
                    disconnected.add(websocket)
            except Exception as e:
                logger.warning(f"⚠️ Erreur envoi message WebSocket: {e}")
                disconnected.add(websocket)
        
        # Nettoyer les connexions fermées
        for ws in disconnected:
            self.disconnect(ws)
            
    async def broadcast_task_update(self, task_id: str, update: dict):
        """Diffuser une mise à jour de tâche aux abonnés."""
        if task_id not in self.task_subscribers:
            return
            
        message = {
            "type": "task_update",
            "task_id": task_id,
            "data": update
        }
        message_json = json.dumps(message)
        disconnected = set()
        
        for websocket in self.task_subscribers[task_id]:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message_json)
                else:
                    disconnected.add(websocket)
            except Exception as e:
                logger.warning(f"⚠️ Erreur envoi mise à jour tâche {task_id}: {e}")
                disconnected.add(websocket)
        
        # Nettoyer les connexions fermées
        for ws in disconnected:
            self.disconnect(ws)
            
    async def send_stats_update(self):
        """Envoyer les statistiques système à tous les clients."""
        try:
            task_manager = get_task_manager()
            active_tasks = task_manager.get_active_tasks()
            completed_tasks = task_manager.get_completed_tasks()
            
            stats = {
                "type": "stats_update",
                "data": {
                    "tasks": {
                        "active": len(active_tasks),
                        "completed": len(completed_tasks),
                        "total": len(active_tasks) + len(completed_tasks)
                    },
                    "memory": {
                        "usage": "N/A"  # TODO: Implémenter surveillance mémoire
                    },
                    "performance": {
                        "avg_response_time": "N/A"  # TODO: Implémenter métriques perf
                    }
                }
            }
            
            await self.broadcast_to_all(stats)
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi statistiques: {e}")

# Instance globale du gestionnaire WebSocket
websocket_manager = WebSocketManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket principal pour streaming temps réel."""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Recevoir les messages du client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "subscribe_task":
                    task_id = message.get("task_id")
                    if task_id:
                        await websocket_manager.subscribe_to_task(websocket, task_id)
                        
                elif message_type == "unsubscribe_task":
                    task_id = message.get("task_id")
                    if task_id:
                        await websocket_manager.unsubscribe_from_task(websocket, task_id)
                        
                elif message_type == "ping":
                    # Répondre au ping pour maintenir la connexion
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
                else:
                    logger.warning(f"⚠️ Type de message WebSocket inconnu: {message_type}")
                    
            except json.JSONDecodeError:
                logger.warning("⚠️ Message WebSocket invalide (JSON malformé)")
            except Exception as e:
                logger.error(f"❌ Erreur traitement message WebSocket: {e}")
                
    except WebSocketDisconnect:
        logger.info("📴 Déconnexion WebSocket normale")
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket inattendue: {e}")
    finally:
        websocket_manager.disconnect(websocket)

async def start_stats_broadcaster():
    """Démarrer la diffusion périodique des statistiques."""
    while True:
        try:
            await websocket_manager.send_stats_update()
            await asyncio.sleep(5)  # Mise à jour toutes les 5 secondes
        except Exception as e:
            logger.error(f"❌ Erreur diffusion statistiques: {e}")
            await asyncio.sleep(10)  # Attendre plus longtemps en cas d'erreur

# Fonction d'aide pour notifier les mises à jour de tâches
async def notify_task_update(task_id: str, update: dict):
    """Fonction d'aide pour notifier une mise à jour de tâche."""
    await websocket_manager.broadcast_task_update(task_id, update)

# Fonction d'aide pour diffuser les notifications globales
async def broadcast_notification(notification: dict):
    """Fonction d'aide pour diffuser une notification globale."""
    message = {
        "type": "notification",
        "data": notification
    }
    await websocket_manager.broadcast_to_all(message)