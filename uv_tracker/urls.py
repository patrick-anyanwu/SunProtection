from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('uv-index/', views.uv_index, name='uv_index'),
    path('address-suggestions/', views.address_suggestions, name='address_suggestions'),
    path("personalization/", views.personalization, name="personalization"),
    path('uv-impact/', views.uv_impact, name='uv_impact'),
    path('set-reminder/', views.set_reminder, name='set_reminder'),
    path('clothing/', views.clothing, name='clothing'),
]
