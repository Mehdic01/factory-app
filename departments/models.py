from django.db import models
from core.models import Role



# Create your models here.

# Department model
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    managers = models.ManyToManyField('core.User', related_name="managed_departments", blank=True, limit_choices_to={'role': Role.MANAGER})
    members = models.ManyToManyField('core.User', related_name="member_departments", blank=True, limit_choices_to={'role': Role.EMPLOYEE})

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def members_count(self):
        return self.members.count()
    
    @property
    def managers_count(self):
        return self.managers.count()