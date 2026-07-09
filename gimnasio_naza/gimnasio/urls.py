from django.urls import path
from gimnasio.views import *
from gimnasio.views.Elementos.views import *
from gimnasio.views.Usuario.views import *
from gimnasio.views.Mantenimiento.views import *
from gimnasio.views.Asistencias.views import *
from gimnasio.views.Membresias.views import *
from gimnasio.views.Notificaciones.views import *
from gimnasio.views.Encuestas.views import *
from gimnasio.views.Soporte_PQRS.views import *
from gimnasio.views.Reportes_Estadisticas.views import *
from gimnasio.views.Categorias.views import *
from gimnasio.views.Nutriciones.views import *
from gimnasio.views.Rutinas.views import *
from gimnasio.views.Masa_muscular.views import *
from gimnasio.views.Sanciones.views import *
from gimnasio.views.registrovisitantestemporales.views import *
from gimnasio.views.turnosdeentrenadores.views import *
from gimnasio.views.certificacionesinternas.views import *
from gimnasio.views.Dashboard.views import DashboardView
from gimnasio.views.Reportes.reportes import *
from gimnasio.models import *
from gimnasio.views.backup.backup import backup, restaurar_datos
from gimnasio.views.Encuestas import views as encuesta_views
from gimnasio.views.IA.views import seleccion_plan_ia

app_name = 'gimnasio'

