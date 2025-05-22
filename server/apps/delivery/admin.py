from django.contrib import admin

from apps.delivery.models import City, PickupPoint

admin.site.register(City)
admin.site.register(PickupPoint)
