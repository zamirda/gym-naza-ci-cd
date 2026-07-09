from django.shortcuts import render, redirect
#from django.http import HttpResponse,JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages

from gimnasio.models import *
from gimnasio.forms import CategoriaForm

    
#Listar categorias
def listar_categorias(request):
    nombre ={
        'titulo':'Listado de Categorias',
        'categorias': Categoria.objects.all()
    }
    return render(request,'categoria/listar.html', nombre)

class categoriaListView(ListView):
    model = Categoria
    template_name = 'Categoria/listar.html'
    
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
        context['titulo'] = 'Listado de Categorias'
        context['crear_url'] = reverse_lazy('gimnasio:crear_categoria')
        return context

#Crear categoria    
class CategoriaCreateView(CreateView):
    model = Categoria
    template_name = 'Categoria/crear.html'
    form_class = CategoriaForm
    success_url = reverse_lazy('gimnasio:listar_categorias')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Categoria'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "La categoría se guardó correctamente")
        return super().form_valid(form)
    
    
class CategoriaUpdateView(UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'Categoria/crear.html'
    success_url = reverse_lazy('gimnasio:listar_categorias')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'editar Categoria'
        context['listar_url'] = reverse_lazy('gimnasio:listar_categorias')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "La categoría se editó correctamente")
        return super().form_valid(form)
    
class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'Categoria/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_categorias')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar Categoria'
        context['listar_url'] = reverse_lazy('gimnasio:listar_categorias')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "La categoría se eliminó correctamente")
        return super().form_valid(form)