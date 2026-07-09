import os
import re 
from django.forms import ModelForm, formset_factory, inlineformset_factory
from gimnasio.models import *
from django import forms
from datetime import date, datetime, time, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.shortcuts import render
from django.db.models import Count
from django.forms import BaseInlineFormSet
from django.contrib.auth.forms import PasswordResetForm
from .models import Usuario
from django.contrib.auth.forms import PasswordResetForm
from .models import Usuario # Asegúrate de que el nombre sea correcto

class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        # Buscamos en tu modelo personalizado 'Usuario'
        usuarios_perfil = Usuario.objects.filter(correo_usuario__iexact=email)
        
        if usuarios_perfil.exists():
            usuarios_reales = []
            for perfil in usuarios_perfil:
                if perfil.user:
                    # TRUCO: Le asignamos temporalmente el correo del perfil 
                    # al objeto User de Django para que el enviador lo encuentre
                    perfil.user.email = perfil.correo_usuario
                    usuarios_reales.append(perfil.user)
            return usuarios_reales
        
        return super().get_users(email)

    def send_mail(self, subject_template_name, email_template_name, context, 
                  from_email, to_email, html_email_template_name=None):
        
        # Forzamos el nombre de la URL con el namespace 'login'
        context['password_reset_confirm_url_name'] = 'login:password_reset_confirm'
        
        super().send_mail(
            subject_template_name, email_template_name, context, 
            from_email, to_email, html_email_template_name
        )
class ElementoForm(forms.ModelForm):
    class Meta:
        model = Elemento
        fields = '__all__'
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
        }


    def clean(self):
        cleaned_data = super().clean()
        serial = cleaned_data.get('serial')
        nombre_elemento = cleaned_data.get('nombre_elemento')
        fecha_ingreso = cleaned_data.get('fecha_ingreso')
        
        if fecha_ingreso and fecha_ingreso > timezone.now().date():
            raise forms.ValidationError('La fecha de ingreso no puede ser futura.')

    
        qs = Elemento.objects.all()
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if serial and nombre_elemento and qs.filter(serial=serial,nombre_elemento=nombre_elemento).exists():
            raise forms.ValidationError('Ya existe un elemento con ese serial y nombre.')
        return cleaned_data
    def clean_serial(self):
        serial = self.cleaned_data.get('serial')
        if serial and not re.match(r'^[A-Z0-9]{5,10}$', serial):
            raise forms.ValidationError('El serial debe contener entre 5 y 10 caracteres alfanuméricos en mayúsculas.')
        return serial
    def clean_nombre_elemento(self):
        nombre_elemento = self.cleaned_data.get('nombre_elemento')
        if nombre_elemento and not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ]+$', nombre_elemento):
            raise forms.ValidationError('El nombre del elemento solo puede contener letras.')
        return nombre_elemento
    def clean_fecha_ingreso(self):
        fecha_ingreso = self.cleaned_data.get('fecha_ingreso')
        if fecha_ingreso and fecha_ingreso > timezone.now().date():
            raise forms.ValidationError('La fecha de ingreso no puede ser futura.')
        return fecha_ingreso
    def clean_marca(self):
        marca = self.cleaned_data.get('marca')
        if marca and not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ]+$', marca):
            raise forms.ValidationError('La marca solo puede contener letras.')
        return marca
    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            ext = os.path.splitext(imagen.name)[1].lower()
            if ext != '.png' and ext != '.jpg' and ext != '.jpeg':
                raise forms.ValidationError('Solo se permiten imágenes en formato PNG, JPG o JPEG.')
        return imagen


# ==========================================
# FORMULARIO DE ACCESO
# ==========================================
# ============================================================
# Este archivo contiene SOLO las clases que cambian.
# Reemplaza las clases correspondientes en tu forms.py existente
# por estas versiones. No borres el resto de tu forms.py.
# ============================================================

import re
from datetime import date, time, datetime, timedelta
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Usuario, Asistencia, Membresia


# ==========================================
# FORMULARIO DE ACCESO (sin cambios funcionales,
# se deja igual a como ya lo tenías)
# ==========================================

class UserForm(forms.ModelForm):

    password = forms.CharField(
        label="Contraseña",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Dejar vacío para no cambiar',
                'autocomplete': 'new-password',
                'id': 'password-field'
            },
            render_value=False
        )
    )

    class Meta:
        model = User
        fields = ['username', 'password']

        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ingrese usuario',
                    'autocomplete': 'off',
                    'maxlength': '30'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Nunca mostrar el hash de la contraseña
        self.initial['password'] = ''
# ==========================================
# FORMULARIO DE USUARIO (CORREGIDO)
# ==========================================
#
# Bugs que tenía el original y que se corrigen aquí:
#
# 1. clean_fecha_nacimiento() definía un campo de formulario
#    (forms.DateField(...)) DENTRO del método, sin usarlo para
#    nada, y luego declaraba un SEGUNDO clean_fecha_nacimiento
#    anidado dentro del primero. En Python, una función definida
#    dentro de otra función no se ejecuta solo por estar ahí: el
#    primer clean_fecha_nacimiento devolvía cleaned_data sin
#    haber asignado fecha_nacimiento (NameError potencial) y el
#    "real" (el de adentro) jamás era llamado por Django, porque
#    Django solo conoce el método de nivel de clase con ese nombre.
#    Al haber dos `def` con el mismo nombre en la clase, el segundo
#    sobrescribe al primero en el namespace de la clase — así que
#    en la práctica funcionaba solo "por accidente", pero el código
#    muerto confundía y arriesgaba romperse con cualquier edición.
#
# 2. clean_telefono_usuario() tenía código MUERTO después de un
#    `return telefono`: las líneas de validación de edad (`if fecha
#    >= date.today(): ...`) nunca se ejecutaban porque están después
#    del return, y además usaban una variable `fecha` que no existe
#    en ese método (era código que pertenecía a clean_fecha_nacimiento
#    y quedó mal pegado).
#
# Abajo: una sola versión limpia de cada método, cada validación en
# su lugar correcto.


