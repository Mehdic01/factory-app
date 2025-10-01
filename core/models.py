from django.db import models

class Role(models.TextChoices):
    EMPLOYEE = 'EMPLOYEE', 'Employee'
    MANAGER = 'MANAGER', 'Manager'
    GM = 'GM', 'General Manager'



# Create your models here.
class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)

    def __str__(self):
        return self.get_full_name() or self.username
    