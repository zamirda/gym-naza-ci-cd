import json
from datetime import timedelta

import django.utils.timezone

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.views.generic import (
    ListView,
    TemplateView,
    CreateView,
    UpdateView,
    DeleteView
)

from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from gimnasio.models import *
from gimnasio.forms import Reportes_estadisticasForm


# =========================================================
# DASHBOARD / REPORTES Y ESTADISTICAS
# =========================================================

class Reportes_estadisticasListView(TemplateView):

    template_name = 'Reporte_Estadistica/listar.html'

    # -----------------------------------------------------
    # DISPATCH
    # -----------------------------------------------------
    # @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):

        return super().dispatch(request, *args, **kwargs)

    # -----------------------------------------------------
    # CONTEXTO
    # -----------------------------------------------------
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        hoy = django.utils.timezone.now().date()

        # =================================================
        # TITULOS Y URLS
        # =================================================
        context['titulo'] = 'Listado de reportes de estadistica'

        context['crear_url'] = reverse_lazy(
            'gimnasio:crear_Reportes_estadisticas'
        )

        # =================================================
        # KPIs PRINCIPALES
        # =================================================

        # TOTAL USUARIOS
        context['total_usuarios'] = Usuario.objects.count()

        # MEMBRESIAS ACTIVAS
        context['membresias_activas'] = Membresia.objects.filter(
            estado='activo',
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).count()

        # TOTAL ELEMENTOS
        context['total_elementos'] = Elemento.objects.count()

        # TOTAL ENCUESTAS
        context['total_encuestas'] = Encuesta.objects.count()

        # TOTAL NOTIFICACIONES
        context['total_notificaciones'] = Notificacion.objects.count()

        # TOTAL SANCIONES
        context['total_sanciones'] = Sancion.objects.count()
        # TOTAL REPORTES
        context['total_reportes'] = Reportes_estadisticas.objects.count()

        # USUARIOS ACTIVOS
        context['usuarios_activos'] = Usuario.objects.filter(
            estado='activo'
        ).count()

        # ELEMENTOS ACTIVOS
        context['elementos_activos'] = Elemento.objects.filter(
            estado='activo'
        ).count()

        # PQRS PENDIENTES
        context['pqrs_pendientes'] = Soporte_PQRS.objects.filter(
            estado='pendiente'
        ).count()

        # =================================================
        # MANTENIMIENTOS
        # =================================================

        context['mant_pendientes'] = Mantenimiento.objects.filter(
            estado='pendiente'
        ).count()

        context['mant_proceso'] = Mantenimiento.objects.filter(
            estado='en_proceso'
        ).count()

        context['mant_completados'] = Mantenimiento.objects.filter(
            estado='completado'
        ).count()

        context['elementos_mantenimiento'] = Mantenimiento.objects.filter(
            estado__in=['pendiente', 'en proceso']
        ).count()

        # =================================================
        # MEMBRESIAS POR VENCER
        # =================================================

        fecha_limite = hoy + timedelta(days=30)

        membresias_por_vencer = Membresia.objects.filter(
            fecha_fin__gte=hoy,
            fecha_fin__lte=fecha_limite
        ).select_related('fk_usuario')

        context['membresias_por_vencer'] = membresias_por_vencer

        # =================================================
        # GRAFICA DE BARRAS
        # =================================================

        labels_estadisticas = [
            'Usuarios',
            'Membresías',
            'Asistencias',
            'Elementos',
            'Encuestas',
            'Reportes'
        ]

        datos_estadisticas = [
            context['total_usuarios'],
            Membresia.objects.count(),
            Asistencia.objects.count(),
            context['total_elementos'],
            context['total_encuestas'],
            context['total_reportes']
        ]

        context['labels_estadisticas'] = json.dumps(
            labels_estadisticas
        )

        context['datos_estadisticas'] = json.dumps(
            datos_estadisticas
        )

        # =================================================
        # ASISTENCIAS ULTIMOS 7 DIAS
        # =================================================

        dias_semana = []

        asistencias_semana = []

        for i in range(6, -1, -1):

            fecha = hoy - timedelta(days=i)

            dias_semana.append(
                fecha.strftime('%d %b')
            )

            total_asistencias = Asistencia.objects.filter(
                fecha_asistencia=fecha
            ).count()

            asistencias_semana.append(
                total_asistencias
            )

        context['dias_semana'] = json.dumps(
            dias_semana
        )

        context['asistencias_semana'] = json.dumps(
            asistencias_semana
        )

        # =================================================
        # DATOS GRAFICOS OPCIONALES
        # =================================================

        context['rutinas_labels'] = json.dumps([])

        context['rutinas_data'] = json.dumps([])

        context['porcentaje_activas'] = 0

        context['porcentaje_inactivas'] = 0

        # =================================================
        # HISTORIAL DE REPORTES
        # =================================================

        context['object_list'] = (
            Reportes_estadisticas.objects
            .select_related('fk_usuario')
            .order_by('-fecha_generacion')
        )

        return context
# =========================================================
# CREAR REPORTE
# =========================================================

class Reportes_estadisticasCreateView(CreateView):

    model = Reportes_estadisticas

    template_name = 'Reporte_Estadistica/crear.html'

    form_class = Reportes_estadisticasForm

    success_url = reverse_lazy(
        'gimnasio:listar_Reportes_estadisticas'
    )

    # -----------------------------------------------------
    # CONTEXTO
    # -----------------------------------------------------
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['titulo'] = 'Crear Reportes y estadisticas'

        context['listar_url'] = reverse_lazy(
            'gimnasio:listar_Reportes_estadisticas'
        )

        return context

    # -----------------------------------------------------
    # MENSAJE SUCCESS
    # -----------------------------------------------------
    def form_valid(self, form):

        messages.success(
            self.request,
            "Reporte guardado correctamente"
        )

        return super().form_valid(form)


# =========================================================
# EDITAR REPORTE
# =========================================================

class Reportes_estadisticasUpdateView(UpdateView):

    model = Reportes_estadisticas

    form_class = Reportes_estadisticasForm

    template_name = 'Reporte_Estadistica/crear.html'

    success_url = reverse_lazy(
        'gimnasio:listar_Reportes_estadisticas'
    )

    # -----------------------------------------------------
    # CONTEXTO
    # -----------------------------------------------------
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['titulo'] = 'Editar Reportes y estadisticas'

        context['listar_url'] = reverse_lazy(
            'gimnasio:listar_Reportes_estadisticas'
        )

        return context

    # -----------------------------------------------------
    # MENSAJE SUCCESS
    # -----------------------------------------------------
    def form_valid(self, form):

        messages.success(
            self.request,
            "Reporte editado correctamente"
        )

        return super().form_valid(form)


# =========================================================
# ELIMINAR REPORTE
# =========================================================

class Reportes_estadisticasDeleteView(DeleteView):

    model = Reportes_estadisticas

    template_name = 'Reporte_Estadistica/eliminar.html'

    success_url = reverse_lazy(
        'gimnasio:listar_Reportes_estadisticas'
    )

    # -----------------------------------------------------
    # CONTEXTO
    # -----------------------------------------------------
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['titulo'] = 'Eliminar Reportes y estadisticas'

        context['listar_url'] = reverse_lazy(
            'gimnasio:listar_Reportes_estadisticas'
        )

        return context

    # -----------------------------------------------------
    # MENSAJE SUCCESS
    # -----------------------------------------------------
    def form_valid(self, form):

        messages.success(
            self.request,
            "Reporte eliminado correctamente"
        )

        return super().form_valid(form)