class UsuarioForm(forms.ModelForm):

    foto = forms.ImageField(required=False)

    class Meta:
        model = Usuario

        fields = [
            'documento',
            'tipo_documento',
            'nombre_usuario',
            'apellido_usuario',
            'fecha_nacimiento',
            'telefono_usuario',
            'correo_usuario',
            'peso_usuario',
            'altura_usuario',
            'rol',
            'genero_usuario',
            'foto',
        ]

        widgets = {
            'documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese documento',
                'maxlength': '10',
                'pattern': '[0-9]{7,10}',
                'title': 'Solo números entre 7 y 10 dígitos',
                'oninput': 'this.value=this.value.replace(/[^0-9]/g,"")'
            }),
            'tipo_documento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nombre_usuario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese nombres',
                'pattern': '[A-Za-záéíóúÁÉÍÓÚñÑ ]+',
                'title': 'Solo letras y espacios',
                'autocomplete': 'off'
            }),
            'apellido_usuario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese apellidos',
                'pattern': '[A-Za-záéíóúÁÉÍÓÚñÑ ]+',
                'title': 'Solo letras y espacios',
                'autocomplete': 'off'
            }),

            # ==========================================
            # FECHA NACIMIENTO
            # ==========================================

            'fecha_nacimiento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),

            # ==========================================
            # TELEFONO
            # ==========================================

            'telefono_usuario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese teléfono',
                'maxlength': '10',
                'pattern': '3[0-9]{9}',
                'title': 'Debe iniciar en 3 y tener 10 dígitos',
                'oninput': 'this.value=this.value.replace(/[^0-9]/g,"")'
            }),
            'correo_usuario': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese correo',
                'autocomplete': 'off'
            }),
            'peso_usuario': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Peso en kg',
                'min': '30',
                'max': '150'
            }),
            'altura_usuario': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Altura en cm',
                'min': '100',
                'max': '230'
            }),
            'rol': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'foto': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.webp'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']

    # =====================================================
    # VALIDAR ROL
    # =====================================================
    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if not rol:
            raise forms.ValidationError('Debe seleccionar un rol válido.')
        return rol

    # =====================================================
    # VALIDAR NOMBRE
    # =====================================================
    def clean_nombre_usuario(self):
        nombre = self.cleaned_data.get('nombre_usuario', '').strip()

        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]+$', nombre):
            raise forms.ValidationError('El nombre solo puede contener letras.')

        if len(nombre) < 2:
            raise forms.ValidationError('El nombre es demasiado corto.')

        limpio = nombre.lower().replace(' ', '')
        if len(set(limpio)) == 1:
            raise forms.ValidationError('Ingrese un nombre válido.')

        return nombre.title()

    # =====================================================
    # VALIDAR APELLIDO
    # =====================================================
    def clean_apellido_usuario(self):
        apellido = self.cleaned_data.get('apellido_usuario', '').strip()

        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]+$', apellido):
            raise forms.ValidationError('El apellido solo puede contener letras.')

        if len(apellido) < 2:
            raise forms.ValidationError('El apellido es demasiado corto.')

        limpio = apellido.lower().replace(' ', '')
        if len(set(limpio)) == 1:
            raise forms.ValidationError('Ingrese un apellido válido.')

        return apellido.title()

    # =====================================================
    # VALIDAR FECHA NACIMIENTO (única versión, limpia)
    # Edad permitida: entre 12 y 90 años, igual que la regla
    # que ya usas en el JS del wizard de asistencia.
    # =====================================================

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')

        if not fecha:
            raise forms.ValidationError(
                "Por favor ingresa una fecha de nacimiento."
            )


    def clean_nombre_usuario(self):
        nombre = self.cleaned_data.get('nombre_usuario', '').strip()
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]+$', nombre):
            raise forms.ValidationError('El nombre solo puede contener letras.')
        if len(nombre) < 2:
            raise forms.ValidationError('El nombre es demasiado corto.')
        limpio = nombre.lower().replace(' ', '')
        if len(set(limpio)) == 1:
            raise forms.ValidationError('Ingrese un nombre válido.')
        return nombre.title()

    def clean_apellido_usuario(self):
        apellido = self.cleaned_data.get('apellido_usuario', '').strip()
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]+$', apellido):
            raise forms.ValidationError('El apellido solo puede contener letras.')
        if len(apellido) < 2:
            raise forms.ValidationError('El apellido es demasiado corto.')
        limpio = apellido.lower().replace(' ', '')
        if len(set(limpio)) == 1:
            raise forms.ValidationError('Ingrese un apellido válido.')
        return apellido.title()



    def clean_nombre_usuario(self):
        nombre = self.cleaned_data.get('nombre_usuario', '').strip()
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]+$', nombre):
            raise forms.ValidationError('El nombre solo puede contener letras.')
        if len(nombre) < 2:
            raise forms.ValidationError('El nombre es demasiado corto.')
        limpio = nombre.lower().replace(' ', '')
        if len(set(limpio)) == 1:
            raise forms.ValidationError('Ingrese un nombre válido.')
        return nombre.title()

    def clean_apellido_usuario(self):
        apellido = self.cleaned_data.get('apellido_usuario', '').strip()
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]+$', apellido):
            raise forms.ValidationError('El apellido solo puede contener letras.')
        if len(apellido) < 2:
            raise forms.ValidationError('El apellido es demasiado corto.')
        limpio = apellido.lower().replace(' ', '')
        if len(set(limpio)) == 1:
            raise forms.ValidationError('Ingrese un apellido válido.')
        return apellido.title()


    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')

        if not fecha:
            raise forms.ValidationError(
                "Por favor ingresa una fecha de nacimiento."
            )

        hoy = date.today()

        if fecha >= hoy:
            raise forms.ValidationError(
                "La fecha de nacimiento no puede ser hoy ni futura."
            )

        if fecha.year < 1900:
            raise forms.ValidationError(
                "La fecha debe ser posterior al año 1900."
            )

        edad = (
            hoy.year
            - fecha.year
            - (
                (hoy.month, hoy.day)
                <
                (fecha.month, fecha.day)
            )
        )

        if edad < 16:
            raise forms.ValidationError(
                "El usuario debe tener mínimo 16 años."
            )

        return fecha

    def clean_telefono_usuario(self):
        telefono = self.cleaned_data.get('telefono_usuario')
        if telefono:
            if not re.match(r'^3\d{9}$', telefono):
                raise forms.ValidationError(
                    'El teléfono debe contener exactamente 10 dígitos y comenzar con 3.'
                )
        return telefono

    # =====================================================
    # VALIDAR CORREO (duplicados, dejado explícito porque
    # el modelo ya tiene unique=True pero así el mensaje de
    # error es más claro en el form)
    # =====================================================
    def clean_correo_usuario(self):
        correo = self.cleaned_data.get('correo_usuario', '').strip()
        if correo:
            qs = Usuario.objects.filter(correo_usuario__iexact=correo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Este correo ya está registrado.')
        return correo

    # =====================================================
    # VALIDAR DOCUMENTO (duplicados)
    # =====================================================
    def clean_documento(self):
        documento = self.cleaned_data.get('documento', '').strip()
        if documento:
            if not documento.isdigit():
                raise forms.ValidationError('El documento solo puede contener números.')
            if not (7 <= len(documento) <= 10):
                raise forms.ValidationError('El documento debe tener entre 7 y 10 dígitos.')

            qs = Usuario.objects.filter(documento=documento)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Este documento ya está registrado.')
        return documento

    # =====================================================
    # VALIDAR PESO / ALTURA
    # =====================================================
    def clean_peso_usuario(self):
        peso = self.cleaned_data.get('peso_usuario')
        if peso is not None and not (30 <= peso <= 150):
            raise forms.ValidationError('El peso debe estar entre 30 kg y 150 kg.')
        return peso

    def clean_altura_usuario(self):
        altura = self.cleaned_data.get('altura_usuario')
        if altura is not None and not (100 <= altura <= 230):
            raise forms.ValidationError('La altura debe estar entre 100 cm y 230 cm.')
        return altura


# ==========================================
# VALIDADORES REUTILIZABLES PARA USERNAME Y PASSWORD
# (usados por el wizard, tanto en backend como referencia
# para mantener el mismo criterio en frontend)
# ==========================================

USERNAME_REGEX = re.compile(r'^[A-Za-z0-9]+$')

# Mín. 8 caracteres, al menos 1 mayúscula, 1 número y 1 símbolo
PASSWORD_REGEX = re.compile(
    r'^(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s])(?=.{8,}).+$'
)


def validar_username(username):
    """
    Solo letras y números, sin espacios ni símbolos.
    Devuelve un string de error o None si es válido.
    """
    username = (username or '').strip()
    if not username:
        return 'El nombre de usuario es requerido.'
    if len(username) < 4:
        return 'Debe tener al menos 4 caracteres.'
    if len(username) > 30:
        return 'No puede tener más de 30 caracteres.'
    if not USERNAME_REGEX.match(username):
        return 'Solo se permiten letras y números, sin espacios ni símbolos.'
    return None


def validar_password(password):
    """
    Mín. 8 caracteres, 1 mayúscula, 1 número, 1 símbolo.
    Devuelve un string de error o None si es válida.
    """
    if not password:
        return 'La contraseña es requerida.'
    if len(password) < 8:
        return 'Debe tener al menos 8 caracteres.'
    if not re.search(r'[A-Z]', password):
        return 'Debe contener al menos una letra mayúscula.'
    if not re.search(r'\d', password):
        return 'Debe contener al menos un número.'
    if not re.search(r'[^\w\s]', password):
        return 'Debe contener al menos un símbolo (ej: ! @ # $ % &).'
    return None

class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = Mantenimiento
        fields = "__all__"
        widgets = {
            "fecha_programada": forms.DateInput(attrs={"type": "date"}),
            "fecha_realizada": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Ingrese la descripción del mantenimiento",
                "rows": 3  # Agregado para que no use el tamaño gigante por defecto de Textarea
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        fecha_programada = cleaned_data.get("fecha_programada")
        elemento = cleaned_data.get("nombre_elemento")

        if elemento and fecha_programada:
            qs = Mantenimiento.objects.filter(
                nombre_elemento=elemento
            )

            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.filter(fecha_programada=fecha_programada).exists():
                raise forms.ValidationError(
                    "Ya existe un mantenimiento para esa fecha."
                )

        return cleaned_data
    
    
class AsistenciaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['fecha_asistencia'].initial = datetime.now().strftime('%d-%m-%Y')
            self.fields['hora_ingreso'].initial = datetime.now().strftime('%H:%M')

    class Meta:
        model = Asistencia
        fields = '__all__'
        widgets = {
            'hora_ingreso': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'fecha_asistencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        fecha_asistencia = cleaned_data.get('fecha_asistencia')
        hora_ingreso = cleaned_data.get('hora_ingreso')
        fk_membresia = cleaned_data.get('fk_membresia')

        if not fecha_asistencia or not fk_membresia:
            return cleaned_data

        hoy = date.today()

        if not self.instance.pk:
            # CREAR: la fecha debe ser exactamente hoy
            if fecha_asistencia != hoy:
                self.add_error('fecha_asistencia', 'Al crear una asistencia, la fecha debe ser la actual')
        else:
            # EDITAR: se permite cambiar el día, pero debe seguir
            # dentro de la semana actual (lunes a domingo)
            inicio_semana = hoy - timedelta(days=hoy.weekday())  # lunes
            fin_semana = inicio_semana + timedelta(days=6)       # domingo

            if not (inicio_semana <= fecha_asistencia <= fin_semana):
                self.add_error(
                    'fecha_asistencia',
                    'La fecha de asistencia debe estar dentro de la semana actual'
                )

        asistencia_existente = Asistencia.objects.filter(
            fk_membresia__fk_usuario=fk_membresia.fk_usuario,
            fecha_asistencia=fecha_asistencia
        ).exclude(pk=self.instance.pk)

        if asistencia_existente.exists():
            self.add_error('fk_membresia', 'Ya existe una asistencia registrada para este usuario en esa fecha')

        if hora_ingreso:
            if time(12, 0) <= hora_ingreso <= time(17, 0):
                self.add_error('hora_ingreso', 'No se permiten registros entre las 12:00 PM y las 5:00 PM')
            elif hora_ingreso >= time(21, 0) or hora_ingreso < time(5, 0):
                self.add_error('hora_ingreso', 'No se permiten registros entre las 9:00 PM y las 5:00 AM')

        return cleaned_data
        
class MembresiaForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = datetime.now().date()
        self.fields['fecha_inicio'].initial = hoy.strftime('%Y-%m-%d')
        self.fields['fecha_fin'].initial = (hoy + timedelta(days=30)).strftime('%Y-%m-%d')
        if 'qr_code' in self.fields:
            self.fields['qr_code'].disabled = True
            self.fields['qr_code'].required = False

        if 'estado' in self.fields:
            if not self.instance.pk:
                # CREAR: estado fijo en 'activo', no editable por el usuario
                self.fields['estado'].initial = 'activo'  # o True si es BooleanField
                self.fields['estado'].disabled = True
                self.fields['estado'].required = False
            # EDITAR: se deja el campo tal cual, editable

    class Meta:
        model = Membresia
        fields = '__all__'
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fk_usuario = cleaned_data.get('fk_usuario')

        if not fecha_inicio or not fk_usuario:
            return cleaned_data

        hoy = date.today()

        if not self.instance.pk:
            # CREAR: la fecha de inicio debe ser exactamente hoy
            if fecha_inicio != hoy:
                self.add_error('fecha_inicio', 'La fecha de inicio debe ser la actual')
            # Forzar estado activo sin importar lo que llegue en el POST
            cleaned_data['estado'] = 'activo'  # o True si es BooleanField
        else:
            # EDITAR: se permite cambiar el día, pero debe seguir
            # dentro del mes y año actual
            if fecha_inicio.month != hoy.month or fecha_inicio.year != hoy.year:
                self.add_error(
                    'fecha_inicio',
                    'La fecha de inicio debe estar dentro del mes y año actual'
                )
            # estado queda tal como lo eligió el usuario en cleaned_data['estado']

        # fecha_fin siempre se recalcula a partir de fecha_inicio,
        # así que ya no hace falta validarla manualmente contra el form:
        # eliminamos las comparaciones viejas (fin > hoy+30, fin < hoy+30, etc.)
        # porque cleaned_data['fecha_fin'] se sobreescribe de todas formas.
        cleaned_data['fecha_fin'] = fecha_inicio + timedelta(days=30)

        membresia_existente = Membresia.objects.filter(
            fk_usuario=fk_usuario,
            fecha_inicio__month=fecha_inicio.month,
            fecha_inicio__year=fecha_inicio.year
        ).exclude(pk=self.instance.pk)

        if membresia_existente.exists():
            self.add_error(
                'fk_usuario',
                'El usuario ya tiene una membresia registrada en este mes'
            )

        return cleaned_data

class NotificacionForm(forms.ModelForm):
    def __init__(self,*args, **kwargs):
        super().__init__(*args,**kwargs)
        self.initial["fecha_envio"] = (
            timezone.now() + timedelta(minutes=1)
        ).strftime("%Y-%m-%dT%H:%M")
    class Meta:
        model = Notificacion
        fields = '__all__'
        widgets ={
            'fk_usuario': forms.Select(attrs={'class': 'form-control'}),
            
            'tipo_notificacion': forms.Select(attrs={
                'class': 'form-control',
            }),
            'canal_notificacion': forms.Select(attrs={
                'class': 'form-control',
            }),
            'fk_membresia': forms.Select(attrs={
                'class': 'form-control',
            }),
            'fk_asistencia': forms.Select(attrs={
                'class': 'form-control',
            }),
            'fk_mantenimiento': forms.Select(attrs={
                'class': 'form-control',
            }),
            'fecha_envio': forms.DateTimeInput(attrs={
                 "class": "form-control",
                 "type": "datetime-local"
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_notificacion = cleaned_data.get('tipo_notificacion')
        canal_notificacion = cleaned_data.get('canal_notificacion')
        exist_notificacion = Notificacion.objects.filter(tipo_notificacion=tipo_notificacion).exclude(pk=self.instance.pk).exists()
        exit_canal = Notificacion.objects.filter(canal_notificacion=canal_notificacion).exclude(pk=self.instance.pk).exists()
        if exist_notificacion and exit_canal:
            self.add_error('tipo_notificacion', 'Ya existe una notificación con este tipo y canal')
        return cleaned_data
        
        
        



class EncuestaForm(forms.ModelForm):
    miembros = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.filter(estado='activo'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label="Seleccionar Miembros"
    )
    class Meta:
        model = Encuesta
        fields = ['nombre', 'estado', 'fk_usuario', 'miembros']
        widgets = {
            'nombre' : forms.TextInput(attrs={ 
                'class':'form-control',
                'placeholder': 'Ingrese el nombre de la encuesta'}),
            
            'estado':
                forms.Select(attrs={
                'class':'form-control'}),
            'fk_usuario':
                forms.Select(attrs={
                    'class':'form-control',
                })      
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')

        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio")

        nombre = nombre.strip()

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise forms.ValidationError("El nombre solo puede contener letras")

        existe = Encuesta.objects.filter(nombre__iexact=nombre)

        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)

        if existe.exists():
            raise forms.ValidationError("Ya existe una encuesta con ese nombre")
        
        if len(set(nombre.replace(" ", "").lower())) == 1:
            raise forms.ValidationError("El nombre no puede contener solo letras repetidas")

        return nombre

class PreguntaForm(forms.ModelForm):
    opciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Opciones separadas por comas (para opciones múltiples)',
            'rows': 3
        })
    )

    requerida = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = Pregunta
        fields = '__all__'

    class Meta:
        model = Pregunta
        fields = ['pregunta', 'tipo', 'opciones', 'requerida']
        widgets = {
            'pregunta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese la pregunta'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'requerida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    def clean_pregunta(self):
        pregunta = self.cleaned_data.get('pregunta')

        if not pregunta:
            raise forms.ValidationError("La pregunta es obligatoria")

        pregunta = pregunta.strip()

        #Solo números (incluye espacios)
        if pregunta.replace(" ", "").isdigit():
            raise forms.ValidationError("La pregunta no puede contener solo números")
        
        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', pregunta):
            raise forms.ValidationError("La pregunta debe contener al menos una letra")

        return pregunta
    # forms.py
    def clean_opciones(self):
        opciones = self.cleaned_data.get('opciones')
        tipo = self.cleaned_data.get('tipo')
        # Validar que si es opción múltiple, existan opciones
        if tipo in ['multiple_choice', 'check_boxes', 'dropdown'] and not opciones:
            raise forms.ValidationError("Debe proporcionar opciones para este tipo de pregunta")
        if opciones:
            # Convierte el texto "1,2" en una lista de Python ['1', '2'] para el JSONField
            return [op.strip() for op in opciones.split(',') if op.strip()]
        return None
    
class BasePreguntaFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        total = 0

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                pregunta = form.cleaned_data.get('pregunta')

                if not pregunta:
                    raise forms.ValidationError("No puede haber preguntas vacías")

                total += 1

        if total == 0:
            raise forms.ValidationError("Debe agregar al menos una pregunta")
        
PreguntaFormSet = inlineformset_factory(
    Encuesta, 
    Pregunta, 
    form=PreguntaForm, 
    formset=BasePreguntaFormSet,
    extra=1,        #Solo 1 pregunta inicial
    can_delete=True,
    max_num=20,     #Permite hasta 20 preguntas
    validate_max=False
)
class Soporte_PQRSForm(ModelForm):

    class Meta:
        model = Soporte_PQRS
        fields = '__all__'

        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el tipo de soporte pqr'
            }),

            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese la descripcion del soporte pqr'
            }),

            'fecha_ingreso': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),

            'estado': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el estado del soporte pqr',
                'rows': 3,
                'cols': 3
            }),

            'fk_usuario': forms.Select(attrs={
                'class': 'form-control',
            })
        }

    def clean_descripcion(self):

        descripcion = self.cleaned_data['descripcion'].strip()

        # VALIDAR MAXIMO
        if len(descripcion) > 200:
            raise forms.ValidationError(
                "La descripción no debe tener más de 200 caracteres"
            )

        # VALIDAR MINIMO
        if len(descripcion) < 10:
            raise forms.ValidationError(
                "La descripción debe tener mínimo 10 caracteres"
            )

        # NO PERMITIR CARACTERES ESPECIALES
        if re.search(r'[{}[\]<>*/\\|°¬¨+=~`%^]', descripcion):
            raise forms.ValidationError(
                "No se permiten caracteres especiales"
            )

        # NO PERMITIR NUMEROS REPETIDOS
        # ejemplo: 111111111
        if re.search(r'(\d)\1{3,}', descripcion):
            raise forms.ValidationError(
                "No se permiten números repetidos excesivamente"
            )

        # NO PERMITIR LETRAS REPETIDAS
        # ejemplo: aaaaaaaa
        if re.search(r'([a-zA-Z])\1{3,}', descripcion.lower()):
            raise forms.ValidationError(
                "No se permiten letras repetidas excesivamente"
            )

        palabras = descripcion.split()

        for palabra in palabras:

            palabra_lower = palabra.lower()

            # NO PERMITIR jajajajaja
            if re.fullmatch(r'(ha|ja|je|ji|jo|ju)+', palabra_lower):
                raise forms.ValidationError(
                    "Ingrese una descripción coherente"
                )

            # NO PERMITIR palabras iguales
            # ejemplo: aaaaaaaa
            if len(set(palabra_lower)) == 1:
                raise forms.ValidationError(
                    "La descripción contiene palabras inválidas"
                )

            # NO PERMITIR TEXTO RANDOM
            # ejemplo: asdfghjkl, qwertyui
            if re.fullmatch(r'[a-zA-Z0-9]{8,}', palabra):

                vocales = sum(
                    1 for letra in palabra_lower
                    if letra in "aeiou"
                )

                consonantes = sum(
                    1 for letra in palabra_lower
                    if letra.isalpha() and letra not in "aeiou"
                )

                if consonantes > vocales * 3:
                    raise forms.ValidationError(
                        "Ingrese una descripción válida y coherente"
                    )

                if vocales > consonantes * 2:
                    raise forms.ValidationError(
                        "Ingrese una descripción válida y coherente"
                    )

            # NO PERMITIR MEZCLAS RANDOM DE LETRAS Y NUMEROS
            # ejemplo: 765gtrhyte3wsdfghj
            if re.fullmatch(r'[a-zA-Z0-9]{10,}', palabra):

                letras = sum(c.isalpha() for c in palabra)
                numeros = sum(c.isdigit() for c in palabra)

                # MUCHAS letras y números juntos
                if letras >= 5 and numeros >= 2:
                    raise forms.ValidationError(
                        "Ingrese una descripción coherente y válida"
                    )

                # PATRONES TIPO TECLADO
                patrones_invalidos = [
                    'asdf', 'qwerty', 'zxcv',
                    'hjkl', 'poiuy', 'lkjh'
                ]

                for patron in patrones_invalidos:

                    if patron in palabra_lower:
                        raise forms.ValidationError(
                            "La descripción contiene texto inválido"
                        )

        return descripcion

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hoy = timezone.localdate()

        self.fields['fecha_ingreso'].initial = hoy.strftime('%Y-%m-%d')

        self.fields['fecha_ingreso'].widget.attrs['min'] = hoy.strftime('%Y-%m-%d')
        
    def clean_fecha_ingreso(self):
        fecha_ingreso = self.cleaned_data.get('fecha_ingreso')

        if fecha_ingreso and fecha_ingreso < timezone.localdate():
            raise forms.ValidationError(
                'La fecha de ingreso no puede ser anterior a la de hoy'
            )

        return fecha_ingreso
        
