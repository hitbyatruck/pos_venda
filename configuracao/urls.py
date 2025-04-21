from django.urls import path
from . import views

app_name = 'configuracao'

urlpatterns = [
    # Dashboard and main settings
    path('', views.dashboard, name='dashboard'),
    path('general/', views.general_settings, name='general_settings'),
    path('email/', views.email_settings, name='email_settings'),
    path('notifications/', views.notification_settings, name='notification_settings'),
    path('appearance/', views.appearance_settings, name='appearance_settings'),

    # Backups
    path('backup/', views.backup_settings, name='backup_settings'),

    # Custom Fields
    path('custom-fields/', views.custom_fields, name='custom_fields'),
    path('custom-fields/add/', views.add_custom_field, name='add_custom_field'),
    path('custom-fields/<int:field_id>/edit/', views.edit_custom_field, name='edit_custom_field'),
    path('custom-fields/<int:field_id>/delete/', views.delete_custom_field, name='delete_custom_field'),

    # System maintenance
    path('maintenance/', views.system_maintenance, name='system_maintenance'),
]
