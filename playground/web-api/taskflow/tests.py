from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import pytest
from .models import Team, Project, Task, Comment


@pytest.mark.unit
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
    
    @pytest.mark.slow
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
    
    def test_team_members_relationship(self):
        """Test team members relationship"""
        self.team.members.add(self.user)
        self.assertIn(self.user, self.team.members.all())
        self.assertIn(self.team, self.user.teams.all())
    
    def test_project_cascade_delete(self):
        """Test that deleting a team cascades to projects"""
        project_count = Project.objects.count()
        self.team.delete()
        self.assertEqual(Project.objects.count(), project_count - 1)
    
    def test_task_cascade_delete(self):
        """Test that deleting a project cascades to tasks"""
        task_count = Task.objects.count()
        self.project.delete()
        self.assertEqual(Task.objects.count(), task_count - 1)
    
    def test_comment_task_relationship(self):
        """Test comment belongs to task"""
        comment = Comment.objects.create(
            task=self.task,
            content='Test comment'
        )
        self.assertEqual(comment.task, self.task)
        self.assertIn(comment, self.task.comments.all())
    
    def test_comment_cascade_delete(self):
        """Test that deleting a task cascades to comments"""
        Comment.objects.create(task=self.task, content='Test comment')
        comment_count = Comment.objects.count()
        self.task.delete()
        self.assertEqual(Comment.objects.count(), comment_count - 1)
    
    def test_model_timestamps(self):
        """Test that created_at and updated_at are set correctly"""
        self.assertIsNotNone(self.team.created_at)
        self.assertIsNotNone(self.team.updated_at)
        self.assertIsNotNone(self.project.created_at)
        self.assertIsNotNone(self.project.updated_at)
        self.assertIsNotNone(self.task.created_at)
        self.assertIsNotNone(self.task.updated_at)