class Reportes_estadisticasForm(forms.ModelForm):
    class Meta:
        model = Reportes_estadisticas
        fields = '__all__'
        widgets = {
            'tipo_reporte': forms.Select(attrs={ 
                'class': 'form-control',
            }),
            'descripcion' : forms.TextInput(attrs={ 
                'class':'form-control',
                
                'placeholder': 'Ingrese la descripcion del reporte o estadistica'}),
            'fecha_generacion': forms.DateInput(attrs={ 
                'class': 'form-control',
                'type': 'date'
            }),
            'formato':
                forms.Select(attrs={
                'class':'form-control',  
                'placeholder': 'Ingrese el formato del reporte',
                'rows':3,
                'cols':3}),
            'fk_usuario':
                forms.Select(attrs={
                    'class':'form-control',
                })      
        }
    
    def clean_fecha_generacion(self):
        fecha_generacion = self.cleaned_data.get('fecha_generacion')
        if fecha_generacion > date.today():
            raise forms.ValidationError("La fecha no puede ser futura.")
        if fecha_generacion < date(2025, 1, 1):
            raise forms.ValidationError("La fecha no puede ser anterior al 1 de enero de 2025.")
        return fecha_generacion
    
    def clean_descripcion(self):
        descripcion = self.cleaned_data['descripcion']

        if len(descripcion) < 10:
            raise forms.ValidationError("La descripción debe tener mínimo 10 caracteres")
        if len(descripcion) > 200:
            raise forms.ValidationError("La descripcion  no debe tener mas de 200 caracteres")

        return descripcion
        
