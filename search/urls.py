from django.urls import path
from . import views

urlpatterns = [
    # Main search route - using the search app's view only
    path('', views.search_global, name='search_global'),
]
