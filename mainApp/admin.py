from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Worker)
admin.site.register(Machine)
admin.site.register(Task)
admin.site.register(Telemetry)
admin.site.register(Replacement)
admin.site.register(Failure)
admin.site.register(Error)