from django.contrib import admin
from .apps import TaskflowConfig, Team, Project, Task, Comment

# Register your models here.
admin.site.register(TaskflowConfig)
admin.site.register(Team)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Comment)
