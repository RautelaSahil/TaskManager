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
    task = models.ForeignKey(OrganisationTask, on_delete=models.CASCADE, related_name="relationships")
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
    
class OrganisationActivityLog(models.Model):
    class Actions(models.TextChoices):
        PROMOTE = "promote", "Promote"
        DEMOTE = "demote", "Demote"
        JOIN = "join", "Join"
        CREATE_TASK = "createTask", "Create Task"
        DELETE_TASK = "deleteTask", "Delete Task"
        CLAIM_TASK = "claimTask", "Claim Task"
        TASKASSIGNED = "taskAssigned","taskAssigned"
        CREATED = "created", "Created"
        UPDATED = "updated","Updated"
        
    organization = models.ForeignKey(Organization,on_delete = models.CASCADE)
    task = models.ForeignKey(OrganisationTask,on_delete=models.SET_NULL,null = True, blank=True)
    actor = models.ForeignKey(User,on_delete=models.SET_NULL, null = True, blank=True, related_name="performed_activities")
    activity = models.CharField(max_length = 20, choices = Actions.choices)
    target_user = models.ForeignKey(User, on_delete = models.SET_NULL, blank=True, null = True, related_name="recieved_activities")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.actor} - {self.activity}"

class TaskActivityLog(models.Model):
    class Events(models.TextChoices):
        CREATED = "created", "Created"
        SUBMIT = "sumbit", "Submit"
        COMPLETED = "completed", "Completed"
    task = models.ForeignKey(OrganisationTask, on_delete = models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null = True, blank=True)
    log = models.CharField(max_length = 10,choices = Events.choices)
    time = models.DateTimeField(auto_now_add=True)
    class Meta: 
        ordering = ["-time"]
    def __str__(self):
        return f"{self.user} - {self.log}"