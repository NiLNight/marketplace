from django.contrib import admin
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'value', 'create_time', 'ip_address')
    list_filter = ('value', 'create_time')
    search_fields = ('product__title', 'user__username', 'ip_address')
