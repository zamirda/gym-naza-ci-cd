from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin


from gimnasio.models import *
from gimnasio.forms import NutricionForm
import json


def crear_usuario_ajax_nutricion(request):
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



#Listar nutriciones


class nutricionListView(PermissionRequiredMixin,ListView):
    model = Nutricion
    template_name = 'Nutricion/listar.html'
    permission_required = 'gimnasio.view_nutricion'
    raise_exception = True
    
    #METODO DISPATCH
    #@method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        #if request.method == 'GET':
            #return redirect('app: listar_categorias')    
        return super().dispatch(request, *args, **kwargs)
    
    #METODO POST
    def post(self, request, *args, **kwargs ):
        return super().post(request, *args, **kwargs)

    
    #METODO GET CONTEXT DATA
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Listado de Nutriciones'
        context['crear_url'] = reverse_lazy('gimnasio:crear_nutricion')
        return context
    
#Crear categoria    
class NutricionCreateView(PermissionRequiredMixin,CreateView):
    model = Nutricion
    template_name = 'Nutricion/crear.html'
    form_class = NutricionForm
    success_url = reverse_lazy('gimnasio:listar_nutriciones')
    permission_required = 'gimnasio.add_nutricion'
    raise_exception = True

    #@method_decorator(csrf_exempt)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nutrición'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Nutricion guardada correctamente")
        return super().form_valid(form)
    
    
class NutricionUpdateView(UpdateView):
    model = Nutricion
    form_class = NutricionForm
    template_name = 'Nutricion/crear.html'
    success_url = reverse_lazy('gimnasio:listar_nutriciones')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Nutricion'
        context['listar_url'] = reverse_lazy('gimnasio:listar_nutriciones')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "La nutricion se editó correctamente")
        return super().form_valid(form)
    
    
class NutricionDeleteView(DeleteView):
    model = Nutricion
    template_name = 'Nutricion/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_nutriciones')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar Nutricion'
        context['listar_url'] = reverse_lazy('gimnasio:listar_nutriciones')
        return context

    def form_valid(self, form):
        messages.success(self.request, "La nutricion se eliminó correctamente")
        return super().form_valid(form)