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
from gimnasio.forms import Masa_muscularForm
from django.contrib import messages
import json

@csrf_exempt
def crear_nutricion_ajax(request):
    import json

    data = json.loads(request.body)
    try:
        nutricion = Nutricion.objects.create(
            nivel_actividad_fisica=data['nivel_actividad'],
            objetivo_nutricional=data['tipo_objetivo'],
            tipo_plan_alimenticio=data['tipo_dieta'],
            fk_Usuario_id=data['fk_usuario']
        )

        return JsonResponse({
            'id': nutricion.id,
            'nombre': f" {nutricion.id} - {nutricion.fk_Usuario.nombre_usuario} - {nutricion.fk_Usuario.documento}"
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

#Listar asistencia 
def Listar_masa_corporal(request):
    nombre ={
        'titulo':'Listado de Masa Muscular',
        'masa_muscular': Masa_corporal.objects.all()
    }
    return render(request,'Masa_muscular/listar.html', nombre)

class Masa_corporalListView(ListView):
    model = Masa_corporal
    template_name = 'masa_muscular/listar.html'
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
        context['titulo'] = 'Listado de masa corporal'
        context['crear_url'] = reverse_lazy('gimnasio:crear_masa_corporal')
        return context


class Masa_corporalCreateView(CreateView):

    model = Masa_corporal
    template_name = 'masa_muscular/crear.html'
    form_class = Masa_muscularForm
    success_url = reverse_lazy('gimnasio:listar_masa_corporal_clas')

    def form_valid(self, form):

        peso = float(form.instance.peso_cliente)
        altura = float(form.instance.altura_cliente)

        imc = peso / (altura * altura)

        # Clasificación IMC
        if imc < 18.5:
            estado = "Bajo peso"

        elif imc < 25:
            estado = "Normal"

        elif imc < 30:
            estado = "Sobrepeso"

        else:
            estado = "Obesidad"

        # Guardar
        form.instance.imc = round(imc, 2)
        form.instance.estado_imc = estado

        messages.success(
            self.request,
            "Registro corporal guardado correctamente"
        )

        return super().form_valid(form)
    
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear masa corporal'
        #Usuarios filtrados por membresia activa
        print(Usuario.objects.filter(membresia__estado = 'Activo'))
        context['usuarios'] = Usuario.objects.filter(membresia__estado = 'Activo')
        print("Usuarios en contexto:", context['usuarios'])
        return context
class Masa_corporalUpdateView(UpdateView):
    model = Masa_corporal
    template_name = 'masa_muscular/crear.html'
    form_class = Masa_muscularForm
    success_url = reverse_lazy('gimnasio:listar_masa_corporal_clas')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Actualizar masa corporal'
        context['listar_url'] = reverse_lazy('gimnasio:listar_masa_corporal_clas')
        return context
    def form_valid(self, form):

        peso = float(form.instance.peso_cliente)
        altura = float(form.instance.altura_cliente)

        imc = peso / (altura * altura)

        # Clasificación IMC
        if imc < 18.5:
            estado = "Bajo peso"

        elif imc < 25:
            estado = "Normal"

        elif imc < 30:
            estado = "Sobrepeso"

        else:
            estado = "Obesidad"

        # Guardar
        form.instance.imc = round(imc, 2)
        form.instance.estado_imc = estado

        messages.success(
            self.request,
            "Registro corporal guardado correctamente"
        )

        return super().form_valid(form)
class Masa_corporalDeleteView(DeleteView):
    model = Masa_corporal
    template_name = 'masa_muscular/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_masa_corporal_clas')
    #@method_decorator(csrf_exempt)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar masa corporal'
        context['listar_url'] = reverse_lazy('gimnasio:listar_masa_corporal_clas')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Masa corporal eliminada correctamente")
        return super().form_valid(form)