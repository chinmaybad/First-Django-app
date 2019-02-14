from django.contrib import admin

from .models import Post
from .models import Companies
from .models import Strategy
from .models import Refreshed

admin.site.register(Companies)
admin.site.register(Strategy)
admin.site.register(Refreshed)
# Register your models here.