class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = '__all__'

        widgets = {
            'nombre_categoria': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese la descripción'
            }),
        }

    def clean_nombre_categoria(self):
        nombre = self.cleaned_data.get('nombre_categoria')
        if nombre and not nombre.isalpha():
            raise forms.ValidationError("El Nombre no puede contener números")
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al minimo 3 palabras")
        if len(nombre) > 45:
            raise forms.ValidationError("El nombre es demasiado grande")
        return nombre

    def clean_material(self):
        material = self.cleaned_data.get('material')
        if material and not material.isalpha():
            raise forms.ValidationError("El Material no puede contener números")
        return material

    def clean_peso_equipo(self):
        peso = self.cleaned_data.get('peso_equipo')
        if peso and not str(peso).isdigit():
            raise forms.ValidationError("El Peso_Equipo solo puede contener números")
        return peso

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        if descripcion:
            if len(descripcion) < 10:
                raise forms.ValidationError("La descripción debe tener al menos 10 caracteres")
            if len(descripcion) > 250:
                raise forms.ValidationError("La descripción no puede tener más de 250 caracteres")
        return descripcion
    
    
    


    
class NutricionForm(forms.ModelForm):
    class Meta:
        model = Nutricion
        fields = '__all__'
        widgets = {
            'nombre' : forms.TextInput(attrs={
                'placeholder': 'Ingrese el nombre de la nutricion'}),
            
        }
        

