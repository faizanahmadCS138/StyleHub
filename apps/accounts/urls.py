from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────
    path('login/',    views.login_view,    name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/',   views.logout_view,   name='logout'),

    # ── Password Reset ────────────────────────────────────
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset_form.html',
             html_email_template_name='accounts/emails/password_reset_email.html',
             email_template_name='accounts/emails/password_reset_email.html',
             subject_template_name='accounts/emails/password_reset_subject.txt',
            
             success_url='/accounts/password-reset/done/'
         ), 
         name='password_reset'),

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password-reset/complete/'
         ), 
         name='password_reset_confirm'),

    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    # ── Profile ───────────────────────────────────────────
    path('profile/',  views.profile_view,  name='profile'),

    # ── Addresses ─────────────────────────────────────────
    path('addresses/',              views.address_list_view,   name='addresses'),
    path('addresses/add/',          views.address_create_view, name='address-add'),
    path('addresses/<int:pk>/edit/',views.address_edit_view,   name='address-edit'),
    path('addresses/<int:pk>/delete/', views.address_delete_view, name='address-delete'),
]
