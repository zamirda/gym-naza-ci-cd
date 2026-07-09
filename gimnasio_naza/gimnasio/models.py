from django.db import models
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
import qrcode
from io import BytesIO
from django.core.files import File

# Create your models here.
# ---------------------------------MODELO USUARIO-----------------------------------------


class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="usuario")
    documento = models.CharField(max_length=45, unique=True)
    nombre_usuario = models.CharField(max_length=45)
    apellido_usuario = models.CharField(max_length=45)
    fecha_nacimiento = models.DateField()
    telefono_usuario = models.CharField(max_length=45)
    correo_usuario = models.CharField(max_length=100, unique=True)
    peso_usuario = models.DecimalField(max_digits=10, decimal_places=2)
    altura_usuario = models.DecimalField(max_digits=10, decimal_places=2)
    genero_usuario = models.CharField(
        max_length=10, choices=[("M", "Masculino"), ("F", "Femenino")], default="M"
    )
    foto = models.ImageField(upload_to="usuarios/", null=True, blank=True)

    ROL_CHOICES = [
        ("Cliente", "Cliente"),
        ("Administrador", "Administrador"),
    ]
    rol = models.CharField(max_length=30, choices=ROL_CHOICES, null=True, blank=True)

    ESTADO_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
        ("visitante", "Visitante"),
    ]
    TIPOS_DOCUMENTO = [
        ("CC", "Cédula de Ciudadanía"),
        ("TI", "Tarjeta de Identidad"),
        ("CE", "Cédula de Extranjería"),
        ("PP", "Pasaporte"),
    ]

    tipo_documento = models.CharField(
        max_length=2, choices=TIPOS_DOCUMENTO, default="CC"
    )
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES)

    def __str__(self):
        return str(self.documento) + ("/") + (self.nombre_usuario)


    fecha_registro = models.DateField(default=date.today)

    def save(self,*args, **kwargs):
        if self.user and self.correo_usuario:
            if self.user.email != self.correo_usuario:
                self.user.email = self.correo_usuario
                self.user.save(update_fields=['email'])
        super(Usuario,self).save(*args, **kwargs)
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        db_table = "usuario"



# -----------------------------MODELO MEMBRESIA---------------------------------------------------
class Membresia(models.Model):

    fecha_inicio = models.DateField(
        default=datetime.now, verbose_name="Fecha de Inicio"
    )
    fecha_fin = models.DateField(
        null=True, blank=True, verbose_name="Fecha de Finalizacion"
    )
    ESTADO_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES)
    qr_code = models.ImageField(upload_to="qrs_membresias/", blank=True, null=True)
    fk_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        datos_qr = self.fk_usuario.documento
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(datos_qr)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        nombre_archivo = f"qr_{datos_qr}.png"
        self.qr_code.save(f"qr_{nombre_archivo}.png", File(buffer), save=False)
        super().save(*args, **kwargs)

    @property
    def es_valida(self):
        """Verifica si la membresía es válida (activa y no vencida)"""
        if not self.fecha_fin:
            return self.estado == "activo"
        from django.utils import timezone

        return self.estado == "activo" and self.fecha_fin >= timezone.now().date()

    @property
    def dias_para_vencer(self):
        """Retorna los días restantes para que venza la membresía"""
        if not self.fecha_fin:
            return None
        from django.utils import timezone

        dias = (self.fecha_fin - timezone.now().date()).days
        return dias if dias >= 0 else 0

    def __str__(self):
        return f"{self.fk_usuario.nombre_usuario} {self.fk_usuario.apellido_usuario} - {self.id}"

    class Meta:
        verbose_name = "Membresia"
        verbose_name_plural = "Membresias"
        db_table = "membresia"


# ---------MODELO ASISTENCIA -----------------------------------------------------
class Asistencia(models.Model):
    fecha_asistencia = models.DateField(
        default=date.today, verbose_name="Fecha de Asistencia"
    )
    hora_ingreso = models.TimeField(
        null=True, blank=True, verbose_name="Hora de Ingreso"
    )
    fk_membresia = models.ForeignKey(Membresia, on_delete=models.CASCADE)

    def __str__(self):
        return str(
            f"{self.id}-{self.fecha_asistencia}/{self.fk_membresia.fk_usuario.nombre_usuario}"
        )

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        db_table = "asistencia"


