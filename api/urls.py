from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_animation, name='generate_animation'),
    path('generate/status/<str:task_id>/', views.get_task_status, name='get_task_status'),
    path('preview/', views.generate_preview, name='generate_preview'),
]
