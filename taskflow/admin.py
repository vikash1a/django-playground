from django.contrib import admin
from .models import Team, Project, Task, Comment


# Register your models here.
admin.site.register(Team)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Comment)
