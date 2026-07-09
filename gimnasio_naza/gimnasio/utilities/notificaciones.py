"""
Módulo de utilidades para envío de notificaciones por correo.

Este módulo proporciona funciones centralizadas para enviar diferentes tipos
de notificaciones a los usuarios del gimnasio.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from gimnasio.models import Notificacion
import logging
from django.core.mail import EmailMultiAlternatives
logger = logging.getLogger(__name__)


class NotificacionManager:
    """Gestor centralizado de notificaciones por correo"""

    EMAIL_FROM = "gymnazareth@gmail.com"

    @staticmethod
    def enviar_notificacion(
        usuario,
        tipo_notificacion,
        detalle_notificacion,
        asunto,
        cuerpo,
        descripcion=None,
        usar_html=False,
        fail_silently=False,
        archivo_adjunto=None,
    ):
        """
        Envía una notificación por correo al usuario y registra en base de datos.

        Args:
            usuario: Objeto Usuario destinatario
            tipo_notificacion: Tipo de notificación (MEMBRESIA, MANTENIMIENTO, ASISTENCIA)
            asunto: Asunto del correo
            cuerpo: Cuerpo del mensaje (HTML si usar_html=True, texto plano si False)
            descripcion: Descripción para guardar en BD (opcional)
            usar_html: Si True, trata el cuerpo como HTML; si False, como texto plano
            fail_silently: Si True, no lanza excepciones si falla el envío
            archivo_adjunto: Ruta al archivo a adjuntar (opcional)

        Returns:
            Tupla (éxito: bool, notificacion: Notificacion object o None)
        """

        if not usuario or not usuario.correo_usuario:
            logger.warning(f"Usuario sin correo: {usuario}")
            return False, None

        try:
            # Preparar el mensaje
            if usar_html:
                message = strip_tags(cuerpo)
                html_message = cuerpo
            else:
                    message = cuerpo
                    html_message = None
            email = EmailMultiAlternatives(
                    subject=asunto,
                    body=message,
                    from_email=NotificacionManager.EMAIL_FROM,
                    to=[usuario.correo_usuario],
                )

            if usar_html and html_message:
                    email.attach_alternative(html_message, "text/html")


            if archivo_adjunto:
                    email.attach_file(archivo_adjunto)
            email.send()

            notificacion = Notificacion.objects.filter(
                fk_usuario=usuario,
                tipo_notificacion=tipo_notificacion,
                detalle_notificacion = detalle_notificacion
            ).first()
            if not notificacion:

                notificacion = Notificacion.objects.create(
                    tipo_notificacion=tipo_notificacion,
                    detalle_notificacion = detalle_notificacion,
                    canal_notificacion="CORREO",
                    estado_notificacion="ASIGNADA",
                    fk_usuario=usuario,
                    descripcion=descripcion or asunto,
                )

                logger.info(
                    f"✓ Notificación enviada a {usuario.nombre_usuario} - ID: {notificacion.id}"
                )
                return True, notificacion

            else:
                if descripcion:  
                    notificacion.descripcion = descripcion
                notificacion.estado_notificacion = "ASIGNADA"
                notificacion.save()
                logger.info(
                    f"✓ Notificación ya registrada. "
                    f"Correo enviado a {usuario.nombre_usuario}"
                )
                return True,notificacion
        except Exception as e:
            logger.error(f"Error enviando notificación a {usuario.nombre_usuario}: {e}")
            if not fail_silently:
                raise
            return False, None

    @staticmethod
    def enviar_bienvenida(usuario):
        """Envía correo de bienvenida al crear una nueva cuenta"""

        asunto = "¡Bienvenido a Gimnasio Nazareth!"

        cuerpo = f"""
        Hola {usuario.nombre_usuario},
        
        ¡Bienvenido a nuestra plataforma Gimnasio Nazareth!
        
        Tu cuenta ha sido creada exitosamente. Ahora puedes acceder a todos nuestros servicios.
        
        Datos de tu cuenta:
        • Usuario: {usuario.user.username}
        • Correo: {usuario.correo_usuario}
        • Documento: {usuario.documento}
        • Rol: {usuario.get_rol_display() if hasattr(usuario, 'get_rol_display') else usuario.rol}
        
        Si tienes alguna pregunta, no dudes en contactarnos.
        
        ¡A entrenar! 💪
        
        Saludos cordiales,
        Equipo Gimnasio Nazareth
        """

        return NotificacionManager.enviar_notificacion(
            usuario=usuario,
            tipo_notificacion="MEMBRESIA",
            detalle_notificacion='Bienvenida',
            asunto=asunto,
            cuerpo=cuerpo,
            descripcion="Correo de bienvenida",
            usar_html=True,
        )

    @staticmethod
    def enviar_confirmacion_membresia(membresia):
        """Envía confirmación cuando se activa una nueva membresía"""

        usuario = membresia.fk_usuario
        asunto = "✅ Tu membresía ha sido activada"

        cuerpo = f"""
        Hola {usuario.nombre_usuario},
        
        Tu membresía ha sido creada y activada exitosamente.
        
        Detalles de tu membresía:
        • Documento: {usuario.documento}
        • Fecha de Inicio: {membresia.fecha_inicio.strftime('%d de %B de %Y')}
        • Fecha de Vencimiento: {membresia.fecha_fin.strftime('%d de %B de %Y') if membresia.fecha_fin else 'Por definir'}
        • Estado: {membresia.get_estado_display()}
        Ya puedes acceder a nuestras instalaciones con tu QR.
        
        ¡A entrenar! 💪
        
        Saludos cordiales,
        Equipo Gimnasio Nazareth
        """

        return NotificacionManager.enviar_notificacion(
            usuario=usuario,
            tipo_notificacion="MEMBRESIA",
            detalle_notificacion='Membresía_activada',
            asunto=asunto,
            cuerpo=cuerpo,
            descripcion=f"Activación de membresía - {membresia.id}",
            archivo_adjunto=membresia.qr_code.path if membresia.qr_code else None,
            usar_html=True,
        )

    @staticmethod
    def enviar_alerta_vencimiento(membresia, dias_faltantes):
        
        try:
            """Envía alerta cuando la membresía está próxima a vencer"""

            usuario = membresia.fk_usuario
            asunto = f'⏰ Tu membresía vence en {dias_faltantes} día{"s" if dias_faltantes != 1 else ""}'

            cuerpo = f"""
            Hola {usuario.nombre_usuario},
            
            Tu membresía está próxima a vencer. ¡Por favor, renévala para continuar disfrutando de nuestros servicios!
            
            Detalles:
            • Documento: {usuario.documento}
            • Fecha de Vencimiento: {membresia.fecha_fin.strftime('%d de %B de %Y')}
            • Días Faltantes: {dias_faltantes}
            
            Acércate a nuestras instalaciones para renovar tu membresía en cualquier momento.
            
            Contacto:
            📞 Teléfono: [Tu número aquí]
            📧 Email: {NotificacionManager.EMAIL_FROM}
            
            Saludos cordiales,
            Equipo Gimnasio Nazareth
            """

            return NotificacionManager.enviar_notificacion(
                usuario=usuario,
                tipo_notificacion="MEMBRESIA",
                detalle_notificacion="Próxima_a_vencer",
                asunto=asunto,
                cuerpo=cuerpo,
                descripcion=f"Alerta de vencimiento - Quedan {dias_faltantes} días",
                usar_html=True,
            )
        except Exception as e:
            logger.error(f"Error enviando alerta de vencimiento: {e}")
            return False, None
    @staticmethod
    def enviar_notificacion_vencida(membresia):
        """Envía notificación cuando la membresía ha vencido"""

        usuario = membresia.fk_usuario
        asunto = "⚠️ Tu membresía ha vencido"

        cuerpo = f"""
        Hola {usuario.nombre_usuario},
        
        Tu membresía ha llegado a su fecha de vencimiento y ha sido desactivada.
        
        Detalles:
        • Documento: {usuario.documento}
        • Fecha de Vencimiento: {membresia.fecha_fin.strftime('%d de %B de %Y') if membresia.fecha_fin else 'N/A'}
        • Estado Actual: Inactivo
        
        Para continuar utilizando nuestras instalaciones, por favor acércate a renovar tu membresía.
        
        Contacto:
        📞 Teléfono: [Tu número aquí]
        📧 Email: {NotificacionManager.EMAIL_FROM}
        
        Esperamos verte pronto,
        Equipo Gimnasio Nazareth
        """

        return NotificacionManager.enviar_notificacion(
            usuario=usuario,
            tipo_notificacion="MEMBRESIA",
            detalle_notificacion='Membresía_vencida',
            asunto=asunto,
            cuerpo=cuerpo,
            descripcion="Membresía vencida",
            usar_html=True,
        )

    @staticmethod
    def enviar_alerta_inasistencia(
        usuario, dias_sin_asistencia, ultima_asistencia=None
    ):
        """Envía alerta de inasistencia después de N días sin asistir"""

        asunto = "📅 Recordatorio: No hemos visto tu asistencia"

        cuerpo = f"""
        Hola {usuario.nombre_usuario},
        
        Notamos que no has asistido a nuestras instalaciones en los últimos {dias_sin_asistencia} días.
        
        ¡Te extrañamos! Nos gustaría verte pronto.
        
        Información:
        • Documento: {usuario.documento}
        • Última Asistencia: {ultima_asistencia.strftime('%d de %B de %Y') if ultima_asistencia else 'Sin registro'}
        • Días sin asistencia: {dias_sin_asistencia}
        
        Recuerda que tu membresía sigue activa y puedes visitar nuestro gimnasio en cualquier momento.
        
        ¡Esperamos tu próxima visita! 💪
        
        Contacto:
        📞 Teléfono: [Tu número aquí]
        📧 Email: {NotificacionManager.EMAIL_FROM}
        
        Saludos cordiales,
        Equipo Gimnasio Nazareth
        """

        return NotificacionManager.enviar_notificacion(
            usuario=usuario,
            tipo_notificacion="ASISTENCIA",
            detalle_notificacion='Inasistencia',
            asunto=asunto,
            cuerpo=cuerpo,
            descripcion=f"Alerta de inasistencia - {dias_sin_asistencia} días",
            usar_html=True,
        )

    @staticmethod
    def enviar_notificacion_mantenimiento(usuarios, mantenimiento):
        try:
            """Envía notificación a múltiples usuarios sobre un mantenimiento"""

            asunto = f"⚠️ Notificación de Mantenimiento: {mantenimiento.nombre_elemento.nombre_elemento}"

            cuerpo = f"""
            Hola,
            
            Informamos que se ha programado un mantenimiento en nuestras instalaciones.
            
            Detalles del Mantenimiento:
            • Elemento: {mantenimiento.nombre_elemento.nombre_elemento}
            • Tipo: {mantenimiento.get_tipo_mantenimiento_display()}
            • Fecha Programada: {mantenimiento.fecha_programada.strftime('%d de %B de %Y')}
            • Estado: {mantenimiento.get_estado_display()}
            • Descripción: {mantenimiento.descripcion}
            
            Durante este período, el equipo no estará disponible para su uso.
            
            Gracias por tu comprensión,
            Equipo Gimnasio Nazareth
            """

            resultados = []
            for usuario in usuarios:
                resultado = NotificacionManager.enviar_notificacion(
                    usuario=usuario,
                    tipo_notificacion="MANTENIMIENTO",
                    detalle_notificacion='Mantenimiento_programado',
                    asunto=asunto,
                    cuerpo=cuerpo,
                    descripcion=f"Mantenimiento - {mantenimiento.nombre_elemento.nombre_elemento}",
                )
                resultados.append(resultado)

            exito_count = sum(1 for r in resultados if r[0])
            logger.info(
                f"✓ {exito_count}/{len(usuarios)} notificaciones de mantenimiento enviadas"
            )

            return resultados
        except Exception as e:
            logger.error(f"Error enviando notificaciones de mantenimiento: {e}")
            return [(False, None) for _ in usuarios]
