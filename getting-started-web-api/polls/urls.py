from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    path('items/', views.ItemListCreateAPIView.as_view(), name='item-list-create'),
    path('', views.index, name='index'),
    
    # Authentication endpoints
    path('auth/verify-token/', auth_views.verify_token, name='verify-token'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    path('auth/user-info/', auth_views.user_info, name='user-info'),
    path('auth/sso-config/', auth_views.sso_config, name='sso-config'),
]