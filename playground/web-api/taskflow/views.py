from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import Team, Project, Task, Comment
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required, user_passes_test

# Create your views here.
def index():
    return HttpResponse("Hello, world. You're at the taskflow index.")

# Team views
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