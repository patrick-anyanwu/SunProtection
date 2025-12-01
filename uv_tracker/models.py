from django.db import models

class CancerData(models.Model):
    state = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField()
    data_type = models.CharField(max_length=50)  # Incidence or Mortality
    count = models.IntegerField()
    cancer_type = models.CharField(max_length=255)
    sex = models.CharField(max_length=20, null=True, blank=True)  # Males, Females, Persons

    def __str__(self):
        return f"{self.cancer_type} ({self.data_type}) - {self.year}"
