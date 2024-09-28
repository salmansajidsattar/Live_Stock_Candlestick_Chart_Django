from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path('', views.stock_chart, name='stock_chart'),
]
