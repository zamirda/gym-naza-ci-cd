from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from gimnasio.models import Mantenimiento, Elemento, Categoria
from gimnasio.forms import MantenimientoForm
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import transaction
from django.utils import timezone

@csrf_exempt
@require_POST
def crear_categoria_ajax(request):
    import json
    from gimnasio.models import Categoria

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    nombre_categoria = data.get('nombre_categoria', '').strip()
    descripcion      = data.get('descripcion', '').strip()

    if not nombre_categoria or not descripcion:
        return JsonResponse({'error': 'Todos los campos son obligatorios'}, status=400)

    categoria = Categoria.objects.create(
        nombre_categoria=nombre_categoria,
        descripcion=descripcion
    )

    return JsonResponse({
        "id": categoria.id,
        "nombre": categoria.nombre_categoria,
    })

@csrf_exempt
def obtener_elementos_por_categoria(request):
    """Vista AJAX para obtener elementos filtrados por categoría"""
    categoria_valor = request.GET.get('categoria_id')
    if not categoria_valor:
        return JsonResponse({'error': 'No se proporcionó categoría'}, status=400)
    
    try:
        # Buscar categoría por valor (maquinas, mancuernas, etc.)
        categoria = Categoria.objects.filter(nombre_categoria=categoria_valor).first()
        if not categoria:
            return JsonResponse({'error': 'Categoría no encontrada'}, status=404)
        
        elementos = Elemento.objects.filter(nombre_categoria=categoria, estado='M')
        
        elementos_list = []
        for elem in elementos:
            elementos_list.append({
                'id': elem.id,
                'nombre': elem.nombre_elemento,
                'serial': elem.serial,
                'marca': elem.marca,
                'peso': elem.peso_elemento
            })
        
        return JsonResponse({'elementos': elementos_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST

def crear_elemento_ajax(request):
    try:
        with transaction.atomic():
            serial = request.POST.get('serial')
            marca = request.POST.get('marca')
            nombre = request.POST.get('nombre')
            peso = request.POST.get('peso')
            unidad_peso = request.POST.get('unidad_peso')
            estado = request.POST.get('estado')
            categoria_valor = request.POST.get('categoria')
            cantidad = request.POST.get('cantidad')
            foto = request.FILES.get('foto')
            if not all([serial, marca, nombre, peso, estado, categoria_valor, cantidad]):
                return JsonResponse({'error': 'Todos los campos son obligatorios'}, status=400)
            
            # Buscar categoría por valor (maquinas, mancuernas, etc.)
            categoria = Categoria.objects.get(nombre_categoria=categoria_valor)        
            elemento = Elemento.objects.create(
                serial=serial,
                marca=marca,
                nombre_elemento=nombre,
                peso_elemento=peso,
                unidad_peso=unidad_peso,
                estado=estado,
                fecha_ingreso=fecha_compra,
                nombre_categoria=categoria,
                cantidad=cantidad,
                imagen=foto
            )
            return JsonResponse({
                'id': elemento.id,
                'nombre': elemento.nombre_elemento,
                'serial': elemento.serial,
                'categoria': elemento.nombre_categoria.nombre_categoria,
            })
    except Categoria.DoesNotExist:
        return JsonResponse({'error': 'Categoría no encontrada'}, status=404)
    except Exception as e:
        print("Error al crear elemento:", str(e))
        return JsonResponse({'error': str(e)}, status=500)

class MantenimientoListView(ListView):
    model = Mantenimiento
    template_name = 'Mantenimiento/listar.html'
    context_object_name = 'mantenimientos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["crear_url"] = reverse_lazy('gimnasio:crear_mantenimiento')
        context['completados'] = Mantenimiento.objects.filter(estado='Completado').count()
        context['pendientes'] = Mantenimiento.objects.filter(estado='Pendiente').count()
        context['en_proceso'] = Mantenimiento.objects.filter(estado='En Proceso').count()
        context['total_mantenimientos'] = Mantenimiento.objects.count() 
        return context

class MantenimientoCreateView(CreateView):
    model = Mantenimiento
    form_class = MantenimientoForm
    template_name = 'Mantenimiento/crear.html'
    success_url = reverse_lazy('gimnasio:listar_mantenimiento')

    def get_initial(self):
        initial = super().get_initial()
        elemento_id = self.request.GET.get('elemento')
        if elemento_id:
            try:
                initial['elemento'] = Elemento.objects.get(pk=elemento_id)
            except Elemento.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Mantenimiento'
        elemento_id = self.request.GET.get('elemento')
        if elemento_id:
            context['elemento_pre'] = Elemento.objects.filter(pk=elemento_id).first()
        context['categorias'] = Categoria.objects.all()
        print("Categorías en contexto:", context['categorias'])
        return context

class MantenimientoUpdateView(UpdateView):
    model = Mantenimiento
    form_class = MantenimientoForm
    template_name = 'Mantenimiento/crear.html'
    success_url = reverse_lazy('gimnasio:listar_mantenimiento')

class MantenimientoDeleteView(DeleteView):
    model = Mantenimiento
    template_name = 'Mantenimiento/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_mantenimiento')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar Mantenimiento'
        return context