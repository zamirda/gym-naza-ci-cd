from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone as Time
import json
from gimnasio.models import *
from gimnasio.forms import EncuestaForm, PreguntaFormSet
from gimnasio.utils import (
    crear_formulario_google, 
    actualizar_formulario_google, 
    agregar_preguntas_a_formulario, 
    validar_credenciales_google_forms
)
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction


# --- ENVÍO INDIVIDUAL (Resuelve el NameError en urls.py) ---
def enviar_encuesta(request, pk):
    """ Envía la encuesta a un usuario específico desde el listado """
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        try:
            encuesta = Encuesta.objects.get(pk=pk)
            usuario = Usuario.objects.get(pk=usuario_id)
            
            if encuesta.estado != 'activa':
                messages.error(request, "No se puede enviar una encuesta inactiva.")
                return redirect('gimnasio:listar_encuestas')
            
            if not encuesta.form_id:
                messages.error(request, "Falta el formulario de Google.")
                return redirect('gimnasio:listar_encuestas')

            form_link = f"https://docs.google.com/forms/d/{encuesta.form_id}/viewform"
            subject = f"Encuesta Gym: {encuesta.nombre}"
            message = f"Hola {usuario.nombre_usuario}, por favor llena esta encuesta: {form_link}"
            
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [usuario.correo_usuario])

            
            encuesta.fecha_envio = Time.now()
            encuesta.save()

            messages.success(request, f"Enviada a {usuario.nombre_usuario}")

        except Exception as e:
            messages.error(request, "Selecciona un usuario antes de enviar la encuesta")

    return redirect('gimnasio:listar_encuestas')

# --- FUNCIONES DE ENVÍO MASIVO ---
def enviar_encuesta_usuarios(request):
    if request.method == 'POST':
        encuesta_id = request.POST.get('encuesta_id')
        usuarios_ids = request.POST.getlist('usuarios')
        
        if not encuesta_id or not usuarios_ids:
            messages.error(request, "Selecciona encuesta y usuarios.")
            return redirect('gimnasio:listar_encuestas')
        
        try:
            encuesta = Encuesta.objects.get(id=encuesta_id)
            
            if encuesta.estado != 'activa':
                messages.error(request, "No se puede enviar una encuesta inactiva.")
                return redirect('gimnasio:listar_encuestas')
            
            usuarios = Usuario.objects.filter(id__in=usuarios_ids)
            form_link = f"https://docs.google.com/forms/d/{encuesta.form_id}/viewform"
            
            for usuario in usuarios:
                if usuario.correo_usuario:
                    send_mail(f"Encuesta: {encuesta.nombre}", f"Link: {form_link}", settings.DEFAULT_FROM_EMAIL, [usuario.correo_usuario])
            
            encuesta.fecha_envio = Time.now()
            encuesta.save()
            messages.success(request, "Correos enviados exitosamente.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    return redirect('gimnasio:listar_encuestas')

def crear_usuario_ajax(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
        with transaction.atomic():
            usuario = Usuario.objects.create(
                documento=data['documento'],
                nombre_usuario=data['nombre'],
                apellido_usuario=data['apellido'],
                correo_usuario=data['correo'],
                fecha_nacimiento=data.get('fecha_nacimiento', '2000-01-01'),
                peso_usuario=float(data.get('peso') or 0),
                altura_usuario=float(data.get('altura') or 0),
                estado='activo',
                fecha_registro=date.today()
            )
            return JsonResponse({'id': usuario.id, 'nombre': f"{usuario.nombre_usuario}"})
        
    except Exception as e:
        return JsonResponse({'error': str(e)})

# --- VISTAS DE ENCUESTAS ---
class EncuestaListView(ListView):
    model = Encuesta
    template_name = 'Encuesta/listar.html'
    context_object_name = 'encuestas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Listado de Encuestas'
        context['usuarios_activos'] = Usuario.objects.filter(estado='activo')
        return context

def crear_encuesta(request):
    """ Esta función es la que abre el formulario de creación """
    if request.method == 'POST':
        form = EncuestaForm(request.POST)
        formset = PreguntaFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Validar Conexión Google
            conectado, mensaje = validar_credenciales_google_forms()
            if not conectado:
                messages.error(request, f"Error Google: {mensaje}")
            else:
                try:
                    # Crear en Google (Solo Título)
                    google_form = crear_formulario_google(form.cleaned_data['nombre'])
                    form_id = google_form['formId']
                    
                    # Guardar Localmente
                    encuesta = form.save(commit=False)
                    encuesta.form_id = form_id
                    encuesta.save()
                    form.save_m2m() # Importante para Select2
                    
                    # Preguntas a Google
                    agregar_preguntas_a_formulario(form_id, formset)
                    
                    formset.instance = encuesta
                    formset.save()
                    
                    messages.success(request, "¡Encuesta creada con éxito!")
                    return redirect('gimnasio:listar_encuestas')
                except Exception as e:
                    messages.error(request, f"Error API: {str(e)}")
    else:
        # Petición GET: Aquí se inicializan los formularios vacíos para abrir la vista
        form = EncuestaForm()
        formset = PreguntaFormSet()
    
    return render(request, 'Encuesta/crear.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Crear Nueva Encuesta'
    })

class EncuestaUpdateView(UpdateView):
    model = Encuesta
    form_class = EncuestaForm
    template_name = 'Encuesta/crear.html'
    success_url = reverse_lazy('gimnasio:listar_encuestas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Encuesta'
        context['formset'] = PreguntaFormSet(self.request.POST or None, instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return redirect(self.success_url)
        return self.render_to_response(self.get_context_data(form=form))

class EncuestaDeleteView(DeleteView):
    model = Encuesta
    template_name = 'Encuesta/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_encuestas')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar encuesta'
        context['listar_url'] = reverse_lazy('gimnasio:listar_encuestas')
        return context