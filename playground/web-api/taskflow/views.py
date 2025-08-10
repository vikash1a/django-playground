from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Team, Project, Task, Comment
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required, user_passes_test
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

# Create your views here.
@api_view(['GET'])
@permission_classes([])  # Allow anonymous access
def index(request):
    return Response({
        "message": "Welcome to TaskFlow API",
        "endpoints": {
            "admin": "/admin/",
            "api_docs": "/api/docs/",
            "teams": "/api/teams/",
            "projects": "/api/projects/",
            "tasks": "/api/tasks/"
        }
    })

# Team views
@extend_schema(
    tags=['teams'],
    summary="Create a new team",
    description="Create a new team. Only admin users can create teams.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': 'Team name'},
                'description': {'type': 'string', 'description': 'Team description'}
            },
            'required': ['name']
        }
    },
    responses={
        201: {
            'description': 'Team created successfully',
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'description': {'type': 'string'},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            }
        },
        400: {'description': 'Bad request - missing required fields'},
        403: {'description': 'Forbidden - user is not an admin'}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_team(request):
    name = request.data.get('name')
    description = request.data.get('description')
    
    if not name:
        return Response({"detail": "Team name is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    team = Team.objects.create(name=name, description=description)
    return Response({
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
    }, status=status.HTTP_201_CREATED)

@extend_schema(
    tags=['teams'],
    summary="List all teams",
    description="Retrieve a list of all teams. User must be authenticated.",
    responses={
        200: {
            'description': 'List of teams retrieved successfully',
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'member_count': {'type': 'integer'},
                    'created_at': {'type': 'string', 'format': 'date-time'},
                    'updated_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_teams(request):
    teams = Team.objects.all()
    team_data = []
    for team in teams:
        team_data.append({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "member_count": team.members.count(),
            "created_at": team.created_at,
            "updated_at": team.updated_at,
        })
    return Response(team_data)

@extend_schema(
    tags=['teams'],
    summary="Get, update, or delete a team",
    description="Retrieve, update, or delete a specific team. Only team admins can modify teams.",
    parameters=[
        OpenApiParameter(
            name='team_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID of the team'
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': 'Team name'},
                'description': {'type': 'string', 'description': 'Team description'}
            }
        }
    },
    responses={
        200: {
            'description': 'Team details retrieved successfully',
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'description': {'type': 'string'},
                'members': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'}
                        }
                    }
                },
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            }
        },
        403: {'description': 'Forbidden - user is not a team admin'},
        404: {'description': 'Team not found'}
    }
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'GET':
        return Response({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "members": [{"id": member.id, "username": member.username} for member in team.members.all()],
            "created_at": team.created_at,
            "updated_at": team.updated_at,
        })
    
    elif request.method == 'PUT':
        if not request.user.groups.filter(name='admin').exists():
            return Response({"detail": "You do not have permission to perform this action."}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        name = request.data.get('name', team.name)
        description = request.data.get('description', team.description)
        
        team.name = name
        team.description = description
        team.save()
        
        return Response({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "created_at": team.created_at,
            "updated_at": team.updated_at,
        })
    
    elif request.method == 'DELETE':
        if not request.user.groups.filter(name='admin').exists():
            return Response({"detail": "You do not have permission to perform this action."}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Project views
@extend_schema(
    tags=['projects'],
    summary="Create a new project",
    description="Create a new project within a team. User must be a member of the team.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': 'Project name'},
                'description': {'type': 'string', 'description': 'Project description'},
                'team_id': {'type': 'integer', 'description': 'ID of the team'}
            },
            'required': ['name', 'team_id']
        }
    },
    responses={
        201: {
            'description': 'Project created successfully',
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'description': {'type': 'string'},
                'team_id': {'type': 'integer'},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            }
        },
        400: {'description': 'Bad request - missing required fields'},
        403: {'description': 'Forbidden - user is not a team member'},
        404: {'description': 'Team not found'}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project(request):
    name = request.data.get('name')
    description = request.data.get('description')
    team_id = request.data.get('team_id')
    
    if not all([name, team_id]):
        return Response({"detail": "Project name and team_id are required."}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is member of the team
    if not team.members.filter(id=request.user.id).exists():
        return Response({"detail": "You must be a member of the team to create projects."}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    project = Project.objects.create(name=name, description=description, team=team)
    return Response({
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "team_id": project.team.id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }, status=status.HTTP_201_CREATED)

@extend_schema(
    tags=['projects'],
    summary="List user's projects",
    description="Retrieve a list of projects from teams the user is a member of.",
    responses={
        200: {
            'description': 'List of projects retrieved successfully',
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'team_name': {'type': 'string'},
                    'created_at': {'type': 'string', 'format': 'date-time'},
                    'updated_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_projects(request):
    # Show projects from teams the user is a member of
    user_teams = request.user.teams.all()
    projects = Project.objects.filter(team__in=user_teams)
    
    project_data = []
    for project in projects:
        project_data.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "team_name": project.team.name,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        })
    return Response(project_data)

# Task views
@extend_schema(
    tags=['tasks'],
    summary="Create a new task",
    description="Create a new task within a project. User must be a member of the project's team.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string', 'description': 'Task title'},
                'description': {'type': 'string', 'description': 'Task description'},
                'project_id': {'type': 'integer', 'description': 'ID of the project'},
                'status': {
                    'type': 'string', 
                    'description': 'Task status',
                    'enum': ['pending', 'in_progress', 'completed', 'cancelled']
                },
                'assignee_id': {'type': 'integer', 'description': 'ID of the assignee (optional)'}
            },
            'required': ['title', 'project_id']
        }
    },
    responses={
        201: {
            'description': 'Task created successfully',
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'status': {'type': 'string'},
                'project_id': {'type': 'integer'},
                'assignee_id': {'type': 'integer'},
                'assignee_username': {'type': 'string'},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'updated_at': {'type': 'string', 'format': 'date-time'}
            }
        },
        400: {'description': 'Bad request - missing required fields or invalid assignee'},
        403: {'description': 'Forbidden - user is not a team member'},
        404: {'description': 'Project not found'}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_task(request):
    title = request.data.get('title')
    description = request.data.get('description')
    project_id = request.data.get('project_id')
    status = request.data.get('status', 'pending')
    assignee_id = request.data.get('assignee_id')
    
    if not all([title, project_id]):
        return Response({"detail": "Task title and project_id are required."}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is member of the project's team
    if not project.team.members.filter(id=request.user.id).exists():
        return Response({"detail": "You must be a member of the team to create tasks."}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    # If assignee_id is provided, verify they are also a team member
    assignee = None
    if assignee_id:
        assignee = get_object_or_404(User, id=assignee_id)
        if not project.team.members.filter(id=assignee.id).exists():
            return Response({"detail": "Assignee must be a member of the team."}, 
                           status=status.HTTP_400_BAD_REQUEST)
    else:
        assignee = request.user
    
    task = Task.objects.create(
        title=title,
        description=description,
        project=project,
        status=status,
        assignee=assignee
    )
    
    return Response({
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "project_id": task.project.id,
        "assignee_id": task.assignee.id,
        "assignee_username": task.assignee.username,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }, status=status.HTTP_201_CREATED)

@extend_schema(
    tags=['tasks'],
    summary="List user's tasks",
    description="Retrieve a list of tasks from projects in teams the user is a member of.",
    responses={
        200: {
            'description': 'List of tasks retrieved successfully',
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'title': {'type': 'string'},
                    'status': {'type': 'string'},
                    'project_name': {'type': 'string'},
                    'assignee_username': {'type': 'string'},
                    'created_at': {'type': 'string', 'format': 'date-time'}
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tasks(request):
    # Show tasks from projects in teams the user is a member of
    user_teams = request.user.teams.all()
    tasks = Task.objects.filter(project__team__in=user_teams)
    
    task_data = []
    for task in tasks:
        task_data.append({
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "project_name": task.project.name,
            "assignee_username": task.assignee.username,
            "created_at": task.created_at,
        })
    return Response(task_data)

# Comment views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request):
    content = request.data.get('content')
    task_id = request.data.get('task_id')
    
    if not all([content, task_id]):
        return Response({"detail": "Comment content and task_id are required."}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user is member of the task's project's team
    if not task.project.team.members.filter(id=request.user.id).exists():
        return Response({"detail": "You must be a member of the team to add comments."}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    comment = Comment.objects.create(
        task=task,
        content=content
    )
    
    return Response({
        "id": comment.id,
        "content": comment.content,
        "task_id": comment.task.id,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_comments(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user is member of the task's project's team
    if not task.project.team.members.filter(id=request.user.id).exists():
        return Response({"detail": "You must be a member of the team to view comments."}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    comments = Comment.objects.filter(task=task)
    comment_data = []
    for comment in comments:
        comment_data.append({
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
        })
    return Response(comment_data)