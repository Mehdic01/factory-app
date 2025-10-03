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
    department = models.ForeignKey('departments.Department', null=True, blank=True, on_delete=models.SET_NULL, related_name='employees')

    def __str__(self):
        return self.get_full_name() or self.username


#User = settings.AUTH_USER_MODEL #nemidoonam ke in badan lazem mishe ya na 

    
 


