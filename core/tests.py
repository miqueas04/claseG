from datetime import date, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient
from core.models import Project, ProjectMembership, Task
from core.serializers import TaskSerializer


class TaskSerializerValidationTestCase(TestCase):
    def setUp(self):
        self.project_empty = Project.objects.create(name="Proyecto Vacio", description="Sin tareas completadas")
        self.project_with_completed = Project.objects.create(name="Proyecto con Completada", description="Con tareas")
        self.tomorrow = date.today() + timedelta(days=1)
        
        # Tarea completada en project_with_completed
        self.completed_task = Task.objects.create(
            project=self.project_with_completed,
            title="Tarea Terminada",
            status="completada",
            due_date=self.tomorrow,
        )

    def test_create_en_progreso_without_completed_task_fails(self):
        """No debe permitir crear tarea 'en_progreso' si el proyecto no tiene ninguna completada."""
        data = {
            "project": self.project_empty.id,
            "title": "Nueva Tarea",
            "status": "en_progreso",
            "due_date": self.tomorrow,
        }
        serializer = TaskSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn(
            "No se puede poner en progreso si el proyecto no tiene ninguna tarea completada.",
            str(serializer.errors["non_field_errors"]),
        )

    def test_create_en_progreso_with_completed_task_succeeds(self):
        """Debe permitir crear tarea 'en_progreso' si el proyecto ya tiene alguna completada."""
        data = {
            "project": self.project_with_completed.id,
            "title": "Nueva Tarea en Progreso",
            "status": "en_progreso",
            "due_date": self.tomorrow,
        }
        serializer = TaskSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_pendiente_without_completed_task_succeeds(self):
        """Crear tarea 'pendiente' debe permitirse aunque no haya tareas completadas."""
        data = {
            "project": self.project_empty.id,
            "title": "Tarea Pendiente",
            "status": "pendiente",
            "due_date": self.tomorrow,
        }
        serializer = TaskSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_status_to_en_progreso_without_completed_task_fails(self):
        """Actualizar (PATCH) a 'en_progreso' sin tareas completadas debe fallar."""
        task = Task.objects.create(
            project=self.project_empty,
            title="Tarea Inicial Pendiente",
            status="pendiente",
            due_date=self.tomorrow,
        )
        data = {"status": "en_progreso"}
        serializer = TaskSerializer(instance=task, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertIn(
            "No se puede poner en progreso si el proyecto no tiene ninguna tarea completada.",
            str(serializer.errors["non_field_errors"]),
        )

    def test_update_status_to_en_progreso_with_completed_task_succeeds(self):
        """Actualizar (PATCH) a 'en_progreso' cuando el proyecto sí tiene una completada debe funcionar."""
        task = Task.objects.create(
            project=self.project_with_completed,
            title="Tarea Inicial Pendiente",
            status="pendiente",
            due_date=self.tomorrow,
        )
        data = {"status": "en_progreso"}
        serializer = TaskSerializer(instance=task, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_title_of_in_progress_task_with_completed_task_succeeds(self):
        """Editar otros campos de una tarea en progreso cuando hay completadas funciona correctamente."""
        task = Task.objects.create(
            project=self.project_with_completed,
            title="Tarea en progreso",
            status="en_progreso",
            due_date=self.tomorrow,
        )
        data = {"title": "Titulo Actualizado"}
        serializer = TaskSerializer(instance=task, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_in_progress_to_completada_succeeds(self):
        """Mover de 'en_progreso' a 'completada' con fecha valida funciona correctamente."""
        task = Task.objects.create(
            project=self.project_with_completed,
            title="Tarea en progreso",
            status="en_progreso",
            due_date=self.tomorrow,
        )
        data = {"status": "completada", "due_date": self.tomorrow}
        serializer = TaskSerializer(instance=task, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class TaskAPIValidationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="admin_user", password="password123")
        self.client.force_authenticate(user=self.user)

        self.project_empty = Project.objects.create(name="Proyecto Vacio")
        ProjectMembership.objects.create(project=self.project_empty, user=self.user, role="admin")

        self.tomorrow = (date.today() + timedelta(days=1)).isoformat()

    def test_api_post_en_progreso_without_completed_returns_400(self):
        response = self.client.post(
            "/api/tasks/",
            {
                "project": self.project_empty.id,
                "title": "API Tarea",
                "status": "en_progreso",
                "due_date": self.tomorrow,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("No se puede poner en progreso si el proyecto no tiene ninguna tarea completada.", str(response.data))


from core.models import SecurityLog
from channels.testing import WebsocketCommunicator
from config.asgi import application


class SecurityAndSanitizationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(username="admin_user", password="password123")
        self.member_user = User.objects.create_user(username="member_user", password="password123")
        self.project = Project.objects.create(name="Proyecto Seguro")
        ProjectMembership.objects.create(project=self.project, user=self.admin_user, role="admin")
        ProjectMembership.objects.create(project=self.project, user=self.member_user, role="miembro")
        self.task = Task.objects.create(
            project=self.project,
            title="Tarea de prueba",
            due_date=date.today() + timedelta(days=2),
        )

    def test_description_sanitization_removes_html_and_scripts(self):
        """nh3 debe sanitizar la descripcion removiendo tags HTML y scripts."""
        data = {
            "project": self.project.id,
            "title": "Tarea Sanitizada",
            "description": "<script>alert(1)</script>Hola <b>mundo</b>",
            "due_date": date.today() + timedelta(days=2),
        }
        serializer = TaskSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["description"], "Hola mundo")

    def test_failed_login_creates_security_log(self):
        """Un intento fallido de login debe crear un registro en SecurityLog."""
        SecurityLog.objects.all().delete()
        response = self.client.post(
            "/api/token/",
            {"username": "admin_user", "password": "wrong_password"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertTrue(SecurityLog.objects.filter(action="login_failed", detail="usuario=admin_user").exists())

    def test_non_admin_member_denied_creates_security_log(self):
        """Un miembro no admin que intenta modificar una tarea recibe 403 y registra SecurityLog."""
        SecurityLog.objects.all().delete()
        self.client.force_authenticate(user=self.member_user)
        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {"title": "Intento de edicion"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(SecurityLog.objects.filter(action="permission_denied", user=self.member_user).exists())

    def test_cors_headers_allowed_origin(self):
        """CorsMiddleware debe responder con encabezado CORS para origenes permitidos."""
        response = self.client.options(
            "/api/tasks/",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://localhost:3000")

    def test_cors_headers_disallowed_origin(self):
        """CorsMiddleware no debe permitir origenes no autorizados."""
        response = self.client.options(
            "/api/tasks/",
            HTTP_ORIGIN="http://sitio-malicioso.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )
        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))


class WebSocketConsumerTestCase(TestCase):
    async def test_websocket_connect_existing_project_echo(self):
        """Conexion a un proyecto existente debe ser aceptada y hacer echo del mensaje."""
        project = await Project.objects.acreate(name="WS Project")
        communicator = WebsocketCommunicator(application, f"ws/projects/{project.id}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Enviar mensaje de prueba
        await communicator.send_json_to({"mensaje": "hola desde test"})
        response = await communicator.receive_json_from()
        self.assertEqual(response, {"echo": {"mensaje": "hola desde test"}})

        await communicator.disconnect()

    async def test_websocket_connect_non_existing_project_rejected(self):
        """Conexion a un proyecto inexistente debe ser rechazada (close)."""
        communicator = WebsocketCommunicator(application, "ws/projects/99999/")
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()
