from django.db import models

class Todo(models.Model):
    title = models.CharField(max_length=100)
    body = models.CharField(max_length=100)
    created_at = models.DateField(auto_now_add=True)
    done_at = models.DateField(null=True)
    updated_at = models.DateField(auto_now_add=True)
    deleted_at = models.DateField(null=True)

    class Meta:
        db_table = 'todos'