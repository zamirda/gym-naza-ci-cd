from django.shortcuts import render, redirect
import json
from datetime import datetime, date
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy

from gimnasio.models import *
from gimnasio.forms import AsistenciaForm
from gimnasio.utilities.notificaciones import NotificacionManager  # <-- AJUSTA esta ruta a donde tengas el módulo real

from datetime import datetime, date


def crear_membresia_ajax(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    fk_usuario_id = data.get('fk_usuario')
    fecha_inicio = data.get('fecha_inicio')
    fecha_fin = data.get('fecha_fin')
    estado = data.get('estado')

    if not fk_usuario_id or not fecha_inicio or not fecha_fin or not estado:
        return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)

    try:
        usuario = Usuario.objects.get(pk=fk_usuario_id)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'El usuario indicado no existe'}, status=400)

    try:
        with transaction.atomic():
            membresia = Membresia.objects.create(
                fk_usuario=usuario,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado=estado,
            )

            # El correo con el QR solo se envía si la transacción
            # se confirma correctamente (evita enviar correo de una
            # membresía que termina siendo revertida).
            transaction.on_commit(
                lambda: NotificacionManager.enviar_confirmacion_membresia(membresia)
            )

        return JsonResponse({
            'id': membresia.id,
            'nombre': f"{usuario.nombre_usuario} {usuario.apellido_usuario}"
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



@csrf_exempt
def wizard_asistencia(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    # ---------- VALIDACIÓN DE CAMPOS OBLIGATORIOS ----------
    campos_obligatorios = ['username', 'password', 'documento', 'nombre_usuario']
    faltantes = [c for c in campos_obligatorios if not data.get(c, '').strip() if isinstance(data.get(c), str)]
    if faltantes:
        return JsonResponse({'error': f"Faltan campos obligatorios: {', '.join(faltantes)}"}, status=400)

    username = data['username'].strip()
    documento = data['documento'].strip()
    correo = (data.get('correo_usuario') or '').strip()

    # ---------- VALIDACIÓN DE DUPLICADOS (esto evita el error 1062) ----------
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': f"El usuario '{username}' ya está registrado."}, status=400)

    if Usuario.objects.filter(documento=documento).exists():
        return JsonResponse({'error': f"El documento '{documento}' ya está registrado."}, status=400)

    if correo and Usuario.objects.filter(correo_usuario=correo).exists():
        return JsonResponse({'error': f"El correo '{correo}' ya está registrado."}, status=400)

    # ---------- CONVERSIÓN/VALIDACIÓN DE FECHAS Y NÚMEROS ----------
    try:
        fecha_nacimiento_str = data.get('fecha_nacimiento') or None
        fecha_inicio_str = data.get('fecha_inicio') or None
        fecha_fin_str = data.get('fecha_fin') or None

        # Conversión explícita de string -> date.
        # Sin esto, Membresia.fecha_inicio/fecha_fin quedan como str en
        # memoria (aunque en la BD se guarden bien), y cualquier código
        # que después llame a .strftime() sobre esos campos (como el
        # correo de confirmación) explota con:
        # "El objeto 'str' no tiene el atributo 'strftime'".
        fecha_nacimiento = (
            datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            if fecha_nacimiento_str else None
        )
        fecha_inicio = (
            datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            if fecha_inicio_str else None
        )
        fecha_fin = (
            datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            if fecha_fin_str else None
        )

        peso = float(data['peso_usuario']) if data.get('peso_usuario') not in (None, '') else None
        altura = float(data['altura_usuario']) if data.get('altura_usuario') not in (None, '') else None
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Datos numéricos o de fecha inválidos.'}, status=400)

    if not fecha_nacimiento:
        return JsonResponse({'error': 'La fecha de nacimiento es obligatoria.'}, status=400)
    if not fecha_inicio or not fecha_fin:
        return JsonResponse({'error': 'Las fechas de membresía son obligatorias.'}, status=400)
    if peso is None or altura is None:
        return JsonResponse({'error': 'El peso y la altura son obligatorios.'}, status=400)

    # ---------- CREACIÓN ATÓMICA: si algo falla, se revierte todo ----------
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                password=data['password'],
                email=correo,
            )

            usuario = Usuario.objects.create(
                user=user,
                documento=documento,
                nombre_usuario=data['nombre_usuario'].strip(),
                apellido_usuario=(data.get('apellido_usuario') or '').strip(),
                correo_usuario=correo,
                telefono_usuario=(data.get('telefono_usuario') or '').strip(),
                fecha_nacimiento=fecha_nacimiento,
                peso_usuario=peso,
                altura_usuario=altura,
                genero_usuario=data.get('genero_usuario') or 'M',
                rol='Cliente',
                estado='activo',
            )

            membresia = Membresia.objects.create(
                fk_usuario=usuario,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado=data.get('estado_membresia') or 'activo',
            )

            # ---------- ENVÍO DE CORREO CON QR ----------
            # Se difiere con on_commit para que el correo solo se envíe
            # si TODO el registro (user + usuario + membresia) se confirmó
            # con éxito. Si el envío de correo falla, no afecta el registro
            # porque ya ocurre fuera de la transacción.
            #
            # IMPORTANTE: si esto falla, el usuario/membresía YA quedaron
            # guardados (porque on_commit corre después del commit), así
            # que atrapamos el error aquí para no romper la respuesta JSON
            # con un error que en realidad no afectó el registro.
            def _enviar_correo_membresia():
                try:
                    NotificacionManager.enviar_confirmacion_membresia(membresia)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(
                        f"No se pudo enviar el correo de confirmación de membresía {membresia.id}: {e}"
                    )

            transaction.on_commit(_enviar_correo_membresia)

        return JsonResponse({
            'id': membresia.id,
            'nombre': f"{usuario.nombre_usuario} {usuario.apellido_usuario}"
        })

    except IntegrityError as e:
        # Captura cualquier duplicado que se nos haya escapado (carrera entre
        # validación y guardado), en vez de dejar pasar el error crudo de MySQL.
        return JsonResponse({'error': f'Ya existe un registro con esos datos: {str(e)}'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# ---------- LISTAR ASISTENCIA ----------
def Listar_asistencia(request):
    contexto = {
        'titulo': 'Listado de Asistencias',
        'asistencias': Asistencia.objects.all()
    }
    return render(request, 'Asistencia/listar.html', contexto)


class AsistenciaListView(ListView):
    model = Asistencia
    template_name = 'Asistencia/listar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Listado de asistencias'
        context['crear_url'] = reverse_lazy('gimnasio:crear_asistencia')
        return context


class AsistenciaCreateView(CreateView):
    model = Asistencia
    template_name = 'Asistencia/crear.html'
    form_class = AsistenciaForm
    success_url = reverse_lazy('gimnasio:listar_asistencia')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear asistencia'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Asistencia creada correctamente")
        return super().form_valid(form)


class AsistenciaUpdateView(UpdateView):
    model = Asistencia
    template_name = 'Asistencia/crear.html'
    success_url = reverse_lazy('gimnasio:listar_asistencia')
    form_class = AsistenciaForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Asistencia'
        context['listar_url'] = reverse_lazy('gimnasio:listar_asistencia')
        return context

    def form_valid(self, form):
        messages.success(self.request, "Asistencia editada correctamente")
        return super().form_valid(form)


class AsistenciaDeleteView(DeleteView):
    model = Asistencia
    template_name = 'Asistencia/eliminar.html'
    success_url = reverse_lazy('gimnasio:listar_asistencia')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Eliminar Asistencia'
        context['listar_url'] = reverse_lazy('gimnasio:listar_asistencia')
        return context

    def form_valid(self, form):
        messages.success(self.request, "Asistencia eliminada correctamente")
        return super().form_valid(form)


class QR_register(View):
    def get(self, request):
        return render(request, 'Asistencia/listar.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 400, 'mensaje': 'JSON inválido'}, status=400)

        qr_code = data.get('codigo')
        if not qr_code:
            return JsonResponse({'status': 400, 'mensaje': 'Código no enviado'}, status=400)

        try:
            membresia = Membresia.objects.filter(
                fk_usuario__documento=qr_code, estado='activo'
            ).first()

            if not membresia:
                return JsonResponse({
                    'status': 404,
                    'mensaje': 'NO TIENE MEMBRESÍA ACTIVA ESTE USUARIO'
                }, status=404)

            hoy = date.today()
            if Asistencia.objects.filter(fk_membresia=membresia, fecha_asistencia=hoy).exists():
                return JsonResponse({
                    'status': 409,
                    'mensaje': f'{membresia.fk_usuario.nombre_usuario} ya registró asistencia hoy'
                })

            Asistencia.objects.create(
                fk_membresia=membresia,
                fecha_asistencia=hoy,
                hora_ingreso=timezone.now().time()
            )
            return JsonResponse({
                'status': 200,
                'mensaje': f'Asistencia registrada para {membresia.fk_usuario.nombre_usuario}'
            })

        except Exception as e:
            return JsonResponse({'status': 500, 'mensaje': f'Error: {str(e)}'}, status=500)