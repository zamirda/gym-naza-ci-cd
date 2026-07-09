from django.urls import path
from login.views import *
from django.contrib.auth import views as auth_views
from gimnasio.forms import CustomPasswordResetForm
app_name = 'login'
urlpatterns = [
    path('login/', LoginFormView.as_view(), name='login'),
    path('logout/', logoutFormView.as_view(), name='logout'),
    path('recuperar_credenciales/', 
         auth_views.PasswordResetView.as_view(
             template_name='login/confirmar_correo.html',
             success_url=reverse_lazy('login:password_reset_done'), # Usa reverse_lazy aquí
             email_template_name='login/password_reset_email.html'
         ), 
         name="password_reset"),
    
    path('password_reset_done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='login/password_reset_sent.html'), 
         name="password_reset_done"),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name="login/password_reset_form.html",
             success_url=reverse_lazy('login:password_reset_complete') # Agrega esto por seguridad
         ), 
         name="password_reset_confirm"),
         
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="login/password_reset_done.html"), 
         name="password_reset_complete"),
]