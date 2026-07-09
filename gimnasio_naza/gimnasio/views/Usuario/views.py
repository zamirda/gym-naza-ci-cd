from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, CreateView, UpdateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import update_session_auth_hash

from gimnasio.models import Usuario
from gimnasio.forms import UsuarioForm, UserForm

# ==========================================
# LISTAR
# ==========================================
class UsuarioListView(LoginRequiredMixin, ListView):
    model = Usuario
    template_name = 'Usuarios/listar.html'
    # Cambiado de 'usuarios' para que coincida con el template
    context_object_name = 'object_list'
    ordering = ['-id']

    def get_queryset(self):
        return Usuario.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Listado de Usuarios'
        context['crear_url'] = reverse_lazy('gimnasio:crear_usuario')
        return context


# ==========================================
# CREAR
# ==========================================
class UsuarioCreateView(LoginRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = 'Usuarios/crear.html'
    success_url = reverse_lazy('gimnasio:listar_usuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if 'user_form' not in context:
            if self.request.POST:
                context['user_form'] = UserForm(self.request.POST)
            else:
                context['user_form'] = UserForm()

        context['titulo'] = 'Crear Usuario'
        return context

    def post(self, request, *args, **kwargs):
        self.object = None

        usuario_form = UsuarioForm(
            request.POST,
            request.FILES
        )

        user_form = UserForm(request.POST)

        if usuario_form.is_valid() and user_form.is_valid():
            return self.form_valid(usuario_form, user_form)

        print("ERRORES USUARIO:")
        print(usuario_form.errors)

        print("ERRORES USER:")
        print(user_form.errors)

        return self.form_invalid(usuario_form, user_form)

    def form_valid(self, usuario_form, user_form):
        try:
            user = user_form.save(commit=False)

            password = user_form.cleaned_data.get('password')

            if password:
                user.set_password(password)

            user.save()

            usuario = usuario_form.save(commit=False)
            usuario.user = user
            usuario.estado = 'activo'
            usuario.save()

            messages.success(
                self.request,
                'Usuario creado correctamente'
            )

            return redirect('gimnasio:listar_usuario')

        except Exception as e:
            print("ERROR AL GUARDAR:", e)

            messages.error(
                self.request,
                f'Error al crear usuario: {e}'
            )

            return self.form_invalid(usuario_form, user_form)

    def form_invalid(self, usuario_form, user_form):
        return self.render_to_response(
            self.get_context_data(
                form=usuario_form,
                user_form=user_form
            )
        )


# ==========================================
# ACTUALIZAR
# ==========================================
class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = 'Usuarios/crear.html'  # Usa el mismo template que crear
    success_url = reverse_lazy('gimnasio:listar_usuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Usuario'
        
        usuario = self.object
        user = usuario.user
        print(usuario.documento)
        if self.request.POST:
            context['user_form'] = UserForm(self.request.POST, instance=user)
        else:
            context['user_form'] = UserForm(instance=user)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        usuario_form = self.get_form()
        user_form = UserForm(request.POST, instance=self.object.user)

        if usuario_form.is_valid() and user_form.is_valid():
            return self.form_valid(usuario_form, user_form)
        return self.form_invalid(usuario_form, user_form)

    def form_valid(self, usuario_form, user_form):
        user = user_form.save(commit=False)
        password = user_form.cleaned_data.get('password')

        if password:
            user.set_password(password)
            user.save()
            # Mantiene la sesión activa del usuario autenticado tras el cambio de contraseña
            update_session_auth_hash(self.request, user)
        else:
            user.save()

        usuario_form.save() # Actualiza los datos del perfil (incluyendo el nuevo rol asignado)

        messages.success(self.request, 'Usuario actualizado correctamente')
        return redirect(self.success_url)

    def form_invalid(self, usuario_form, user_form):
        return self.render_to_response(
            self.get_context_data(form=usuario_form, user_form=user_form)
        )


# ==========================================
# ELIMINAR / COUT_DOWN ESTADO
# ==========================================
class UsuarioDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)

        usuario.user.is_active = not usuario.user.is_active
        usuario.user.save()

        # Corrección semántica: de 'desactivo' a 'inactivo' para coincidir con tu HTML anterior
        usuario.estado = 'activo' if usuario.user.is_active else 'inactivo'
        usuario.save()

        estado = 'activado' if usuario.user.is_active else 'desactivado'
        messages.success(request, f'Usuario {estado} correctamente')
        return redirect('gimnasio:listar_usuario')


# =============================
# ASIGNAR ROL A USUARIO
# =============================
class UsuarioRolUpdateView(UpdateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = 'Usuarios/asignar_rol.html'
    success_url = reverse_lazy('gimnasio:listar_usuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Asignar Rol'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Rol asignado correctamente")
        return super().form_valid(form)
    
from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin

class PerfilView(LoginRequiredMixin, View):
    template_name = "Usuarios/perfil.html"

    def get(self, request):
        return render(request, self.template_name, {'user': request.user})