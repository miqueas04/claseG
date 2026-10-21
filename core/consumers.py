import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Project


class TaskNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.group_name = f"project_{self.project_id}"

        # Validación: si el project_id no existe en la base de datos, rechazar conexión
        exists = await database_sync_to_async(
            Project.objects.filter(id=self.project_id).exists
        )()
        if not exists:
            await self.close()
            return

        # Nos unimos a un "grupo"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Por ahora, hacemos "echo" del mensaje recibido
        await self.send(text_data=json.dumps({"echo": data}))

    async def task_notification(self, event):
        # Este método es llamado cuando llega un mensaje al grupo (Clase 10)
        await self.send(text_data=json.dumps(event["payload"]))