# --------------------CATEGORIA------------------
class Categoria(models.Model):

    NOMBRE_CATEGORIA = [
        ("maquinas", "Máquinas"),
        ("mancuernas", "Mancuernas"),
        ("discos", "Discos"),
        ("accesorios", "Accesorios"),
        ("barras", "Barras"),
    ]

    nombre_categoria = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=250)

    def __str__(self):
        return str(self.nombre_categoria)

    class Meta:
        db_table = "Categoria"
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"


class Elemento(models.Model):
    serial = models.CharField(max_length=45, unique=True)
    marca = models.CharField(max_length=45)
    nombre_elemento = models.CharField(max_length=45)

    UNIDAD_CHOICES = [("kg", "kg"), ("lb", "lb")]

    unidad_peso = models.CharField(max_length=2, choices=UNIDAD_CHOICES, default="kg")

    TIPO_CHOICES = [
        ("maquina", "Máquina"),
        ("disco", "Disco"),
        ("mancuerna", "Mancuerna"),
        ("barra", "Barras"),
        ("otro", "Otro"),
    ]

    peso_elemento = models.DecimalField(max_digits=10, decimal_places=2)

    ESTADO_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    fecha_ingreso = models.DateField()
    nombre_categoria = models.ForeignKey("Categoria", on_delete=models.CASCADE)

    cantidad = models.IntegerField(default=1)  # agregado
    imagen = models.ImageField(upload_to="elementos/", null=True, blank=True)

    def __str__(self):
        return self.nombre_elemento


class Mantenimiento(models.Model):
    fecha_programada = models.DateField()

    TIPO_CHOICES = [
        ("preventivo", "Preventivo"),
        ("correctivo", "Correctivo"),
    ]
    tipo_mantenimiento = models.CharField(max_length=20, choices=TIPO_CHOICES)

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("en_proceso", "En proceso"),
        ("completado", "Completado"),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)

    nombre_elemento = models.ForeignKey(Elemento, on_delete=models.CASCADE)
    descripcion = models.TextField()

    def __str__(self):
        return str(self.id)


# ---------------------------------MODELO NOTIFCACIONES-----------------------------------------
TIPO_NOTIFICACION = [
    ("MEMBRESIA", "Membresía"),
    ("MANTENIMIENTO", "Mantenimiento"),
    ("ASISTENCIA", "Asistencia"),
]

DETALLE_NOTIFICACION = [
    ("Bienvenida", "BIENVENIDA"),
    ("Membresía_activada", "MEMBRESIA_ACTIVADA"),
    ("Próxima_a_vencer", "VENCIMIENTO"),
    ("Membresía_vencida", "VENCIDA"),
    ("Inasistencia", "INASISTENCIA"),
    ("Mantenimiento_programado", "MANTENIMIENTO_PROGRAMADO"),
]
CANAL_NOTIFICACION = [
    ("SMS", "SMS"),
    ("CORREO", "Correo"),
]
ESTADO_NOTFIFICACION = [("ASIGNADA", "Asignada"), ("NO ASIGNADA", "No asignada")]


class Notificacion(models.Model):
    tipo_notificacion = models.CharField(
        max_length=120, choices=TIPO_NOTIFICACION, verbose_name="Tipo de Notificacion"
    )
    canal_notificacion = models.CharField(
        max_length=120, choices=CANAL_NOTIFICACION, verbose_name="Canal de Notificacion"
    )
    estado_notificacion = models.CharField(
        max_length=120,
        choices=ESTADO_NOTFIFICACION,
        verbose_name="Estado de Notificacion",
    )
    detalle_notificacion = models.CharField(
        max_length=120,
        choices=DETALLE_NOTIFICACION,
    )
    fk_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )
    fecha_envio = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de Envío"
    )
    descripcion = models.TextField(null=True, blank=True, verbose_name="Descripción")

    def __str__(self):
        return f"{self.get_tipo_notificacion_display()} - {self.fk_usuario.nombre_usuario} ({self.fecha_creacion.strftime('%d/%m/%Y')})"

    class Meta:
        verbose_name = "Notificacion"
        verbose_name_plural = "Notificaciones"
        db_table = "notificaciones"
        ordering = ["-fecha_creacion"]


