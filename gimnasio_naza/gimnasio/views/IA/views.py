# gimnasio/views/IA/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
from gimnasio.models import Usuario, Nutricion, Masa_corporal, Rutina
from gimnasio.servicios.ia_engine import MotorRecomendacionGym

@login_required
@login_required
def seleccion_plan_ia(request, usuario_id):
    # Intentamos buscar el perfil usando el id del 'User' de Django que viaja en la URL
    try:
        usuario = Usuario.objects.get(user_id=usuario_id)
    except Usuario.DoesNotExist:
        # Si no lo encuentra por el ID de la URL, usamos al usuario que tiene la sesión activa de respaldo
        usuario = get_object_or_404(Usuario, user=request.user)
    
    # Inicializar el motor predictivo de IA
    motor_ia = MotorRecomendacionGym()
    
    # Generar las dos propuestas basadas en el ID del perfil real
    planes = motor_ia.generar_recomendaciones(usuario.id)
    
    if request.method == 'POST':
        opcion_elegida = request.POST.get('opcion_elegida')
        
        # 1. Mapear las recomendaciones del diccionario de la IA a las opciones estrictas (choices) del modelo
        if opcion_elegida == 'opcion_2':
            # Enfoque de Fuerza / Hipertrofia
            nivel_act = "alto"
            obj_nutricional = "ganar_masa"
            tipo_dieta = "hiperproteica"
            tipo_rut = "FUERZA"
            dist_rutina = "SUPERIOR"
        else:
            # Enfoque Funcional / Mantenimiento básico
            nivel_act = "medio"
            obj_nutricional = "mantener"
            tipo_dieta = "balanceada"
            tipo_rut = "FUNCIONAL"
            dist_rutina = "COMPLETA"
            
        # 2. Instanciar el objeto Nutricion respetando las columnas de la base de datos fk_Usuario 
        nueva_nutricion = Nutricion.objects.create(
            nivel_actividad_fisica=nivel_act,
            objetivo_nutricional=obj_nutricional,
            tipo_plan_alimenticio=tipo_dieta,
            fk_Usuario=usuario
        )
        
        # 3. Calcular la clasificación del IMC para registrar el historial de control de Masa_corporal
        imc_valor = planes['metricas']['imc']
        if imc_valor < 18.5:
            estado_imc_str = "Bajo peso"
        elif 18.5 <= imc_valor < 25.0:
            estado_imc_str = "Normal"
        elif 25.0 <= imc_valor < 30.0:
            estado_imc_str = "Sobrepeso"
        else:
            estado_imc_str = "Obesidad"

        nuevo_control_imc = Masa_corporal.objects.create(
            peso_cliente=usuario.peso_usuario,
            altura_cliente=usuario.altura_usuario,
            fecha_control=date.today(),
            fk_Nutricion=nueva_nutricion,
            imc=float(imc_valor),
            estado_imc=estado_imc_str
        )
        
        # 4. Instanciar la Rutina acoplada obligatoriamente al control de Masa_corporal recién creado (fk_imc)
        nueva_rutina = Rutina.objects.create(
            tipo_rutina=tipo_rut,
            dias_disponibles=int(planes['metricas']['asistencia_proyectada']),
            distribucion_rutina=dist_rutina,
            fk_imc=nuevo_control_imc
        )
        
        # Enviar alerta flash de confirmación de SweetAlert y redirigir al espacio de trabajo principal
        messages.success(request, "¡Tu plan personalizado con IA ha sido generado y asignado con éxito!")
        return redirect('usuarios:dashboard_usuario')
        
    contexto = {
        'planes': planes,
        'usuario_objetivo': usuario,
        'titulo': 'Generación de Plan con IA'
    }
    
    return render(request, 'IA/generacion_ia.html', contexto)