from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from gimnasio.models import Registrovisitantestemporales
from gimnasio.forms import RegistrovisitantetemporalForm
from django.contrib import messages
from gimnasio.models import Usuario,Membresia
from  django.contrib.auth.models import User
import json
from datetime import date, datetime
from django.db.models import Count
from django.utils import timezone
from django.shortcuts import redirect

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

class RegistrovisitantetemporalListView(ListView):
    model = Registrovisitantestemporales
    template_name = 'registrovisitantetemporal/listar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        visitantes = (
            Registrovisitantestemporales.objects
            .values('fecha_registro')
            .annotate(total=Count('id'))
            .order_by('fecha_registro')
        )

        labels = []
        datos = []
        detalle = {}

        for v in visitantes:
            fecha = v['fecha_registro'].strftime("%d/%m/%Y")
            labels.append(fecha)
            datos.append(v['total'])

            registros = Registrovisitantestemporales.objects.filter(
                fecha_registro=v['fecha_registro']
            )

            detalle[fecha] = [
                f"{r.nombre} - {r.cedula}"
                for r in registros
            ]

        context['labels_estadisticas'] = json.dumps(labels)
        context['datos_estadisticas'] = json.dumps(datos)
        context['detalle_visitantes'] = json.dumps(detalle)

        return context


class RegistrovisitantestemporalCreateView(CreateView):
    model = Registrovisitantestemporales
    form_class = RegistrovisitantetemporalForm
    template_name = 'registrovisitantetemporal/crear.html'
    success_url = reverse_lazy('gimnasio:listar_registrovisitante')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear registro visitante'
        return context

    def form_valid(self, form):
        form.instance.fecha_registro = timezone.now().date()
        form.save()

        messages.success(
            self.request,
            "Registro de visitante creado correctamente"
        )

        return redirect('gimnasio:listar_registrovisitante')



class RegistrovisitantetemporalUpdateView(UpdateView):
    model = Registrovisitantestemporales
    form_class = RegistrovisitantetemporalForm
    template_name = 'registrovisitantetemporal/crear.html'
    success_url = reverse_lazy('gimnasio:listar_registrovisitante')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar registro visitante'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Actualizacion de registro visitante actualizado correctamente')
        return super().form_valid(form)
    
    
class RegistrovisitantetemporalDeleteView(DeleteView):
    model = Registrovisitantestemporales
    template_name = 'registrovisitantetemporal/eliminar.html'
    success_url = reverse_lazy('gimnasio:eliminar_registrovisitante')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar registro visitante'
        context['listar_url'] = reverse_lazy('gimnasio:listar_registrovisitante')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Registro de visitante eliminado correctamente")
        return super().form_valid(form)
