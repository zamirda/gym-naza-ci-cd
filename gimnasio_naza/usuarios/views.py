from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from gimnasio.models import Usuario,Membresia,Asistencia,Nutricion,Masa_corporal,Rutina,Certificacion_interna,Encuesta,Sancion,Soporte_PQRS
from datetime import date,timedelta
from django.views.generic import ListView,DetailView
import json

from gimnasio.utilities.calcular_dias import calcular_dias
# Create your views here.

from datetime import date
from django.http import Http404
class DashboardUsuarioView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def obtener_dias_restantes(self, membresia):
        hoy = date.today()
        if membresia.fecha_fin < hoy:
            return 0
        if membresia.fecha_inicio > hoy:
            return (membresia.fecha_fin - membresia.fecha_inicio).days
        return (membresia.fecha_fin - hoy).days

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        
        if hasattr(usuario, 'usuario'):
            context['nombre_usuario'] = usuario.usuario.nombre_usuario
            context['apellido_usuario'] = usuario.usuario.apellido_usuario
            context['documento'] = usuario.usuario.documento
            context['correo'] = usuario.usuario.correo_usuario
            context['telefono'] = usuario.usuario.telefono_usuario
            context['usuario_id'] = usuario.usuario.id

            # 1. BUSCAR PLAN GENERADO POR IA EN LA BD
            mi_nutricion = Nutricion.objects.filter(fk_Usuario=usuario.usuario).last()
            context['mi_nutricion'] = mi_nutricion
            
            mi_rutina = None
            if mi_nutricion:
                masa_corp = Masa_corporal.objects.filter(fk_Nutricion=mi_nutricion).last()
                if masa_corp:
                    mi_rutina = Rutina.objects.filter(fk_imc=masa_corp).last()
            context['mi_rutina'] = mi_rutina

            # 2. CALCULAR ASISTENCIAS, BARRA DE PROGRESO Y CALENDARIO
            membresia = Membresia.objects.filter(fk_usuario=usuario.usuario, estado='activo').first()
            
            if membresia:
                asistencia = Asistencia.objects.filter(fk_membresia=membresia)
                
                # ======================================================
                #  CÁLCULO DE LA BARRA DE PROGRESO DE IA
                # ======================================================
                meta_dias_semana = mi_rutina.dias_disponibles if mi_rutina else 4
                meta_mensual = meta_dias_semana * 4 # Aprox 4 semanas al mes
                asistencias_mes = asistencia.filter(fecha_asistencia__month=date.today().month).count()
                
                context['asistencias_mes'] = asistencias_mes
                context['meta_mensual'] = meta_mensual
                
                # Porcentaje exacto para la barra (evitando división por cero y tope en 100%)
                porcentaje_ia = min(int((asistencias_mes / meta_mensual) * 100) if meta_mensual > 0 else 0, 100)
                context['porcentaje_ia'] = porcentaje_ia

                # ======================================================
                # CÁLCULO DEL CALENDARIO
                # ======================================================
                eventos = []
                fecha_actual = membresia.fecha_inicio
                hoy = date.today()

                nombre_rutina = mi_rutina.get_tipo_rutina_display() if mi_rutina else "Entrenamiento"
                dias_entreno = mi_rutina.dias_disponibles if mi_rutina else 4
                
                # Lógica: Asigna los días de entreno en la semana (0=Lunes, 6=Domingo)
                if dias_entreno <= 3: dias_activos = [0, 2, 4]
                elif dias_entreno == 4: dias_activos = [0, 1, 3, 4]
                elif dias_entreno == 5: dias_activos = [0, 1, 2, 3, 4]
                else: dias_activos = [0, 1, 2, 3, 4, 5]

                while fecha_actual <= membresia.fecha_fin:
                    if fecha_actual <= hoy:
                        asistio = asistencia.filter(fecha_asistencia=fecha_actual).exists()
                        if asistio:
                            eventos.append({'title': f'✅ Entrenó: {nombre_rutina}', 'start': fecha_actual.strftime('%Y-%m-%d'), 'color': '#28a745'})
                        elif fecha_actual < hoy:
                            eventos.append({'title': '❌ Faltó', 'start': fecha_actual.strftime('%Y-%m-%d'), 'color': '#dc3545'})
                    else:
                        if mi_rutina and fecha_actual.weekday() in dias_activos:
                            eventos.append({'title': f'📅 Plan: {nombre_rutina}', 'start': fecha_actual.strftime('%Y-%m-%d'), 'color': '#ffd700', 'textColor': '#000'})
                    fecha_actual += timedelta(days=1)

                context['eventos'] = json.dumps(eventos)
                context['dias_restantes'] = self.obtener_dias_restantes(membresia)
                context['dias_totales'] = (membresia.fecha_fin - membresia.fecha_inicio).days
            else:
                # Valores por defecto si no tiene membresía
                context['asistencias_mes'] = 0
                context['meta_mensual'] = 0
                context['porcentaje_ia'] = 0
                context['eventos'] = json.dumps([])
                context['dias_restantes'] = 0
                context['dias_totales'] = 0

        return context
