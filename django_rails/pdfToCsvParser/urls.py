from django.urls import path
from . import views

urlpatterns = [
	path('send_pdf', views.send_pdf, name='send_pdf'),
	path('', views.parser, name='home'),
]