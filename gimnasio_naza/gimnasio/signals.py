from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from datetime import datetime, timedelta, timezone
from gimnasio.models import Usuario, Membresia, Notificacion, Mantenimiento, Notificacion, Asistencia
from gimnasio.utilities.notificaciones import NotificacionManager
from gimnasio.utilities.calcular_dias import calcular_dias, calcular_dias_restantes, buscar_mantenimiento
import logging

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def create_grupos(sender, **kwargs):
    """
    Crea los grupos de usuarios (Administrador y Cliente) después de las migraciones.
    """
    grupos = ['Administrador', 'Cliente']
    for grupo in grupos:
        g, created = Group.objects.get_or_create(name=grupo)
        if g.name == 'Administrador':
            g.permissions.set(Permission.objects.all())
        elif g.name == 'Cliente':
            g.permissions.set(Permission.objects.filter(codename__in=[
                'add_usuario',
                'change_usuario',
                'view_usuario',
                'delete_usuario',
            ]))
        g.save()

@receiver(post_save, sender=Usuario)
def asignar_grupo_por_rol(sender, instance, **kwargs):
    """
    Asigna un grupo al usuario según el rol y sincroniza los permisos.
    """
    if instance.user and instance.rol:
        grupo, _ = Group.objects.get_or_create(name=instance.rol)
        if grupo.name == 'Administrador':
            grupo.permissions.set(Permission.objects.all())
        elif grupo.name == 'Cliente':
            grupo.permissions.set(Permission.objects.filter(codename__in=[
                'add_usuario',
                'change_usuario',
                'view_usuario',
                'delete_usuario',
            ]))
        grupo.save()
        instance.user.groups.set([grupo])

@receiver(post_save, sender=Usuario)
def enviar_correo_bienvenida(sender, instance, created, **kwargs):
    """
    Envía un correo de bienvenida cuando se crea una nueva cuenta.
    """
    if created:
        try:
            NotificacionManager.enviar_bienvenida(instance)
            logger.info(f"✓ Correo de bienvenida enviado a {instance.nombre_usuario}")
        except Exception as e:
            logger.error(f"Error enviando correo de bienvenida: {e}")

@receiver(post_save, sender=Membresia)
def notificar_cambio_membresia(sender, instance, created, **kwargs):
    """
    Envía notificación cuando cambia el estado de una membresía o se crea una nueva.
    Este es el ÚNICO punto donde se envía la confirmación de membresía nueva,
    ya sea creada manualmente o desde crear_membresia_auto.
    """
    usuario = instance.fk_usuario
    if created:
        # Nueva membresía creada
        try:
            NotificacionManager.enviar_confirmacion_membresia(instance)
            logger.info(f"✓ Confirmación de membresía enviada a {usuario.nombre_usuario}")
        except Exception as e:
            logger.error(f"Error notificando nueva membresía: {e}")

    else:
        # Cambio de estado de membresía
        try:
            if instance.estado == 'inactivo':
                NotificacionManager.enviar_notificacion_vencida(instance)
                logger.info(f"✓ Notificación de vencimiento enviada a {usuario.nombre_usuario}")
        except Exception as e:
            logger.error(f"Error notificando cambio de membresía: {e}")

@receiver(post_save, sender=Mantenimiento)
def notificar_mantenimiento(sender, instance, created, **kwargs):
    """
    Notifica a los usuarios cuando hay un mantenimiento programado.
    """
    if created:
        try:
            # Notificar a todos los usuarios activos
            usuarios = Usuario.objects.filter(estado='activo')
            if usuarios.exists():
                NotificacionManager.enviar_notificacion_mantenimiento(usuarios, instance)
                logger.info(f"✓ Notificaciones de mantenimiento enviadas a {usuarios.count()} usuarios")
        except Exception as e:
            logger.error(f"Error notificando mantenimiento: {e}")


@receiver(post_save, sender=Notificacion)
def notificar(sender, instance, created, **kwargs):
    if created:
        try:
            notificaciones = instance.tipo_notificacion
            print(instance.detalle_notificacion)
            membresia = Membresia.objects.filter(fk_usuario=instance.fk_usuario).first()
            if notificaciones == 'MEMBRESIA':
                if instance.detalle_notificacion == 'Bienvenida':
                    NotificacionManager.enviar_bienvenida(instance.fk_usuario)
                elif instance.detalle_notificacion == 'Membresía_activada':
                    NotificacionManager.enviar_confirmacion_membresia(membresia)
                elif instance.detalle_notificacion == 'Membresía_vencida':
                    NotificacionManager.enviar_notificacion_vencida(membresia)
                else:
                    NotificacionManager.enviar_alerta_vencimiento(membresia, calcular_dias_restantes(instance.fk_usuario))
            elif notificaciones == 'MANTENIMIENTO':
                NotificacionManager.enviar_notificacion_mantenimiento(instance.fk_usuario, buscar_mantenimiento())
            else:
                usuario = instance.fk_usuario
                NotificacionManager.enviar_alerta_inasistencia(usuario, calcular_dias(usuario))
        except Exception as e:
            logger.error(f"Error notificando: {e}")


@receiver(post_save, sender=Usuario)
def crear_membresia_auto(sender, instance, created, **kwargs):
    """
    Crea automáticamente una membresía cuando se registra un usuario con rol Cliente.
    La notificación de confirmación NO se envía aquí: la dispara automáticamente
    el signal post_save de Membresia (notificar_cambio_membresia) al hacer .create().
    """
    if instance.rol == 'Cliente' and created:
        try:
            membresia = Membresia.objects.create(
                fk_usuario=instance,
                fecha_inicio=datetime.now(),
                fecha_fin=datetime.now() + timedelta(days=30),
                estado='activo'
            )
            logger.info(f"Membresía creada automáticamente para {instance.nombre_usuario}")


        except Exception as e:
            logger.error(f"Error creando membresía automática: {e}")