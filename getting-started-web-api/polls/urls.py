from django.urls import path

from . import views

urlpatterns = [
    path('items/', views.ItemListCreateAPIView.as_view(), name='item-list-create'),
    path('', views.index, name='index'),
]