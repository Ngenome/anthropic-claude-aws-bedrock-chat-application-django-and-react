import uuid
from django.db import models
from appauth.models import AppUser

# Create your models here.

class DesignProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='design_projects')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    design_project = models.ForeignKey(DesignProject, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']

class Prototype(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    design_project = models.ForeignKey(DesignProject, on_delete=models.CASCADE, related_name='prototypes')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='prototypes')
    title = models.CharField(max_length=200)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

class PrototypeVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prototype = models.ForeignKey(Prototype, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_original = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.prototype.title} - {self.name}"
    
    class Meta:
        ordering = ['-created_at']

class PrototypeVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(PrototypeVariant, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    name = models.CharField(max_length=200)
    edit_prompt = models.TextField(blank=True, null=True)
    html_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.variant.name} - v{self.version_number}: {self.name}"
    
    class Meta:
        ordering = ['version_number']
        unique_together = ['variant', 'version_number']
