import json
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, TemplateView
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import ExtractMonth
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin


# Importamos SOLO los modelos que vamos a usar explícitamente, evitando colisiones
from gimnasio.models import Usuario, Asistencia, Membresia, Elemento, Soporte_PQRS, Rutina

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'Dashboard/dashboard.html'
    def dispatch(self, request, *args, **kwargs):
        print("Accediendo al DashboardView...")
        print("Usuario actual:", request.user)
        user = self.request.user

        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        if hasattr(user, 'usuario') and user.usuario.rol == 'Administrador':
            return super().dispatch(request, *args, **kwargs)

        return redirect('usuarios:dashboard_usuario')
    
    def get_context_data(self, **kwargs):
        # Llamamos al contexto original
        context = super().get_context_data(**kwargs)
        
        # Obtenemos la fecha de hoy
        hoy = timezone.now().date()

        # ---------------------------------------------------------
        # //1.KPIs principales// request, *args, **kwargs):
        user = self.request.user

        # ---------------------------------------------------------
        context['usuarios_activos'] = Usuario.objects.filter(estado='activo').count()
        context['asistencias_hoy'] = Asistencia.objects.filter(fecha_asistencia=hoy).count()
        
        # Membresías vigentes (Iniciaron hoy o antes, y terminan hoy o después)
        membresias_activas = Membresia.objects.filter(estado='activo').count()
        membresias_inactivas = Membresia.objects.filter(estado='inactivo').count()

        total_membresias = membresias_activas + membresias_inactivas

        # ---------------------------------------------------------
        # //Estadisticas generales//
        # ---------------------------------------------------------
        context['total_usuarios'] = Usuario.objects.count()
        context['elementos_activos'] = Elemento.objects.filter(estado='activo').count()
        context['pqrs_pendientes'] = Soporte_PQRS.objects.filter(estado='pendiente').count()

        # ---------------------------------------------------------
        # //ultimos 7 dias asistencias//
        # ---------------------------------------------------------
        dias_semana = []
        asistencias_semana = []
        
        # Recorremos los últimos 7 días hacia atrás (6, 5, 4, 3, 2, 1, 0)
        for i in range(6, -1, -1):
            fecha = hoy - timedelta(days=i)
            # Formateamos la fecha (ej. "05 Mar")
            dias_semana.append(fecha.strftime('%d %b')) 
            # Contamos cuántas asistencias hubo ese día
            asistencias_dia = Asistencia.objects.filter(fecha_asistencia=fecha).count()
            asistencias_semana.append(asistencias_dia)
            
        # Convertimos las listas a JSON para que JavaScript (Chart.js) pueda leerlas
        context['dias_semana'] = json.dumps(dias_semana)
        context['asistencias_semana'] = json.dumps(asistencias_semana)

        # ---------------------------------------------------------
        # // GRAFICO DE PASTEL: Tipos de Rutina asignadas//
        # ---------------------------------------------------------
        rutinas_fuerza = Rutina.objects.filter(tipo_rutina='FUERZA').count()
        rutinas_cardio = Rutina.objects.filter(tipo_rutina='CARDIO').count()
        rutinas_funcional = Rutina.objects.filter(tipo_rutina='FUNCIONAL').count()
        
        context['rutinas_data'] = json.dumps([rutinas_fuerza, rutinas_cardio, rutinas_funcional])
        context['rutinas_labels'] = json.dumps(['Fuerza', 'Cardio', 'Funcional'])

        # ---------------------------------------------------------
        # //Estado de las Membresias (Porcentajes)//
        # ---------------------------------------------------------
        total_membresias = membresias_activas + membresias_inactivas

        if total_membresias > 0:
            porcentaje_activas = int((membresias_activas / total_membresias) * 100)
            porcentaje_inactivas = int((membresias_inactivas / total_membresias) * 100)
        else:
            porcentaje_activas = 0
            porcentaje_inactivas = 0

        context['porcentaje_activas'] = porcentaje_activas
        context['porcentaje_inactivas'] = porcentaje_inactivas


        # ---------------------------------------------------------
        # // CRECIMIENTO MENSUAL USUARIOS //
        # ---------------------------------------------------------

        usuarios_por_mes = (
            Usuario.objects
            .annotate(mes=ExtractMonth('fecha_registro'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )

        # Inicializamos meses
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

        datos_meses = [0] * 12

        for item in usuarios_por_mes:
            mes_index = item['mes'] - 1
            datos_meses[mes_index] = item['total']

        # SOLO mostramos los últimos 3 meses (como tu gráfica)
        context['meses_labels'] = json.dumps(meses[:3])
        context['usuarios_mensuales'] = json.dumps(datos_meses[:3])
        return context



       