# --------------------------------Modulo de Gestión de Encuestas----------------------------
class Encuesta(models.Model):
    ESTADO_CHOICES = [
        ("activa", "Activa"),
        ("inactiva", "Inactiva"),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="activa")
    fk_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    form_id = models.CharField(
        max_length=100, blank=True, null=True
    )  # ID del formulario de Google Forms
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(
        blank=True, null=True
    )  # Fecha cuando se envía la encuesta
    miembros = models.ManyToManyField(
        Usuario, related_name="encuestas", blank=True
    )  # Miembros seleccionados para la encuesta

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Encuesta"
        verbose_name_plural = "Encuestas"
        db_table = "encuesta"


class Pregunta(models.Model):
    TIPO_CHOICES = [
        ("short_answer", "Respuesta corta"),
        ("paragraph", "Párrafo"),
        ("multiple_choice", "Opción múltiple"),
        ("check_boxes", "Casillas de verificación"),
        ("dropdown", "Lista desplegable"),
        ("linear_scale", "Escala lineal"),
        ("date", "Fecha"),
        ("time", "Hora"),
    ]

    encuesta = models.ForeignKey(
        Encuesta, on_delete=models.CASCADE, related_name="preguntas"
    )
    pregunta = models.CharField(max_length=500)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    opciones = models.JSONField(
        blank=True, null=True
    )  # Para opciones en multiple_choice, check_boxes, dropdown
    requerida = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.pregunta

    class Meta:
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"
        db_table = "pregunta"
        ordering = ["orden"]


# --------------------------------Modulo Gestión de reportes estadisticas----------------------------
class Reportes_estadisticas(models.Model):

    TIPO_REPORTE_CHOICES = [
        ("usuarios", "Usuarios"),
        ("membresia", "Membresías"),
        ("asistencia", "Asistencias"),
        ("elemento", "Elementos"),
        ("mantenimiento", "Mantenimientos"),
        ("pqrs", "PQRS"),
        ("sancion", "Sanciones"),
        ("visitantes", "Visitantes Temporales"),
        ("turnos", "Turnos de Entrenadores"),
        ("certificaciones", "Certificaciones Internas"),
        ("estadisticas", "Reportes y Estadísticas"),
    ]

    TIPO_ARCHIVO = [
        ("PDF", "PDF"),
        ("EXCEL", "Excel"),
    ]

    tipo_reporte = models.CharField(
        max_length=30,
        choices=TIPO_REPORTE_CHOICES
    )

    tipo_archivo = models.CharField(
        max_length=10,
        choices=TIPO_ARCHIVO
    )

    descripcion = models.TextField()

    fecha_generacion = models.DateTimeField(auto_now_add=True)

    fk_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.get_tipo_reporte_display()} - {self.tipo_archivo}"

    class Meta:
        db_table = "Reporte"
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
        ordering = ["-fecha_generacion"]


# --------------------------------Modulo Gestión de reportes y PQRS------------------------


class Soporte_PQRS(models.Model):
    TIPO_PQRS_CHOICES = [
        ("peticion", "Peticion"),
        ("queja", "Queja"),
        ("reclamo", "Reclamo"),
        ("sugerencia", "Sugerencia"),
    ]
    tipo = models.CharField(
        max_length=20, choices=TIPO_PQRS_CHOICES, default="peticion"
    )
    descripcion = models.TextField()
    fecha_ingreso = models.DateField(default=date.today)
    ESTADO_CHOICES = [
        ("pendiente", "pendiente"),
        ("en_proceso", "en_proceso"),
        ("solucionada", "solucionada"),
    ]

    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="pendiente"
    )
    fk_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = "PQRS"
        verbose_name_plural = "PQRS"
        db_table = "PQRS"


# --------------------NUTRICION------------------


class Nutricion(models.Model):

    NIVEL_ACTIVIDAD_FISICA = [
        ("bajo", "Bajo"),
        ("medio", "Medio"),
        ("alto", "Alto"),
    ]

    OBJETIVO_NUTRICIONAL = [
        ("perder_peso", "Perder Peso"),
        ("mantener", "Mantener"),
        ("ganar_masa", "Ganar Masa Muscular"),
    ]

    TIPO_PLAN_ALIMENTICIO = [
        ("keto", "Keto"),
        ("balanceada", "Balanceada"),
        ("hiperproteica", "Hiperproteica"),
    ]

    nivel_actividad_fisica = models.CharField(
        max_length=20, choices=NIVEL_ACTIVIDAD_FISICA
    )
    objetivo_nutricional = models.CharField(max_length=20, choices=OBJETIVO_NUTRICIONAL)
    tipo_plan_alimenticio = models.CharField(
        max_length=40, choices=TIPO_PLAN_ALIMENTICIO
    )

    fk_Usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.fk_Usuario.nombre_usuario)

    class Meta:
        db_table = "Nutricion"
        verbose_name = "Nutricion"
        verbose_name_plural = "Nutriciones"


