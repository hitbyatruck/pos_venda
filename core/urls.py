from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # Settings URLs
    path('settings/', views.settings_dashboard, name='settings_dashboard'),
    path('settings/users/', views.user_management, name='user_management'),
    path('settings/roles/', views.roles_permissions, name='roles_permissions'),
    path('settings/client-sectors/', views.settings_client_sectors, name='settings_client_sectors'),
    path('settings/contact-types/', views.settings_contact_types, name='settings_contact_types'),
    path('settings/equipment-categories/', views.settings_equipment_categories, name='settings_equipment_categories'),

    # User management CRUD operations
    path('settings/users/add/', views.user_add, name='user_add'),
    path('settings/users/edit/', views.user_edit, name='user_edit'),
    path('settings/users/delete/', views.user_delete, name='user_delete'),

    # Group management CRUD operations
    path('settings/groups/add/', views.group_add, name='group_add'),
    path('settings/groups/edit/', views.group_edit, name='group_edit'),
    path('settings/groups/delete/', views.group_delete, name='group_delete'),
    path('settings/groups/permissions/', views.group_permissions, name='group_permissions'),  # Add missing URL
    path('settings/groups/<int:group_id>/permissions/', views.get_group_permissions, name='get_group_permissions'),  # Add AJAX endpoint

    path('search/', include('search.urls')),
]