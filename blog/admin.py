from django.contrib import admin

from .models import Post
from .models import Companies
from .models import Strategy
from .models import Indicators

admin.site.register(Companies)
admin.site.register(Strategy)
admin.site.register(Indicators)
# Register your models here.
