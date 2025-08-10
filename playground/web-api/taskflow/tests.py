from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Team, Project, Task


class TaskFlowModelsTest(TestCase):
    """Basic model tests"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.team = Team.objects.create(
            name='Test Team',
            description='A test team'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            team=self.team
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='A test task',
            project=self.project,
            status='pending',
            assignee=self.user
        )
    
    def test_team_creation(self):
        """Test team creation"""
        self.assertEqual(self.team.name, 'Test Team')
        self.assertIsNotNone(self.team.created_at)
    
    def test_project_team_relationship(self):
        """Test project belongs to team"""
        self.assertEqual(self.project.team, self.team)
        self.assertIn(self.project, self.team.projects.all())
    
    def test_task_project_relationship(self):
        """Test task belongs to project"""
        self.assertEqual(self.task.project, self.project)
        self.assertEqual(self.task.assignee, self.user)


class TaskFlowAPITest(APITestCase):
    """Basic API tests"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        admin_group = Group.objects.create(name='admin')
        team_admin_group = Group.objects.create(name='team-admin')
        self.admin_user.groups.add(admin_group, team_admin_group)
        
        # Create regular user
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        
        # Create team
        self.team = Team.objects.create(
            name='Test Team',
            description='A test team'
        )
        self.team.members.add(self.user)
    
    def test_index_endpoint(self):
        """Test welcome endpoint"""
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_create_team_success(self):
        """Test team creation by admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'New Team', 'description': 'New team'}
        response = self.client.post('/api/teams/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Team')
    
    def test_list_teams_authenticated(self):
        """Test listing teams for authenticated users"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/teams/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Team')
    
    def test_list_teams_unauthenticated(self):
        """Test listing teams fails for unauthenticated users"""
        response = self.client.get('/api/teams/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
