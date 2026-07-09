from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from gimnasio.models import Certificacion_interna, Asistencia, Membresia, Usuario
from django.contrib.auth.models import User
from gimnasio.forms import CertificacioninternaForm
from django.contrib import messages
from django.views import View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.utils import timezone
from django.shortcuts import redirect
from django.http import JsonResponse
import json

from django.views.decorators.csrf import csrf_exempt
from django.db import transaction


@csrf_exempt
def guardar_wizard(request):

    if request.method == 'POST':

        try:

            data = json.loads(request.body)
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password']
                ) 

                usuario = Usuario.objects.create(
                    user=user,
                    documento=data['documento'],
                    nombre_usuario=data['nombre'],
                    apellido_usuario=data['apellido'],
                    correo_usuario=data['correo'],
                    telefono_usuario=data['telefono'],
                    fecha_nacimiento=data['fecha_nacimiento'],
                    peso_usuario=data['peso_usuario'],
                    altura_usuario=data['altura_usuario'],
                    genero_usuario=data['genero'],
                    rol='cliente',
                    estado='Activo',
                    fecha_registro=timezone.now()
                )

                Membresia.objects.create(
                    fk_usuario=usuario,
                    fecha_inicio=data['fecha_inicio'],
                    fecha_fin=data['fecha_fin'],
                    estado=data['estado']
                )

                return JsonResponse({
                    'success': True,
                    'message': 'Usuario registrado correctamente'
                })

        except Exception as e:

            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })


class CertificacioninternaListView(ListView):
    model = Certificacion_interna
    template_name = 'certificacioninterna/listar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Listado de certificaciones internas'
        context['crear_url'] = reverse_lazy(
            'gimnasio:crear_certificacioninterna')
        return context


class CertificacioninternaCreateView(CreateView):
    model = Certificacion_interna
    form_class = CertificacioninternaForm
    template_name = 'certificacioninterna/crear.html'
    success_url = reverse_lazy('gimnasio:listar_certificacioninterna')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear certificación interna'
        return context

    def form_valid(self, form):
        print('Aqui')
        messages.success(self.request, 'Certificacion creada correctamente')
        return super().form_valid(form)


class CertificacioninternaUpdateView(UpdateView):
    model = Certificacion_interna
    form_class = CertificacioninternaForm
    template_name = 'certificacioninterna/crear.html'
    success_url = reverse_lazy('gimnasio:listar_certificacioninterna')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar certificación interna'
        return context

    def form_valid(self, form):
        messages.success(
            self.request, 'Actualizacion de certificación interna actualizado correctamente')
        return super().form_valid(form)


class CertificacioninternaDeleteView(DeleteView):
    model = Certificacion_interna
    template_name = 'certificacioninterna/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_certificacioninterna')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar certificación interna'
        context['listar_url'] = reverse_lazy(
            'gimnasio:listar_certificacioninterna')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Certificación interna eliminada correctamente')
        return super().form_valid(form)



class CertificacioninternaUser(View):
    template_name = 'certificacioninterna/diploma.html'

    def get(self, request, pk, *args, **kwargs):
        certificaciones = get_object_or_404(Certificacion_interna, pk=pk)
        if certificaciones.descargado:
            messages.error(self.request, 'ya fue descargada')
            return redirect('gimnasio:listar_certificacioninterna')
        context = {
            'nombre': certificaciones.fk_membresia.fk_usuario.nombre_usuario,
            'apellido': certificaciones.fk_membresia.fk_usuario.apellido_usuario,
            'documento': certificaciones.fk_membresia.fk_usuario.documento,
            'fecha': certificaciones.fk_membresia.fecha_inicio,
            'fecha_hoy': timezone.now(),
        }
        print(context)
        html_content = render_to_string(self.template_name, context)
        pdf = HTML(string=html_content,
                   base_url=request.build_absolute_uri()).write_pdf()
        certificaciones.descargado = True
        certificaciones.save()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment;filename="Certificacion_{certificaciones.fk_membresia.fk_usuario.nombre_usuario}_{timezone.now().strftime("%Y-%m-%d")}.pdf"'
        return response