class MiNutricionView(LoginRequiredMixin, ListView):
    model = Nutricion
    template_name = "usuario/nutricion.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        if hasattr(usuario, 'usuario'):
            nutricion = Nutricion.objects.filter(fk_Usuario=usuario.usuario).first()
            
            context['nutricion'] = nutricion
        return context
    

class MiNutricionView(LoginRequiredMixin, ListView):
    model = Nutricion
    template_name = "usuario/nutricion.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        if hasattr(usuario, 'usuario'):
            nutricion = Nutricion.objects.filter(fk_Usuario=usuario.usuario).first()
            
            context['nutricion'] = nutricion
        return context

class MiRutinaView(LoginRequiredMixin,ListView):
    model = Rutina
    template_name = "usuario/rutina.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        if hasattr(usuario,'usuario'):
            rutina = Rutina.objects.filter(fk_imc__fk_Nutricion__fk_Usuario = usuario.usuario)
            context['rutina'] = rutina
        return context
    

class MiCertificacionView(LoginRequiredMixin,ListView):
    model = Certificacion_interna
    template_name = "usuario/certificacion.html"
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        if hasattr(usuario,'usuario'):
            certificacion = Certificacion_interna.objects.filter(fk_membresia__fk_usuario = usuario.usuario)
            context['certificaciones'] = certificacion
        return context
    
class MiEncuestasView(LoginRequiredMixin,ListView):
    model = Encuesta
    template_name = 'usuario/encuestas.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        if hasattr(usuario,'usuario'):
            encuesta = Encuesta.objects.filter(
                miembros = usuario.usuario,
                estado = 'Activo'
            )
            context['encuesta'] = encuesta
        return context

class MisSancionesView(LoginRequiredMixin,ListView):
    model = Sancion
    template_name = 'usuario/sanciones.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        if hasattr(usuario,'usuario'):
            sancion = Sancion.objects.filter(fk_usuario = usuario.usuario)
            context['sancion'] = sancion
        return context


class MiPqrs(LoginRequiredMixin, ListView):
    model = Soporte_PQRS
    template_name = 'usuario/pqrs.html'
    context_object_name = 'lista_pqr'

    def get_queryset(self):
        usuario = getattr(self.request.user, "usuario", None)

        if usuario is None:
            return Soporte_PQRS.objects.none()

        return Soporte_PQRS.objects.filter(
            fk_usuario=usuario
        ).order_by('-fecha_ingreso', '-id')


class MisEncuestasListView(LoginRequiredMixin, ListView):
    model = Encuesta
    template_name = "usuario/mis_encuestas.html"
    context_object_name = "lista_encuestas"  

    def get_queryset(self):
        """
        Trae únicamente las encuestas donde el alumno logueado 
        haya sido asignado en la relación ManyToMany (miembros).
        """
        return Encuesta.objects.filter(
            miembros=self.request.user.usuario
        ).order_by('-fecha_envio', '-fecha_creacion')