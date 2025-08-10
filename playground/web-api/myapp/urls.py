"""
URL configuration for myapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from taskflow import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Swagger/OpenAPI documentation endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Taskflow API endpoints
    path('api/', include([
        # Team endpoints
        path('teams/', views.list_teams, name='list_teams'),
        path('teams/create/', views.create_team, name='create_team'),
        path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
        
        # Project endpoints
        path('projects/', views.list_projects, name='list_projects'),
        path('projects/create/', views.create_project, name='create_project'),
        
        # Task endpoints
        path('tasks/', views.list_tasks, name='list_tasks'),
        path('tasks/create/', views.create_task, name='create_task'),
        
        # Comment endpoints
        path('comments/create/', views.create_comment, name='create_comment'),
        path('tasks/<int:task_id>/comments/', views.list_comments, name='list_comments'),
    ])),
    
    # Root endpoint
    path('', views.index, name='index'),
]
