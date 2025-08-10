### Set up
- create a virtual env
- pip install django
- django-admin startproject myapp .
- django-admin startapp core 
- python manage.py makemigrations
- python manage.py migrate
- python manage.py createsuperuser --username admin --email admin@example.com --password admin123
- python manage.py runserver


# Django API Project – Team Task Management

**Goal:**  
Build an API for managing teams, projects, and tasks.  
- **Phase 1**: Django authentication + authorization (JWT)  
- **Phase 2**: Google SSO & Okta SSO for authentication, Django for authorization  

---

## 1. Overview
The API will allow teams to manage projects and tasks.  
- **Authentication**: Phase 1 → Django JWT, Phase 2 → Google & Okta SSO.  
- **Authorization**: Role-based using Django Groups & Permissions.  

---

## 2. Entities / Data Models


### Team
| Field       | Type           | Notes |
|-------------|---------------|-------|
| id          | UUID/Int      | Primary key |
| name        | String        | Unique |
| description | Text          | Optional |
| members     | Many-to-Many (User) | Users in the team |
| created_at  | DateTime      | Auto |

---

### Project
| Field       | Type           | Notes |
|-------------|---------------|-------|
| id          | UUID/Int      | Primary key |
| name        | String        | Unique within a team |
| description | Text          | Optional |
| team        | ForeignKey (Team) | Project belongs to one team |
| created_by  | ForeignKey (User) | Project creator |
| created_at  | DateTime      | Auto |

---

### Task
| Field       | Type           | Notes |
|-------------|---------------|-------|
| id          | UUID/Int      | Primary key |
| title       | String        |  |
| description | Text          | Optional |
| status      | Enum (todo, in_progress, done) | Default: todo |
| priority    | Enum (low, medium, high) | Default: medium |
| due_date    | Date          | Optional |
| project     | ForeignKey (Project) | Task belongs to a project |
| assignee    | ForeignKey (User) | Optional |
| created_by  | ForeignKey (User) | Task creator |
| created_at  | DateTime      | Auto |
| updated_at  | DateTime      | Auto |

---

### Comment
| Field       | Type           | Notes |
|-------------|---------------|-------|
| id          | UUID/Int      | Primary key |
| task        | ForeignKey (Task) | Comment belongs to a task |
| author      | ForeignKey (User) | Comment creator |
| content     | Text          |  |
| created_at  | DateTime      | Auto |

---

## 3. Functional Requirements

### Phase 1 – Django Auth + Authorization

#### Authentication
- User registration endpoint (`/api/auth/register`)
- User login endpoint (`/api/auth/login`) → JWT access + refresh tokens
- Token refresh endpoint (`/api/auth/refresh`)

#### Authorization
- Groups: `admin`, `manager`, `member` (via Django groups)
- Admin: full access
- Manager: manage projects/tasks for their team
- Member: manage only tasks assigned to them

#### Core APIs
- **Teams**
  - Create team (admin only)
  - Add/remove team members (admin/manager)
  - View team details (team members only)
- **Projects**
  - CRUD projects (admin/manager for their team)
  - View projects for a team (members)
- **Tasks**
  - CRUD tasks (admin/manager for their team)
  - Member can update their assigned tasks’ status
  - Filter by status, priority, due date
- **Comments**
  - Add comment to task
  - View comments for a task
- **User Profile**
  - `/api/me/` → Get logged-in user profile

---

### Phase 2 – Google SSO + Okta SSO

#### Google SSO
- Implement using `social-auth-app-django`
- On first login:
  - Create new Django user if email not found
  - Assign default role = `member`
- On subsequent login:
  - Update profile info (name, picture) if changed

#### Okta SSO
- Implement using `mozilla-django-oidc` or `python-social-auth`
- Same user creation & role assignment flow as Google

#### Unified Login Flow
- Frontend shows:
  - “Login with Google”
  - “Login with Okta”
- Backend maps SSO user → Django user → permissions
- JWT returned for API access

---

## 4. Non-Functional Requirements
- Database: PostgreSQL (preferred)
- API documentation: `drf-spectacular` or `drf-yasg`
- Background tasks: Celery + Redis (optional for sending notifications)
- Logging: Django logging + DRF exception handling
- Testing: Unit tests for auth, permissions, and core APIs
- Rate limiting: DRF throttling

---

## 5. Example API Endpoints
