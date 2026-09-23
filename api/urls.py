from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_animation, name='generate_animation'),
    path('generate/status/<str:task_id>/', views.get_task_status, name='get_task_status'),
    path('preview/', views.generate_preview, name='generate_preview'),
    path('open-file/', views.open_file, name='open_file'),
    path('open-location/', views.open_location, name='open_location'),
    path('settings/storage/', views.storage_setting_api, name='storage_setting'),
    path('settings/browse/', views.browse_storage_path, name='browse_storage'),
]