# ------------REGISTRO DE VISITANTES----------------


class Registrovisitantestemporales(models.Model):
    fecha_registro = models.DateField(default=date.today)
    nombre = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre} - {self.cedula}"

    class Meta:
        verbose_name = "Registro Visitante"
        verbose_name_plural = "Registros Visitantes"
        db_table = "registro_visitantes"


# -----------TURNO DE ENTRENADORES----------------


class Turnosentrenadores(models.Model):
    JORNADA_CHOICES = [
        ("mañana", "Mañana"),
        ("tarde", "Tarde"),
    ]

    administrador = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="turnos_entrenador",
    )

    fecha_turno_inicio = models.DateField(default=date.today)
    fecha_turno_final = models.DateField(default=date.today)
    jornada = models.CharField(max_length=10, choices=JORNADA_CHOICES)

    def __str__(self):
        if self.administrador:
            return f"{self.administrador.username} - {self.jornada}"
        return f"Turno {self.id}"

    class Meta:
        verbose_name = "Turno Entrenador"
        verbose_name_plural = "Turnos Entrenadores"
        db_table = "turno_entrenadores"


# -----------------IMC------------------------------


class Masa_corporal(models.Model):
    peso_cliente = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_control = models.DateField()
    altura_cliente = models.DecimalField(max_digits=10, decimal_places=2)
    fk_Nutricion = models.ForeignKey(
        Nutricion, on_delete=models.CASCADE, verbose_name="Nutricion" , related_name='nutricion'
    )
    imc = models.FloatField(null=True, blank=True)
    estado_imc = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        usuario = self.fk_Nutricion.fk_Usuario
        return f"{usuario.nombre_usuario} - {usuario.documento}"

    class Meta:
        db_table = "Masa_corporal"
        verbose_name = "Masa_corporal"
        verbose_name_plural = "Masas_corporales"


# ------------RUTINA----------------


class Rutina(models.Model):
    tipo_rutina = models.CharField(
        max_length=50,
        choices=[
            ("FUERZA", "Fuerza"),
            ("CARDIO", "Cardio"),
            ("FUNCIONAL", "Funcional"),
        ],
    )

    dias_disponibles = models.IntegerField()

    distribucion_rutina = models.CharField(
        max_length=30,
        choices=[
            ("SUPERIOR", "Superior"),
            ("INFERIOR", "Inferior"),
            ("COMPLETA", "Cuerpo completo"),
        ],
    )

    fk_imc = models.ForeignKey(Masa_corporal, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Rutina"
        verbose_name_plural = "Rutinas"
        db_table = "rutina"

    def __str__(self):
        return str(self.id)


"""----------certificaciones-----------"""


class Certificacion_interna(models.Model):
    descripcion_certificacion = models.CharField(max_length=500)
    fecha_certificacion = models.DateField(auto_now=False, auto_now_add=False)
    fk_membresia = models.ForeignKey(
        Membresia, on_delete=models.CASCADE, verbose_name="Membresía"
    )
    descargado = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = "Certificacion_interna"
        verbose_name = "Certificacion_interna"
        verbose_name_plural = "Certificaciones_internas"


# ---------sanciones----------
class Sancion(models.Model):

    Tipo_sancion_chioce = [
        ("leve", "Leve"),
        ("moderada", "Moderada"),
        ("grave", "Grave"),
    ]
    Estado_choice = [
        ("activa", "Activa"),
        ("inactiva", "Inactiva"),
        ("pendiente", "Pendiente"),
    ]
    motivo_sancion = models.CharField(max_length=350)
    tipo_sancion = models.CharField(max_length=80, choices=Tipo_sancion_chioce)
    fecha_inicio = models.DateField()
    duracion_sancion = models.IntegerField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=80, choices=Estado_choice)
    fk_usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, verbose_name="Usuario"
    )

    def __str__(self):
        usuario = self.fk_Usuario
        return f"{usuario.nombre_usuario} - {usuario.documento}"

    class Meta:
        db_table = "Sancion"
        verbose_name = "Sancion"
        verbose_name_plural = "Sanciones"