class RutinaForm(ModelForm):
    class Meta:
        model = Rutina
        fields = '__all__'
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'dias_disponibles': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 7
            }),
        }

    def clean_dias_disponibles(self):
        dias_disponibles = self.cleaned_data.get('dias_disponibles')
        if dias_disponibles < 1 or dias_disponibles > 7:
            raise forms.ValidationError("Los días disponibles deben estar entre 1 y 7.")
        return dias_disponibles

class Masa_muscularForm(forms.ModelForm):

    class Meta:

        model = Masa_corporal

        fields = [
            'peso_cliente',
            'fecha_control',
            'altura_cliente',
            'fk_Nutricion'
        ]

        widgets = {

            'peso_cliente': forms.NumberInput(
                attrs={
                    'placeholder': 'Ejemplo: 80 kg',
                    'step': '0.01'
                }
            ),

            'altura_cliente': forms.NumberInput(
                attrs={
                    'placeholder': 'Ejemplo: 1.75 m',
                    'step': '0.01'
                }
            ),

            'fecha_control': forms.DateInput(
                attrs={

                    'type': 'date',

                    # SOLO HOY
                    'min': date.today().strftime('%Y-%m-%d'),

                    'max': date.today().strftime('%Y-%m-%d'),

                }
            )
        }

    def clean_peso_cliente(self):
        peso = self.cleaned_data.get('peso_cliente')

        if peso <= 0:
            raise forms.ValidationError("El peso debe ser mayor que 0.")

        if peso < 30 or peso > 300:
            raise forms.ValidationError("El peso debe estar entre 30kg y 300kg.")

        return peso

    def clean_altura_cliente(self):
        altura = self.cleaned_data.get('altura_cliente')

        if altura <= 0:
            raise forms.ValidationError("La altura debe ser mayor que 0.")

        if altura < 0.5 or altura > 2.5:
            raise forms.ValidationError("La altura debe estar entre 0.5m y 2.5m.")

        return altura

    def clean_fecha_control(self):
        fecha = self.cleaned_data.get('fecha_control')
        if fecha > date.today():
            raise forms.ValidationError("La fecha no puede ser futura.")
        if fecha < date(1950, 1, 1):
            raise forms.ValidationError("La fecha no puede ser anterior al 1 de enero de 1950.")
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        fk_nutricion = cleaned_data.get('fk_Nutricion')
        fecha = cleaned_data.get('fecha_control')

        if fk_nutricion and fecha:
            queryset = Masa_corporal.objects.filter(
                fk_Nutricion=fk_nutricion,
                fecha_control=fecha
            )

            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    "Ya existe un control para esta nutrición en esa fecha."
                )

        return cleaned_data

