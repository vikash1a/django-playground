# Django REST API Service

A Django REST API service built with Django REST Framework that provides a simple CRUD API for managing items.

## Features

- Django 4.2+ with Django REST Framework
- PostgreSQL database support
- Docker and Docker Compose setup
- RESTful API endpoints
- SQLite database for development

## Prerequisites

- Python 3.8+
- pip
- Docker and Docker Compose (for containerized deployment)
- PostgreSQL (optional, for production)

## Quick Start

### Option 1: Local Development (SQLite)

1. **Clone the repository and navigate to the API directory:**
   ```bash
   cd getting-started-web-api
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

   The API will be available at `http://localhost:8000`

### Option 2: Docker Deployment (PostgreSQL)

1. **Navigate to the API directory:**
   ```bash
   cd getting-started-web-api
   ```

2. **Build and start the services:**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - PostgreSQL database on port 5432
   - Django API server on port 8000

3. **Run migrations in the container:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. **Create a superuser (optional):**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## API Endpoints

### Base URL
- Local: `http://localhost:8000`
- Docker: `http://localhost:8000`

### Available Endpoints

#### Items API
- **GET** `/polls/items/` - List all items
- **POST** `/polls/items/` - Create a new item

#### Admin Interface
- **GET** `/admin/` - Django admin interface

### API Usage Examples

#### List all items
```bash
curl http://localhost:8000/polls/items/
```

#### Create a new item
```bash
curl -X POST http://localhost:8000/polls/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Sample Item", "description": "This is a sample item"}'
```

#### Get admin interface
```bash
curl http://localhost:8000/admin/
```

## Data Models

### Item Model
- `id` - Primary key (auto-generated)
- `name` - Item name (CharField, max 100 characters)
- `description` - Item description (TextField, optional)

## Development

### Project Structure
```
getting-started-web-api/
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile           # Docker image definition
├── mysite/              # Main Django project
│   ├── settings.py      # Django settings
│   ├── urls.py          # Main URL configuration
│   └── wsgi.py          # WSGI application
└── polls/               # Django app
    ├── models.py        # Data models
    ├── serializers.py   # DRF serializers
    ├── views.py         # API views
    └── urls.py          # App URL configuration
```

### Adding New Models

1. **Create a model in `polls/models.py`:**
   ```python
   class NewModel(models.Model):
       field1 = models.CharField(max_length=100)
       field2 = models.TextField()
   ```

2. **Create a serializer in `polls/serializers.py`:**
   ```python
   class NewModelSerializer(serializers.ModelSerializer):
       class Meta:
           model = NewModel
           fields = ['id', 'field1', 'field2']
   ```

3. **Add views in `polls/views.py`:**
   ```python
   class NewModelListCreateAPIView(generics.ListCreateAPIView):
       queryset = NewModel.objects.all()
       serializer_class = NewModelSerializer
   ```

4. **Add URLs in `polls/urls.py`:**
   ```python
   path('newmodel/', views.NewModelListCreateAPIView.as_view(), name='newmodel-list-create'),
   ```

5. **Create and run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Environment Variables

### Docker Environment Variables
- `DEBUG` - Django debug mode (default: 1)
- `DB_NAME` - PostgreSQL database name (default: django_db)
- `DB_USER` - PostgreSQL username (default: django_user)
- `DB_PASSWORD` - PostgreSQL password (default: django_pass)
- `DB_HOST` - PostgreSQL host (default: db)
- `DB_PORT` - PostgreSQL port (default: 5432)

## Database Configuration

### SQLite (Development)
The project is configured to use SQLite by default for development:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### PostgreSQL (Production)
For production, update the database configuration in `mysite/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'django_db'),
        'USER': os.environ.get('DB_USER', 'django_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'django_pass'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Database connection issues:**
   - Ensure PostgreSQL is running (Docker: `docker-compose up db`)
   - Check database credentials in environment variables

3. **Migration issues:**
   ```bash
   python manage.py makemigrations --dry-run
   python manage.py showmigrations
   ```

4. **Docker issues:**
   ```bash
   # Rebuild containers
   docker-compose down
   docker-compose up --build
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE). 