@pytest.mark.integration
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

        # Create a manager 
        self.manager_user = User.objects.create_user(
            username='user-manager',
            email='user-manager@example.com',
            password='user-managerpass123',
        )
        self.manager_user.groups.add(Group.objects.create(name='manager'))
        
        # Create team
        self.team = Team.objects.create(
            name='Test Team',
            description='A test team'
        )
        self.team.members.add(self.user, self.manager_user)
        
        # Create project
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            team=self.team
        )
        
        # Create task
        self.task = Task.objects.create(
            title='Test Task',
            description='A test task',
            project=self.project,
            status='pending',
            assignee=self.user
        )
    
    def test_index_endpoint(self):
        """Test welcome endpoint"""
        response = self.client.get('')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('endpoints', response.data)
    
    @pytest.mark.slow
    def test_create_team_success(self):
        """Test team creation by admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'New Team', 'description': 'New team'}
        response = self.client.post('/api/teams/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Team')
    
    
    def test_create_team_manager_success(self):
        """Test team creation by manager"""
        self.client.force_authenticate(user=self.manager_user)
        data = {'name': 'Manager Team', 'description': 'Team created by manager'}
        response = self.client.post('/api/teams/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Manager Team')
    
    def test_create_team_missing_name(self):
        """Test team creation fails without name"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'description': 'Team without name'}
        response = self.client.post('/api/teams/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_teams_authenticated(self):
        """Test listing teams for authenticated users"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/teams/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Team')
        self.assertIn('member_count', response.data[0])
    
    def test_list_teams_unauthenticated(self):
        """Test listing teams fails for unauthenticated users"""
        response = self.client.get('/api/teams/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # Project tests
    def test_create_project_success(self):
        """Test project creation by team member"""
        self.client.force_authenticate(user=self.manager_user)
        data = {
            'name': 'New Project',
            'description': 'A new project',
            'team_id': self.team.id
        }
        response = self.client.post('/api/projects/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Project')
        self.assertEqual(response.data['team_id'], self.team.id)
    
    def test_create_project_unauthorized(self):
        """Test project creation by non-team member"""
        non_member = User.objects.create_user(
            username='nonmember',
            email='non@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=non_member)
        data = {
            'name': 'New Project',
            'description': 'A new project',
            'team_id': self.team.id
        }
        response = self.client.post('/api/projects/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_project_missing_fields(self):
        """Test project creation fails without required fields"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Project without team'}
        response = self.client.post('/api/projects/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_project_invalid_team(self):
        """Test project creation fails with invalid team ID"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'New Project',
            'description': 'A new project',
            'team_id': 99999  # Non-existent team
        }
        response = self.client.post('/api/projects/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_projects_authenticated(self):
        """Test listing projects for authenticated team member"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Project')
        self.assertIn('team_name', response.data[0])
    
    def test_list_projects_unauthenticated(self):
        """Test listing projects fails for unauthenticated users"""
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_projects_non_member(self):
        """Test listing projects for non-team member returns empty"""
        non_member = User.objects.create_user(
            username='nonmember',
            email='non@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=non_member)
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    # Task tests
    
    def test_create_task_invalid_project(self):
        """Test task creation fails with invalid project ID"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'title': 'New Task',
            'description': 'A new task',
            'project_id': 99999  # Non-existent project
        }
        response = self.client.post('/api/tasks/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_tasks_authenticated(self):
        """Test listing tasks for authenticated team member"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Task')
        self.assertIn('project_name', response.data[0])
        self.assertIn('assignee_username', response.data[0])
    
    def test_list_tasks_unauthenticated(self):
        """Test listing tasks fails for unauthenticated users"""
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_tasks_non_member(self):
        """Test listing tasks for non-team member returns empty"""
        non_member = User.objects.create_user(
            username='nonmember',
            email='non@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=non_member)
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    # Comment tests
    def test_create_comment_success(self):
        """Test comment creation by team member"""
        self.client.force_authenticate(user=self.user)
        data = {
            'content': 'Test comment content',
            'task_id': self.task.id
        }
        response = self.client.post('/api/comments/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test comment content')
        self.assertEqual(response.data['task_id'], self.task.id)
    
    def test_create_comment_unauthorized(self):
        """Test comment creation by non-team member"""
        non_member = User.objects.create_user(
            username='nonmember',
            email='non@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=non_member)
        data = {
            'content': 'Test comment content',
            'task_id': self.task.id
        }
        response = self.client.post('/api/comments/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_comment_missing_fields(self):
        """Test comment creation fails without required fields"""
        self.client.force_authenticate(user=self.user)
        data = {'task_id': self.task.id}
        response = self.client.post('/api/comments/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_comment_invalid_task(self):
        """Test comment creation fails with invalid task ID"""
        self.client.force_authenticate(user=self.user)
        data = {
            'content': 'Test comment content',
            'task_id': 99999  # Non-existent task
        }
        response = self.client.post('/api/comments/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_comments_success(self):
        """Test listing comments for task"""
        # Create a comment first
        comment = Comment.objects.create(
            task=self.task,
            content='Test comment'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/tasks/{self.task.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], 'Test comment')
    
    def test_list_comments_unauthorized(self):
        """Test listing comments fails for non-team member"""
        non_member = User.objects.create_user(
            username='nonmember',
            email='non@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=non_member)
        response = self.client.get(f'/api/tasks/{self.task.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_comments_invalid_task(self):
        """Test listing comments fails for invalid task ID"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/tasks/99999/comments/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_comments_empty(self):
        """Test listing comments for task with no comments"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/tasks/{self.task.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


@pytest.mark.unit
class TaskFlowEdgeCasesTest(TestCase):
    """Test edge cases and error conditions"""
    
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
    
    def test_team_name_max_length(self):
        """Test team name respects max length"""
        long_name = 'A' * 200  # Max length
        team = Team.objects.create(name=long_name, description='Test')
        self.assertEqual(team.name, long_name)
    
    def test_project_name_max_length(self):
        """Test project name respects max length"""
        long_name = 'A' * 200  # Max length
        project = Project.objects.create(
            name=long_name,
            description='Test',
            team=self.team
        )
        self.assertEqual(project.name, long_name)
    
    def test_task_title_max_length(self):
        """Test task title respects max length"""
        long_title = 'A' * 200  # Max length
        task = Task.objects.create(
            title=long_title,
            description='Test',
            project=self.project,
            status='pending',
            assignee=self.user
        )
        self.assertEqual(task.title, long_title)
    
    def test_comment_content_blank(self):
        """Test comment content can be blank"""
        task = Task.objects.create(
            title='Test Task',
            description='A test task',
            project=self.project,
            status='pending',
            assignee=self.user
        )
        comment = Comment.objects.create(
            task=task,
            content=''
        )
        self.assertEqual(comment.content, '')
    
    def test_team_description_blank(self):
        """Test team description can be blank"""
        team = Team.objects.create(name='Blank Team', description='')
        self.assertEqual(team.description, '')


@pytest.mark.integration
class TaskFlowPermissionTest(APITestCase):
    """Test permission-based access control"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users with different permission levels
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        admin_group = Group.objects.create(name='admin')
        self.admin_user.groups.add(admin_group)
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='managerpass123'
        )
        manager_group = Group.objects.create(name='manager')
        self.manager_user.groups.add(manager_group)
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpass123'
        )
        
        # Create team and add users
        self.team = Team.objects.create(
            name='Test Team',
            description='A test team'
        )
        self.team.members.add(self.regular_user, self.manager_user)
        
        # Create project
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            team=self.team
        )
        
        # Create task
        self.task = Task.objects.create(
            title='Test Task',
            description='A test task',
            project=self.project,
            status='pending',
            assignee=self.regular_user
        )
    
    def test_admin_can_create_team(self):
        """Test admin can create teams"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Admin Team', 'description': 'Team by admin'}
        response = self.client.post('/api/teams/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_manager_can_create_team(self):
        """Test manager can create teams"""
        self.client.force_authenticate(user=self.manager_user)
        data = {'name': 'Manager Team', 'description': 'Team by manager'}
        response = self.client.post('/api/teams/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_admin_can_create_project(self):
        """Test admin can create projects"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Admin Project',
            'description': 'Project by admin',
            'team_id': self.team.id
        }
        self.team.members.add(self.admin_user)
        response = self.client.post('/api/projects/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_manager_can_create_project(self):
        """Test manager can create projects"""
        self.client.force_authenticate(user=self.manager_user)
        data = {
            'name': 'Manager Project',
            'description': 'Project by manager',
            'team_id': self.team.id
        }
        response = self.client.post('/api/projects/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_regular_user_cannot_create_project(self):
        """Test regular user cannot create projects"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'name': 'Regular Project',
            'description': 'Project by regular user',
            'team_id': self.team.id
        }
        print(f'{self.regular_user.groups}')
        response = self.client.post('/api/projects/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_create_task(self):
        """Test admin can create tasks"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'title': 'Admin Task',
            'description': 'Task by admin',
            'project_id': self.project.id
        }
        self.team.members.add(self.admin_user)
        response = self.client.post('/api/tasks/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_manager_can_create_task(self):
        """Test manager can create tasks"""
        self.client.force_authenticate(user=self.manager_user)
        data = {
            'title': 'Manager Task',
            'description': 'Task by manager',
            'project_id': self.project.id
        }
        response = self.client.post('/api/tasks/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_regular_user_cannot_create_task(self):
        """Test regular user cannot create tasks"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'title': 'Regular Task',
            'description': 'Task by regular user',
            'project_id': self.project.id
        }
        response = self.client.post('/api/tasks/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_team_member_can_create_comment(self):
        """Test team member can create comments"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'content': 'Comment by team member',
            'task_id': self.task.id
        }
        response = self.client.post('/api/comments/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_non_team_member_cannot_create_comment(self):
        """Test non-team member cannot create comments"""
        non_member = User.objects.create_user(
            username='nonmember',
            email='non@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=non_member)
        data = {
            'content': 'Comment by non-member',
            'task_id': self.task.id
        }
        response = self.client.post('/api/comments/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
