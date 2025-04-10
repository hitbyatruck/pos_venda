from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('search/', include('search.urls')),
]