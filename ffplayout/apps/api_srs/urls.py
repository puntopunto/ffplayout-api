from django.urls import path

from . import views

app_name = 'api_srs'

urlpatterns = [
    path('srs/publish/', views.Publish.as_view()),
]