urlpatterns = [
    # ── Elementos ──────────────────────────────────────────────────────────────
    path('crear_elemento/', ElementoCreateView.as_view(), name='crear_elemento'),
    path('listar_elemento/', ElementoListView.as_view(), name='listar_elementos'),
    path('modificar_estado/<int:pk>/',
         ElementoUpdateView.as_view(), name='editar_elemento'),
    path('eliminar_elemento/<int:pk>/',
         ElementoDeleteView.as_view(), name='eliminar_elemento'),
    path('exportar_elementos_pdf/', ExportarElementosPDF.as_view(),
         name='exportar_elementos_pdf'),
    path('exportar_elementos_excel/', ExportarElementosExcel.as_view(),
         name='exportar_elementos_excel'),
    path('crear-categoria-ajax/', crear_categoria_ajax,
         name='crear_categoria_ajax'),

    # ── Usuarios ────────────────────────────────────────────────────────────────
    path('crear_usuario/', UsuarioCreateView.as_view(), name='crear_usuario'),
    path('listar_usuario/', UsuarioListView.as_view(), name='listar_usuario'),
    path('modificar_usuario/<int:pk>/',
         UsuarioUpdateView.as_view(), name='editar_usuario'),
    path('eliminar_usuario/<int:pk>/',
         UsuarioDeleteView.as_view(), name='eliminar_usuario'),
    path('asignar_rol/<int:pk>/', UsuarioRolUpdateView.as_view(),
         name='asignar_rol_usuario'),
    path('exportar_usuarios_pdf/', ExportarUsuariosPDF.as_view(),
         name='exportar_usuarios_pdf'),
    path('exportar_usuarios_excel/', ExportarUsuariosExcel.as_view(),
         name='exportar_usuarios_excel'),
    path('perfil_usuario/', PerfilView.as_view(), name='perfil_usuario'),
    path('crear-usuario-ajax/', crear_usuario_ajax,
         name='crear_usuario_ajax'),  # ✅ Solo una vez
    path('crear_nombre_categoria_ajax/', crear_nombre_categoria_ajax, name='crear_nombre_categoria_ajax'),
    # ── Mantenimiento ───────────────────────────────────────────────────────────
    path('crear_mantenimiento/', MantenimientoCreateView.as_view(),
         name='crear_mantenimiento'),
    path('listar_mantenimiento/', MantenimientoListView.as_view(),
         name='listar_mantenimiento'),
    path('editar_mantenimiento/<int:pk>/',
         MantenimientoUpdateView.as_view(), name='editar_mantenimiento'),
    path('eliminar_mantenimiento/<int:pk>/',
         MantenimientoDeleteView.as_view(), name='eliminar_mantenimiento'),
    path('exportar_mantenimiento_pdf/', ExportarmantenimientoPDF.as_view(),
         name='exportar_mantenimiento_pdf'),
    path('exportar_mantenimiento_excel/', ExportarMantenimientoExcel.as_view(),
         name='exportar_mantenimiento_excel'),
    path('crear_elemento_ajax/', crear_elemento_ajax, name='crear_elemento_ajax'),
    path('crear_categoria_ajax/', crear_categoria_ajax, name='crear_categoria_ajax'),
    

    # ==============================asistencia==============================#

    path('wizard-asistencia/', wizard_asistencia, name='wizard_asistencia'),
    path('listar_asistencia/', AsistenciaListView.as_view(),
         name='listar_asistencia'),
    path('crear_asistencia/', AsistenciaCreateView.as_view(),
         name='crear_asistencia'),
    path('editar_asistencia/<int:pk>/',
         AsistenciaUpdateView.as_view(), name='editar_asistencia'),
    path('eliminar_asistencia/<int:pk>/',
         AsistenciaDeleteView.as_view(), name='eliminar_asistencia'),
    path('registrar_asistencia_qr/', QR_register.as_view(), name='registrarQr'),
    path('exportar_asistencia_pdf/', ExportarAsistenciaPDF.as_view(),
         name='exportar_asistencia_pdf'),
    path('exportar_asistencia_excel/', ExportarAsistenciaExcel.as_view(),
         name='exportar_asistencia_excel'),
    path('crear-membresia-ajax/', crear_membresia_ajax,
         name='crear_membresia_ajax'),

    # ── Membresías ──────────────────────────────────────────────────────────────
    path('listar_membresia/', MembresiaListView.as_view(), name='listar_membresia'),
    path('crear_membresia/', MembresiaCreateView.as_view(), name='crear_membresia'),
    path('editar_membresia/<int:pk>/',
         MembresiaUpdateView.as_view(), name='editar_membresia'),
    path('eliminar_membresia/<int:pk>/',
         MembresiaDeleteView.as_view(), name='eliminar_membresia'),
    path('exportar_membresia_pdf/', ExportarMembresiaPDF.as_view(),
         name='exportar_membresia_pdf'),
    path('exportar_membresia_excel/', ExportarMembresiaExcel.as_view(),
         name='exportar_membresia_excel'),

    # ── Notificaciones ──────────────────────────────────────────────────────────
    path('listar_notificacion/', NotificacionListView.as_view(),
         name='listar_notificacion'),
    path('crear_notificacion/', NotificacionCreateView.as_view(),
         name='crear_notificacion'),
    path('editar_notificacion/<int:pk>/',
         NotificacionUpdateView.as_view(), name='editar_notificacion'),
    path('eliminar_notificacion/<int:pk>/',
         NotificacionDeleteView.as_view(), name='eliminar_notificacion'),

    # ── Encuestas ───────────────────────────────────────────────────────────────
    path('listar_encuestas/', EncuestaListView.as_view(), name='listar_encuestas'),
    path('crear_encuesta/', crear_encuesta, name='crear_encuesta'),
    path('editar_encuesta/<int:pk>/',
         EncuestaUpdateView.as_view(), name='editar_encuesta'),
    path('eliminar_encuesta/<int:pk>/',
         EncuestaDeleteView.as_view(), name='eliminar_encuesta'),
    path('enviar_encuesta/<int:pk>/', enviar_encuesta, name='enviar_encuesta'),
    path('enviar_encuesta_usuarios/', enviar_encuesta_usuarios,
         name='enviar_encuesta_usuarios'),

    # ── Soporte / PQRS ──────────────────────────────────────────────────────────
    path('listar_Soporte_PQRS/', Soporte_PQRSListView.as_view(),
         name='listar_Soporte_PQRS'),
    path('crear_Soporte_PQRS/', Soporte_PQRSCreateView.as_view(),
         name='crear_Soporte_PQRS'),
    path('editar_Soporte_PQRS/<int:pk>/',
         Soporte_PQRSUpdateView.as_view(), name='editar_Soporte_PQRS'),
    path('eliminar_Soporte_PQRS/<int:pk>/',
         Soporte_PQRSDeleteView.as_view(), name='eliminar_Soporte_PQRS'),
    path('ExportarSoporte_PQRSPDF/', ExportarSoporte_PQRSPDF.as_view(),
         name='ExportarSoporte_PQRSPDF'),
    path('ExportarSoporte_PQRSEXCEL/', ExportarSoporte_PQRSEXCEL.as_view(),
         name='ExportarSoporte_PQRSEXCEL'),

    # ── Reportes / Estadísticas ─────────────────────────────────────────────────

    path('crear_Reportes_estadisticas/', Reportes_estadisticasCreateView.as_view(), name='crear_Reportes_estadisticas'),
    path('editar_Reportes_estadisticas/<int:pk>/', Reportes_estadisticasUpdateView.as_view(), name='editar_Reportes_estadisticas'),
    path('eliminar_Reportes_estadisticas/<int:pk>/', Reportes_estadisticasDeleteView.as_view(), name='eliminar_Reportes_estadisticas'),
    path('ExportarReportes_estadisticasPDF/', ExportarReportes_estadisticasPDF.as_view(), name='ExportarReportes_estadisticasPDF'),
    path('ExportarReportes_estadisticasEXCEL/', ExportarReportes_estadisticasEXCEL.as_view(), name='ExportarReportes_estadisticasEXCEL'),
    path('listar_Reportes_estadisticas/', Reportes_estadisticasListView.as_view(),
         name='listar_Reportes_estadisticas'),
    path('crear_Reportes_estadisticas/', Reportes_estadisticasCreateView.as_view(),
         name='crear_Reportes_estadisticas'),
    path('editar_Reportes_estadisticas/<int:pk>/',
         Reportes_estadisticasUpdateView.as_view(), name='editar_Reportes_estadisticas'),
    path('eliminar_Reportes_estadisticas/<int:pk>/',
         Reportes_estadisticasDeleteView.as_view(), name='eliminar_Reportes_estadisticas'),
    path('ExportarReportes_estadisticasPDF/', ExportarReportes_estadisticasPDF.as_view(),
         name='ExportarReportes_estadisticasPDF'),
    path('ExportarReportes_estadisticasEXCEL/', ExportarReportes_estadisticasEXCEL.as_view(),
         name='ExportarReportes_estadisticasEXCEL'),

    # ── Categorías ──────────────────────────────────────────────────────────────
    path('listar_categorias/', categoriaListView.as_view(),
         name='listar_categorias'),
    path('crear_categoria/', CategoriaCreateView.as_view(), name='crear_categoria'),
    path('editar_categoria/<int:pk>/',
         CategoriaUpdateView.as_view(), name='editar_categoria'),
    path('eliminar_categoria/<int:pk>/',
         CategoriaDeleteView.as_view(), name='eliminar_categoria'),

    # ── Nutrición ───────────────────────────────────────────────────────────────
    path('listar_nutriciones/', nutricionListView.as_view(),
         name='listar_nutriciones'),  # ✅ Función, sin .as_view()
    path('crear_nutricion/', NutricionCreateView.as_view(), name='crear_nutricion'),
    path('editar_nutricion/<int:pk>/',
         NutricionUpdateView.as_view(), name='editar_nutricion'),
    path('eliminar_nutricion/<int:pk>/',
         NutricionDeleteView.as_view(), name='eliminar_nutricion'),
    path('crear-nutricion-ajax/', crear_nutricion_ajax,
         name='crear_nutricion_ajax'),

    # ── Rutinas ─────────────────────────────────────────────────────────────────
    path('crear-usuario-ajax/', crear_usuario_ajax_nutricion,
         name='crear_usuario_ajax'),



    # Rutina
    path('listar_rutinas/', rutinaListView.as_view(), name='listar_rutinas'),
    path('crear_rutinas/', RutinaCreateView.as_view(), name='crear_rutina'),
    path('editar_rutinas/<int:pk>/',
         RutinaUpdateView.as_view(), name='editar_rutina'),
    path('eliminar_rutinas/<int:pk>/',
         RutinaDeleteView.as_view(), name='eliminar_rutina'),
    path('wizard/crear-todo/', wizard_crear_todo, name='wizard_crear_todo'),

    # ── Masa Corporal ───────────────────────────────────────────────────────────
    path('listar_masa_corporal_clas/', Masa_corporalListView.as_view(),
         name='listar_masa_corporal_clas'),
    path('crear_masa_corporal/', Masa_corporalCreateView.as_view(),
         name='crear_masa_corporal'),
    path('eliminar_masa_corporal/<int:pk>/',
         Masa_corporalDeleteView.as_view(), name='eliminar_masa_corporal'),
    path('editar_masa_corporal/<int:pk>/',
         Masa_corporalUpdateView.as_view(), name='editar_masa_corporal'),

    # ── Sanciones ───────────────────────────────────────────────────────────────
    path('listar_sanciones_clas/', SacionesListView.as_view(),
         name='listar_sanciones_clas'),
    path('crear_sancion/', SancionesCreateView.as_view(), name='crear_sancion'),
    path('eliminar_sancion/<int:pk>/',
         SancionesDeleteView.as_view(), name='eliminar_sancion'),
    path('editar_sancion/<int:pk>/',
         SancionesUpdateView.as_view(), name='editar_sancion'),
    path('exportar/sanciones/pdf/', ExportarSancionPDF.as_view(),
         name='exportar_sanciones_pdf'),
    path('exportar/sanciones/excel/', ExportarSancionExcel.as_view(),
         name='exportar_sanciones_excel'),

    # ── Visitantes Temporales ───────────────────────────────────────────────────
    path('listar_registrovisitantetemporal/',
         RegistrovisitantetemporalListView.as_view(), name='listar_registrovisitante'),
    path('crear_registrovisitantetemporal/',
         RegistrovisitantestemporalCreateView.as_view(), name='crear_registrovisitante'),
    path('editar_registrovisitantetemporal/<int:pk>/',
         RegistrovisitantetemporalUpdateView.as_view(), name='editar_registrovisitante'),
    path('eliminar_registrovisitantetemporal/<int:pk>/',
         RegistrovisitantetemporalDeleteView.as_view(), name='eliminar_registrovisitante'),
    path('ExportarRegistrovisitantestemporalesPDF/', ExportarRegistrovisitantestemporalesPDF.as_view(),
         name='ExportarRegistrovisitantestemporalesPDF'),
    path('ExportarRegistrovisitantestemporalesExcel/', ExportarRegistrovisitantestemporalesExcel.as_view(),
         name='ExportarRegistrovisitantestemporalesExcel'),

    # ── Turnos de Entrenadores ──────────────────────────────────────────────────
    path('listar_turnodeentrenador/', TurnodeentrenadorListView.as_view(),
         name='listar_turnodeentrenador'),
    path('crear_turnodeentrenador/', TurnodeentrenadorCreateView.as_view(),
         name='crear_turnodeentrenador'),
    path('editar_turnodeentrenador/<int:pk>/',
         TurnodeentrenadorUpdateView.as_view(), name='editar_turnodeentrenador'),
    path('eliminar_turnodeentrenador/<int:pk>/',
         TurnodeentrenadorDeleteView.as_view(), name='eliminar_turnodeentrenador'),
    path('ExportarTurnodeentrenadorPDF/', ExportarTurnodeentrenadorPDF.as_view(),
         name='ExportarTurnodeentrenadorPDF'),
    path('ExportarTurnodeentrenadorExcel/', ExportarTurnodeentrenadorExcel.as_view(),
         name='ExportarTurnodeentrenadorExcel'),

    # ── Certificaciones Internas ────────────────────────────────────────────────
    path('listar_certificacioninterna/', CertificacioninternaListView.as_view(),
         name='listar_certificacioninterna'),
    path('crear_certificacioninterna/', CertificacioninternaCreateView.as_view(),
         name='crear_certificacioninterna'),
    path('editar_certificacioninterna/<int:pk>/',
         CertificacioninternaUpdateView.as_view(), name='editar_certificacioninterna'),
    path('eliminar_certificacioninterna/<int:pk>/',
         CertificacioninternaDeleteView.as_view(), name='eliminar_certificacioninterna'),
    path('certificacion_interna/<int:pk>/',
         CertificacioninternaUser.as_view(), name='certificacion_interna'),
    path('ExportarCertificacioninternaPDF/', ExportarCertificacioninternaPDF.as_view(),
         name='ExportarCertificacioninternaPDF'),
    path('ExportarCertificacioninternaExcel/', ExportarCertificacioninternaExcel.as_view(),
         name='ExportarCertificacioninternaExcel'),
    path(
        'guardar-wizard/',
        guardar_wizard,
        name='guardar_wizard'
    ),
# ── Inteligencia Artificial ────────────────────────────────────────────────
    path('generar-plan-ia/<int:usuario_id>/', seleccion_plan_ia, name='generar_plan_ia'),
    # ── Dashboard y Backup ──────────────────────────────────────────────────────
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('backup/', backup, name='backup'),
    path('backup/restaurar/', restaurar_datos, name='restaurar_datos'),
]