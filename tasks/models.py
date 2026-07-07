from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    user = models.ForeignKey(User,on_delete = models.CASCADE,null = False)
    def __str__(self):
        return self.title

class Organization(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class Membership(models.Model):
    class Roles(models.TextChoices):
        Leader = 'leader', 'leader'
        Co_leader = 'co_leader', 'Co-Leader'
        Elder = 'elder', 'Elder'
        Member = 'member', 'Member'
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'organization'], name='unique_membership')
        ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=Roles.choices, default = "member")

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"

class OrganisationTask(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.title

class OrganisationTaskRelationships(models.Model):
    class types(models.TextChoices):
        Assigned = 'assigned', 'Assigned'
        Claimed = 'claimed', 'Claimed'
    task = models.ForeignKey(OrganisationTask, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    source = models.CharField(max_length=50, choices = types.choices)
    def __str__(self):
        return f"{self.task.title} assigned to {self.user.username} in {self.task.organization.name}"
    
class JoinRequest(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization,on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.user.username} -> {self.organization.name}"
    

