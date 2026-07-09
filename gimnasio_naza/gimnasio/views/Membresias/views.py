import json
import calendar
from datetime import date, datetime, timedelta
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import Count
from django.db.models.functions import TruncMonth

from gimnasio.models import *
from gimnasio.forms import MembresiaForm


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
            fecha_nacimiento = datetime.strptime(
                data['fecha_nacimiento'], "%Y-%m-%d"
            ).date()
        else:
            fecha_nacimiento = date(2000, 1, 1)

        peso = float(data.get('peso') or 0)
        altura = float(data.get('altura') or 0)
        password = data.get('password') or "123456"

        user = User.objects.create(
            username=data['username'],
            email=data.get('correo', '')
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

        return JsonResponse({
            'id': usuario.id,
            'nombre': f"{usuario.nombre_usuario} {usuario.apellido_usuario}"
        })

    except Exception as e:
        return JsonResponse({'error': str(e)})


class MembresiaListView(ListView):
    model = Membresia
    template_name = 'Membresia/listar.html'
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['titulo'] = 'Listado de membresias'
        context['crear_url'] = reverse_lazy('gimnasio:crear_membresia')

        # ========== GRÁFICO DONUT - ESTADOS ==========
        activas = Membresia.objects.filter(estado='activo').count()
        vencidas = Membresia.objects.filter(estado='inactivo').count()

        context['total_membresias'] = activas + vencidas
        context['chart_labels'] = json.dumps(['Activas', 'Vencidas'])
        context['chart_data'] = json.dumps([activas, vencidas])

        # ========== GRÁFICO BARRAS - MEMBRESÍAS POR MES ==========
        hoy = date.today()  # ✅ Sin depender de timezone
        inicio_periodo = hoy - timedelta(days=365)

        membresias_por_mes = (
            Membresia.objects.filter(fecha_inicio__gte=inicio_periodo)
            .annotate(mes=TruncMonth('fecha_inicio'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )

        meses_grafica = []
        totales_grafica = []

        fecha_actual = hoy.replace(day=1)

        for i in range(11, -1, -1):  # ✅ Orden cronológico ascendente
            mes_actual = fecha_actual - timedelta(days=30 * i)
            nombre_mes = calendar.month_abbr[mes_actual.month]
            meses_grafica.append(nombre_mes)

            total_mes = 0
            for item in membresias_por_mes:
                if (
                    item['mes']
                    and item['mes'].month == mes_actual.month
                    and item['mes'].year == mes_actual.year
                ):
                    total_mes = item['total']
                    break

            totales_grafica.append(int(total_mes))

        context['chart_labels_mensual'] = json.dumps(meses_grafica)
        context['chart_data_mensual'] = json.dumps(totales_grafica)

        return context


class MembresiaCreateView(CreateView):
    model = Membresia
    template_name = 'Membresia/crear.html'
    form_class = MembresiaForm
    success_url = reverse_lazy('gimnasio:listar_membresia')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear membresia'
        return context


class MembresiaUpdateView(UpdateView):
    model = Membresia
    template_name = 'Membresia/crear.html'
    form_class = MembresiaForm
    success_url = reverse_lazy('gimnasio:listar_membresia')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar membresia'
        context['listar_url'] = reverse_lazy('gimnasio:listar_membresia')
        return context


class MembresiaDeleteView(DeleteView):
    model = Membresia
    template_name = 'Membresia/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_membresia')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar membresia'
        context['listar_url'] = reverse_lazy('gimnasio:listar_membresia')
        return context


def send_email(request):
    subject = request.POST.get("subject", "")
    message = request.POST.get("message", "")
    from_email = request.POST.get("from_email", "")

    if subject and message and from_email:
        try:
            send_mail(
                subject,
                message,
                from_email,
                ["admin@example.com"]
            )
        except ValueError:
            return HttpResponse("Invalid header found.")

        return HttpResponseRedirect("/contact/thanks/")

    return HttpResponse("Make sure all fields are entered and valid.")