from django.db import models

# Create your models here.
class FuelStation(models.Model):
    truckstop_id = models.IntegerField()
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)

    rack_id = models.IntegerField(null=True, blank=True)

    retail_price = models.DecimalField(max_digits=6, decimal_places=3)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    geocode_source = models.CharField(max_length=30, null=True, blank=True)
    geocode_accuracy = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"

