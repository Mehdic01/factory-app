from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class Role(models.TextChoices):
    EMPLOYEE = 'EMPLOYEE', 'Employee'
    MANAGER = 'MANAGER', 'Manager'
    GM = 'GM', 'General Manager'



# Create your models here.
class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    department = models.ForeignKey('Department', null=True, blank=True, on_delete=models.SET_NULL, related_name='employees')

    def __str__(self):
        return self.get_full_name() or self.username


#User = settings.AUTH_USER_MODEL #nemidoonam ke in badan lazem mishe ya na 

# Department model
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    managers = models.ManyToManyField(User, related_name="managed_departments", blank=True, limit_choices_to={'role': Role.MANAGER})
    members = models.ManyToManyField(User, related_name="member_departments", blank=True, limit_choices_to={'role': Role.EMPLOYEE})

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return super().name
    
    @property
    def members_count(self):
        return self.members.count()
    
    @property
    def managers_count(self):
        return self.managers.count()
    
 


