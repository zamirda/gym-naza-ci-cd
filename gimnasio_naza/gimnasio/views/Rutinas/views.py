from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from gimnasio.models import *
from gimnasio.forms import RutinaForm
from django.contrib.auth.models import User
from datetime import datetime,date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import transaction
from django.db import IntegrityError

@csrf_exempt
def wizard_crear_todo(request):
    if request.method == "POST":

        data = json.loads(request.body)
        try:
            with transaction.atomic():

                fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
                fecha_control = datetime.strptime(data['fecha_control'], '%Y-%m-%d').date()

                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password']
                )
                print(user)
                print("Creando Usuario")
                usuario = Usuario.objects.create(
                    user=user,
                    documento=data['documento'],
                    nombre_usuario=data['nombre'],
                    apellido_usuario=data['apellido'],
                    correo_usuario=data['correo'],
                    telefono_usuario=data['telefono'],
                    fecha_nacimiento=fecha_nacimiento,
                    peso_usuario=data['peso_usuario'],
                    altura_usuario=data['altura_usuario'],
                    genero_usuario=data['genero'],
                    estado='activo',
                    rol='cliente'
                )
                print(usuario)
                print("Creando nutricion")
                nutricion = Nutricion.objects.create(
                    nivel_actividad_fisica=data['nivel_actividad'],
                    objetivo_nutricional=data['tipo_objetivo'],
                    tipo_plan_alimenticio=data['tipo_dieta'],
                    fk_Usuario=usuario
                )
                print(nutricion)
                masa = Masa_corporal.objects.create(
                    peso_cliente=data['peso_cliente'],
                    altura_cliente=data['altura_cliente'],
                    fecha_control=fecha_control,
                    fk_Nutricion=nutricion
                )
                print(masa)
            return JsonResponse({
                "id": masa.id,
                "nombre": f"IMC {masa.id}"
            })
        except IntegrityError as e:
            error_msg = str(e).lower()
            

            errores_duplicados = {
                'documento': "El número de documento ya se encuentra registrado.",
                'username': "El nombre de usuario ya está en uso por otra persona.",
                'correo': "Este correo electrónico ya está registrado."
            }
            
            for campo, mensaje in errores_duplicados.items():
                if campo in error_msg:
                    return JsonResponse({"error": mensaje}, status=200)
            
            return JsonResponse({
                "error": "Ocurrió un conflicto de integridad al guardar los datos."
            }, status=200)
#Listar rutinas
def listar_rutinas(request):
    nombre ={
        'titulo':'Listado de Rutinas',
        'categorias': Rutina.objects.all()
    }
    return render(request,'rutina/listar.html', nombre)

class rutinaListView(ListView):
    model = Rutina
    template_name = 'Rutina/listar.html'
    
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
        context['titulo'] = 'Listado de Rutinas'
        context['crear_url'] = reverse_lazy('gimnasio:crear_rutina')

        return context
    
#Crear rutina   
class RutinaCreateView(CreateView):
    model = Rutina
    template_name = 'Rutina/crear.html'
    form_class = RutinaForm
    success_url = reverse_lazy('gimnasio:listar_rutinas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Rutina'
        context['nutriciones'] = Nutricion.objects.all()
        context['usuarios'] = Usuario.objects.all()  # 🔥 IMPORTANTE
        return context

    def form_valid(self, form):
        messages.success(self.request, "Rutina guardada correctamente")
        return super().form_valid(form)
    
class RutinaUpdateView(UpdateView):
    model = Rutina
    form_class = RutinaForm
    template_name = 'Rutina/crear.html'
    success_url = reverse_lazy('gimnasio:listar_rutinas')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Rutina'
        context['listar_url'] = reverse_lazy('gimnasio:listar_rutinas')
        return context

    def form_valid(self, form):
        messages.success(self.request, "La rutina se editó correctamente")
        return super().form_valid(form)
    
    
class RutinaDeleteView(DeleteView):
    model = Rutina
    template_name = 'Rutina/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_rutinas')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar Rutina'
        context['listar_url'] = reverse_lazy('gimnasio:listar_rutinas')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "La rutina se eliminó correctamente")
        return super().form_valid(form)