from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.views.generic import CreateView , UpdateView , DeleteView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from gimnasio.models import *
from gimnasio.forms import SancionesForm
from django.contrib import messages
import json
from datetime import date, datetime
@csrf_exempt
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

        usuario = Usuario.objects.create(
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

        return JsonResponse({
            'id': usuario.id,
            'nombre': f"{usuario.nombre_usuario} {usuario.apellido_usuario}"
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        })
#Listar asistencia 
def Listar_sanciones(request):
    nombre ={
        'titulo':'Listado de Sanciones',
        'sanciones': Sancion.objects.all()
    }
    return render(request,'Sanciones/listar.html', nombre)

class SacionesListView(ListView):
    model = Sancion
    template_name = 'Sanciones/listar.html'
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
        context['titulo'] = 'Listado de sanciones'
        context['crear_url']= reverse_lazy('gimnasio:crear_sancion')
        return context


class SancionesCreateView(CreateView):
    model = Sancion
    template_name = 'Sanciones/crear.html'
    form_class = SancionesForm
    success_url = reverse_lazy('gimnasio:listar_sanciones_clas')

    def form_valid(self, form):
        messages.success(self.request, "La sanción se registró correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear sanción'
        context['listar_url'] = reverse_lazy('gimnasio:listar_sanciones_clas')
        return context
    
class SancionesUpdateView(UpdateView):
    model = Sancion
    template_name = 'Sanciones/crear.html'
    form_class = SancionesForm
    success_url = reverse_lazy('gimnasio:listar_sanciones_clas')
    #@method_decorator(csrf_exempt)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Actualizar sancion'
        context['listar_url'] = reverse_lazy('gimnasio:listar_sanciones_clas')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Sanción editada correctamente")
        return super().form_valid(form)
class SancionesDeleteView(DeleteView):
    model = Sancion
    template_name = 'Sanciones/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_sanciones_clas')
    #@method_decorator(csrf_exempt)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar sancion'
        context['listar_url'] = reverse_lazy('gimnasio:listar_sanciones_clas')
        return context 
    
    def form_valid(self, form):
        messages.success(self.request, "Sanción eliminada correctamente")
        return super().form_valid(form)