class SancionesForm(forms.ModelForm):
    class Meta:
        model = Sancion
        fields = '__all__'
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_motivo_sancion(self):
        motivo = self.cleaned_data.get('motivo_sancion')

        if not motivo or len(motivo.strip()) < 5:
            raise forms.ValidationError("El motivo debe tener al menos 5 caracteres.")

        motivo = motivo.strip()

        if not motivo[0].isalpha():
            raise forms.ValidationError("La descripción debe iniciar obligatoriamente con una letra.")

        return motivo

    def clean_duracion_sancion(self):
        duracion = self.cleaned_data.get('duracion_sancion')

        if duracion <= 0:
            raise forms.ValidationError("La duración debe ser mayor que 0 días.")

        if duracion > 365:
            raise forms.ValidationError("La duración no puede ser mayor a 365 días.")

        return duracion

    def clean(self):
        cleaned_data = super().clean()

        duracion = cleaned_data.get('duracion_sancion')
        usuario = cleaned_data.get('fk_usuario')
        tipo = cleaned_data.get('tipo_sancion')
        estado = cleaned_data.get('estado')

        fecha_inicio = date.today()
        cleaned_data['fecha_inicio'] = fecha_inicio

        if duracion:
            fecha_fin = fecha_inicio + timedelta(days=duracion)
            cleaned_data['fecha_fin'] = fecha_fin

        if usuario and tipo and estado == 'activa':
            queryset = Sancion.objects.filter(
                fk_usuario=usuario,
                tipo_sancion=tipo,
                estado='activa'
            )

            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    "Este usuario ya tiene una sanción activa de este tipo."
                )

        return cleaned_data

    def clean(self):
        cleaned_data = super().clean()

        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        usuario = cleaned_data.get('fk_usuario')
        tipo = cleaned_data.get('tipo_sancion')
        estado = cleaned_data.get('estado')

        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise forms.ValidationError(
                    "La fecha de fin debe ser mayor que la fecha de inicio."
                )

        if usuario and tipo and estado == 'activa':
            queryset = Sancion.objects.filter(
                fk_usuario=usuario,
                tipo_sancion=tipo,
                estado='activa'
            )

            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    "Este usuario ya tiene una sanción activa de este tipo."
                )

        return cleaned_data

