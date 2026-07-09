from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.urls import reverse_lazy
# Create your views here.

class LoginFormView(LoginView):
    template_name = 'login/login.html'
    redirect_authenticated_user = True
    next_page= reverse_lazy('gimnasio:dashboard')  
    print('Login')  
class logoutFormView(LogoutView):
    next_page = reverse_lazy('login:login')
    
class RegisterFormView(TemplateView):
    template_name = 'login/registro.html'
    success_url = reverse_lazy('login:login')
    
class PasswordResetView(TemplateView):
    template_name = 'login/recuperar.html'
    success_url = reverse_lazy('login:login')
    
class ConfirmarCorreoView(TemplateView):
    template_name = 'login/confirmar_correo.html'