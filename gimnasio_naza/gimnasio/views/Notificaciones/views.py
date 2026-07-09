import json
from django.views import generic
from django.utils import timezone
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from gimnasio.models import *
from gimnasio.forms import NotificacionForm
from django.http import HttpResponse,JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


def crear_usuario_ajax(request):

    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)

    
        if not data.get('documento') or not data.get('nombre') or not data.get('apellido') or not data.get('correo'):
            return JsonResponse({'error': 'Faltan campos obligatorios'})

  
        if Usuario.objects.filter(documento=data['documento']).exists():
            return JsonResponse({'error': 'El usuario ya existe'})

    
        if data.get('fecha_nacimiento'):
            fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], "%Y-%m-%d").date()
        else:
            fecha_nacimiento = date(2000, 1, 1)
        peso = float(data.get('peso') or 0)
        altura = float(data.get('altura') or 0)
        password = data.get('password') or "123456"
        user = User.objects.create(
            username=data['username'],
            email = data.get('correo','')
        )
        user.set_password(password)
        user.save()
        usuario = Usuario.objects.create(
            user=user,
            documento=data['documento'],
            nombre_usuario=data['nombre'],
            apellido_usuario=data['apellido'],
            correo_usuario=data['correo'],
            telefono_usuario=data.get('telefono', ''),
            fecha_nacimiento=fecha_nacimiento,
            peso_usuario=peso,
            altura_usuario=altura,
            genero_usuario=data.get('genero', 'M'),
            rol='cliente',
            estado='activo',
            fecha_registro=date.today()
        )
        membresia = Membresia.objects.create(
            fk_usuario = usuario
        )
        return JsonResponse({
            'id': usuario.id,
            'nombre': f"{usuario.nombre_usuario} {usuario.apellido_usuario}"
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        })

#Listar notificaciones 
def Listar_notificacion(request):
    nombre ={
        'titulo':'Listado de Notificaciones',
        'notificaciones': Notificacion.objects.all()
    }
    return render(request,'Notificacion/listar.html', nombre)

class NotificacionListView(ListView):
    model = Notificacion
    template_name = 'Notificacion/listar.html'

 
    # metodo dispatch
    #@method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        #if request.method == 'GET':
            #return redirect('app:listar_categorias')
        return super().dispatch(request, *args, **kwargs)
    
    # metodo post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    #metodo context data 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Listado de notificaciones'
        context['crear_url']= reverse_lazy('gimnasio:crear_notificacion')
        return context


class NotificacionCreateView(CreateView):
    model = Notificacion
    template_name = 'Notificacion/crear.html'
    form_class = NotificacionForm
    success_url = reverse_lazy('gimnasio:listar_notificacion')
    #@method_decorator(csrf_exempt)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear notificacion'
        return context
    
class NotificacionUpdateView(UpdateView):
    model = Notificacion
    template_name = 'Notificacion/crear.html'
    success_url = reverse_lazy('gimnasio:listar_notificacion')
    form_class = NotificacionForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar notificacion'
        context['listar_url'] = reverse_lazy('gimnasio:listar_notificacion')
        return super().get_context_data(**kwargs)

class NotificacionDeleteView(DeleteView):
    model = Notificacion
    template_name = 'Notificacion/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_notificacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar notificacion'
        context['listar_url'] = reverse_lazy('gimnasio:listar_notificacion')
        return context




    
    
    