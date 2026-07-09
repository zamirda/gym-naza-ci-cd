from django.urls import path

from gimnasio.views.IA.views import seleccion_plan_ia
from gimnasio.views.Dashboard.views import DashboardView
from .views import DashboardUsuarioView, MiNutricionView,MiRutinaView,MiCertificacionView,MisSancionesView,MiPqrs,MisEncuestasListView
from gimnasio.views.IA.views import *


app_name = 'usuarios'

urlpatterns = [
    path('dashboard/', DashboardUsuarioView.as_view(), name='dashboard_usuario'),
    path('mi-nutricion/', MiNutricionView.as_view(), name='mi_nutricion'),
    path('mi-rutina/', MiRutinaView.as_view(), name='mi_rutina'),
    path('mi-certificacion/', MiCertificacionView.as_view(), name='mi_certificacion'),
    path('mis-sanciones/', MisSancionesView.as_view(), name='mi_sancion'),
    path('mis-pqrs',MiPqrs.as_view(),name='miPqrs'),
    path('mis-encuestas', MisEncuestasListView.as_view(), name='mis_encuestas'),
    
    # Ruta para que el cliente active el motor de IA local
    path('generar-plan-ia/<int:usuario_id>/', seleccion_plan_ia, name='generar_plan_ia'),

    # ── Dashboard y Backup ──────────────────────────────────────────────────────
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
]