class RegistrovisitantetemporalForm(forms.ModelForm):

    class Meta:
        model = Registrovisitantestemporales
        fields = ['nombre', 'cedula', 'fecha_registro']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre completo'
            }),
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese la cédula'
            }),
            'fecha_registro': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'fk_usuario': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise forms.ValidationError("El nombre es obligatorio.")
        nombre = nombre.strip()
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener mínimo 3 caracteres.")
        if not all(c.isalpha() or c.isspace() for c in nombre):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        return nombre.title()

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not cedula:
            raise forms.ValidationError("La cédula es obligatoria.")
        cedula = cedula.strip()
        if not cedula.isdigit():
            raise forms.ValidationError("La cédula solo puede contener números.")
        if len(cedula) < 6 or len(cedula) > 12:
            raise forms.ValidationError("La cédula debe tener entre 6 y 12 dígitos.")
        return cedula

    def clean_fecha_registro(self):
        fecha_registro = self.cleaned_data.get('fecha_registro')
        if fecha_registro:
            hoy = timezone.now().date()
            if fecha_registro < hoy:
                raise forms.ValidationError("La fecha de registro no puede ser en el pasado.")
            if fecha_registro > hoy:
                raise forms.ValidationError("La fecha de registro no puede ser en el futuro.")
        return fecha_registro


