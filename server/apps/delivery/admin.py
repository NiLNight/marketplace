from django.contrib import admin

from apps.delivery.models import Delivery, City, PickupPoint

admin.site.register(Delivery)
admin.site.register(City)
admin.site.register(PickupPoint)
