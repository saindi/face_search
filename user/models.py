from django.contrib.auth.models import AbstractUser
from django.db import models


class UserModel(AbstractUser):
    """
        User model, inherited from the default django user model
    """
    email = models.EmailField(
        unique=True
    )

    def __str__(self):
        return f"{self.email}"

    class Meta:
        verbose_name = "користувач"
        verbose_name_plural = "користувачі"