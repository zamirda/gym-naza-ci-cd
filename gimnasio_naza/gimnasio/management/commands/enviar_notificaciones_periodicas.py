"""
Management command para enviar notificaciones periódicas:
- Membresías próximas a vencer (7 días antes)
- Inasistencias después de 7 días sin registrar asistencia

Ejecutar con: python manage.py enviar_notificaciones_periodicas
Para programar con cron: 0 8 * * * cd /ruta/proyecto && python manage.py enviar_notificaciones_periodicas
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from gimnasio.models import Usuario, Membresia, Asistencia, Notificacion
from gimnasio.utilities.notificaciones import NotificacionManager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envía notificaciones periódicas de membresías próximas a vencer e inasistencias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias-vencimiento',
            type=int,
            default=7,
            help='Días antes del vencimiento para enviar notificación (default: 7)'
        )
        parser.add_argument(
            '--dias-inasistencia',
            type=int,
            default=7,
            help='Días sin asistencia para notificar (default: 7)'
        )

    def handle(self, *args, **options):
        dias_vencimiento = options['dias_vencimiento']
        dias_inasistencia = options['dias_inasistencia']
        
        self.stdout.write(self.style.SUCCESS('Iniciando envío de notificaciones periódicas...'))
        
        # Notificar membresías próximas a vencer
        self.notificar_membresias_proximas_a_vencer(dias_vencimiento)
        
        # Notificar inasistencias
        self.notificar_inasistencias(dias_inasistencia)
        
        self.stdout.write(self.style.SUCCESS('✓ Notificaciones periódicas enviadas exitosamente'))

    def notificar_membresias_proximas_a_vencer(self, dias=7):
        """
        Notifica a usuarios cuya membresía está próxima a vencer.
        """
        try:
            hoy = timezone.now().date()
            fecha_limite = hoy + timedelta(days=dias)
            fecha_inicio = hoy
            
            # Buscar membresías activas que vencen en los próximos 'dias' días
            membresias = Membresia.objects.filter(
                estado='activo',
                fecha_fin__gte=fecha_inicio,
                fecha_fin__lte=fecha_limite
            )
            
            notificadas = 0
            
            for membresia in membresias:
                usuario = membresia.fk_usuario
                
                if not usuario.correo_usuario:
                    continue
                
                # Verificar si ya se envió una notificación para esta membresía
                notificacion_existente = Notificacion.objects.filter(
                    tipo_notificacion='MEMBRESIA',
                    fk_usuario=usuario,
                    estado_notificacion='ASIGNADA',
                    descripcion__contains='Alerta de vencimiento'
                ).exists()
                
                if notificacion_existente:
                    continue
                
                try:
                    dias_faltantes = (membresia.fecha_fin - hoy).days
                    
                    # Usar el NotificacionManager centralizado
                    exito, notif = NotificacionManager.enviar_alerta_vencimiento(
                        membresia, 
                        dias_faltantes
                    )
                    
                    if exito:
                        notificadas += 1
                    
                except Exception as e:
                    logger.error(f"Error enviando notificación a {usuario.nombre_usuario}: {e}")
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ {notificadas} notificaciones de vencimiento enviadas')
            )
            
        except Exception as e:
            logger.error(f"Error en notificaciones de membresía: {e}")
            self.stdout.write(self.style.ERROR(f'✗ Error: {e}'))

    def notificar_inasistencias(self, dias=7):
        """
        Notifica a usuarios que no han asistido en los últimos 'dias' días.
        """
        try:
            hoy = timezone.now().date()
            fecha_limite = hoy - timedelta(days=dias)
            
            # Obtener todos los usuarios con membresía activa
            usuarios_activos = Usuario.objects.filter(
                estado='activo',
                membresia__estado='activo'
            ).distinct()
            
            notificadas = 0
            
            for usuario in usuarios_activos:
                if not usuario.correo_usuario:
                    continue
                
                # Verificar si tiene asistencias en los últimos 'dias' días
                ultima_asistencia = Asistencia.objects.filter(
                    fk_membresia__fk_usuario=usuario
                ).order_by('-fecha_asistencia').first()
                
                # Si no tiene asistencia o la última fue hace más de 'dias' días
                if not ultima_asistencia or ultima_asistencia.fecha_asistencia < fecha_limite:
                    
                    # Verificar si ya se envió una notificación de inasistencia
                    notificacion_existente = Notificacion.objects.filter(
                        tipo_notificacion='ASISTENCIA',
                        fk_usuario=usuario,
                        estado_notificacion='ASIGNADA'
                    ).exists()
                    
                    if notificacion_existente:
                        continue
                    
                    try:
                        dias_sin_asistencia = (hoy - ultima_asistencia.fecha_asistencia).days if ultima_asistencia else dias
                        
                        # Usar el NotificacionManager centralizado
                        exito, notif = NotificacionManager.enviar_alerta_inasistencia(
                            usuario,
                            dias_sin_asistencia,
                            ultima_asistencia.fecha_asistencia if ultima_asistencia else None
                        )
                        
                        if exito:
                            notificadas += 1
                        
                    except Exception as e:
                        logger.error(f"Error enviando notificación de inasistencia a {usuario.nombre_usuario}: {e}")
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ {notificadas} notificaciones de inasistencia enviadas')
            )
            
        except Exception as e:
            logger.error(f"Error en notificaciones de inasistencia: {e}")
            self.stdout.write(self.style.ERROR(f'✗ Error: {e}'))