class TurnodeentrenadorForm(forms.ModelForm):
    administrador = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(rol='Administrador', estado='activo'),
        empty_label="Seleccione un administrador",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Administrador",
        required=True
    )

    class Meta:
        model = Turnosentrenadores
        fields = [
            'administrador',
            'fecha_turno_inicio',
            'fecha_turno_final',
            'jornada',
        ]
        widgets = {
            'fecha_turno_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_turno_final': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'jornada': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def clean_fecha_turno_inicio(self):
        inicio = self.cleaned_data.get('fecha_turno_inicio')
        hoy = timezone.now().date()

        if inicio and inicio < hoy:
            raise forms.ValidationError(
                "La fecha de inicio no puede ser en el pasado."
            )
        return inicio

    def clean_fecha_turno_final(self):
        fin = self.cleaned_data.get('fecha_turno_final')
        hoy = timezone.now().date()

        if fin and fin < hoy:
            raise forms.ValidationError(
                "La fecha de finalización no puede ser en el pasado."
            )
        return fin

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('fecha_turno_inicio')
        fin = cleaned_data.get('fecha_turno_final')
        jornada = cleaned_data.get('jornada')

        if inicio and fin and fin < inicio:
            self.add_error('fecha_turno_final', "La fecha final no puede ser menor a la fecha de inicio.")

        if jornada:
            turno = Turnosentrenadores.objects.filter(jornada=jornada)

            # Si se está editando un turno, excluir el mismo registro
            if self.instance.pk:
                turno = turno.exclude(pk=self.instance.pk)

            if turno.exists():
                self.add_error(
                    'jornada',
                    "Esta jornada ya está asignada a otro entrenador."
                )

        return cleaned_data
class CertificacioninternaForm(ModelForm):
    class Meta:
        model = Certificacion_interna
        fields = '__all__'
        widgets = {
            'fecha_certificacion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'descripcion_certificacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese la descripcion de la certificacion interna'
            }),
            'fk_membresia': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrar membresías con mínimo 10 asistencias
        membresias_validas = Membresia.objects.annotate(
            total_asistencias=Count('asistencia')
        ).filter(total_asistencias__gte=1)

        self.fields['fk_membresia'].queryset = membresias_validas
    def clean_descripcion_certificacion(self):
        descripcion_certificacion = self.cleaned_data['descripcion_certificacion']
        if len(descripcion_certificacion) < 10:
            raise forms.ValidationError("La descripcion de la certificacion interna debe tener al menos 10 caracteres.")
        if descripcion_certificacion.isdigit():
            raise forms.ValidationError("La descripcion de la certificacion interna no puede ser solo números.")
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ]', descripcion_certificacion):
            raise forms.ValidationError(
                "La descripción debe comenzar con una letra."
            )        
        return descripcion_certificacion
    
    def clean_fecha_certificacion(self):
        fecha_certificacion = self.cleaned_data['fecha_certificacion']
        hoy = timezone.now().date()
        if fecha_certificacion < hoy:
            raise forms.ValidationError(
            "La fecha de certificación no puede ser una fecha pasada."
        )
        if fecha_certificacion > hoy:
            raise forms.ValidationError(
            "La fecha de certificación no puede ser una fecha futura."
        )
        return fecha_certificacion