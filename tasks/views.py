from django.db.models.query import QuerySet
from django.db import transaction
from django.forms.models import BaseModelForm
from django.shortcuts import redirect, render, get_object_or_404
from django.tasks import task
from .models import Task, Organization, Membership, OrganisationTask, OrganisationTaskRelationships,JoinRequest, User, OrganisationActivityLog
from django.views.generic import ListView, CreateView, TemplateView , UpdateView
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseForbidden

ACTIVITY_RENDERERS = {
    OrganisationActivityLog.Actions.CREATED:
        lambda l: f"{l.actor.username} created the organization.",

    OrganisationActivityLog.Actions.CREATE_TASK:
        lambda l: f"{l.actor.username} created '{l.task.title}'.",

    OrganisationActivityLog.Actions.CLAIM_TASK:
        lambda l: f"{l.actor.username} claimed '{l.task.title}'.",

    OrganisationActivityLog.Actions.JOIN:
        lambda l: f"{l.target_user.username} joined the organization.",

    OrganisationActivityLog.Actions.PROMOTE:
        lambda l: f"{l.actor.username} promoted {l.target_user.username}.",

    OrganisationActivityLog.Actions.UPDATED:
        lambda l: f"{l.actor.username} updated the organization.",
}

### HelperFunction ###
def OrganizationActivity(organization,actor, activity, task =None,target_user = None ):
    OrganisationActivityLog.objects.create(
        organization = organization,
        actor = actor,
        activity = activity,
        task = task,
        target_user = target_user
    )

def get_organization_activity(organization):
    return (
        OrganisationActivityLog.objects
        .filter(organization=organization)
        .select_related("actor", "task", "target_user")
        .order_by("-created_at")
    )
    
def render_activity(log):
    renderer = ACTIVITY_RENDERERS.get(log.activity)
    if renderer is None:
        return "Unknown activity."
    return renderer(log)

#######################   
### INDEX FOR VIEWS ###
#######################
class HomeView(TemplateView):
    template_name = 'tasks/home.html'
    
########+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#########
########------------------ AUTHENTICATION -------------------------#########
########+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#########
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('task-list')
    else:                              
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("/organizations/")
    else:
        form = AuthenticationForm()
    return render(request, 'tasks/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


#################################################################################
########################## PERSONAL TASK LOGIC ##################################
#################################################################################
class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["organisation_tasks"] = (
            OrganisationTaskRelationships.objects
            .filter(user=self.request.user)
            .select_related("task", "task__organization")
        )

        return context

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = 'tasks/task_create.html'
    fields = ['title', 'description', 'completed']
    success_url = reverse_lazy('task-list')
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    template_name = 'tasks/task_update.html'
    fields = ['title','description','completed']
    success_url = reverse_lazy('task-list')
    def form_valid(self,form):
        form.instance.user = self.request.user
        return super().form_valid(form)
        
#==========================================================================#
#------------------------ ORGANIZATION LOGIC ------------------------------#
#==========================================================================#

class OrganizationListView(ListView):
    model = Organization
    template_name = 'tasks/organizations.html'
    context_object_name = 'organizations'
    def get_queryset(self):
        return Organization.objects.all()
    
class OrganizationCreateView(LoginRequiredMixin, CreateView):
    model = Organization
    template_name = 'tasks/Create_Organizations.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('organizations')

    def form_valid(self, form):
        response = super().form_valid(form)
        Membership.objects.create(
            user=self.request.user, 
            organization=form.instance, 
            role="leader"
        )
        OrganizationActivity(
            organization=form.instance,
            actor=self.request.user,
            activity=OrganisationActivityLog.Actions.CREATED
        )
        return response

class OrganizationUpdateView(LoginRequiredMixin,UpdateView):
    model = Organization
    template_name = 'tasks/Edit_Org.html'
    fields = ['description']
    success_url = reverse_lazy('organizations')
    def get_queryset(self):
        return Organization.objects.filter(
            membership__user=self.request.user
        )
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        response =  super().form_valid(form)
        OrganizationActivity(
            organization=form. instance,
            actor=self.request.user,
            activity= OrganisationActivityLog.Actions.UPDATED
        )
        return response
#==========================================================================#
#------------------------- MEMBERSHIP LOGIC -------------------------------#
#==========================================================================#
@login_required()
def membership_list(request,pk):
    organization = get_object_or_404(Organization,pk = pk)
    if request.method == "GET":
        memberships = Membership.objects.filter(organization=organization)
        is_member = memberships.filter(user=request.user).exists()
        tasks = OrganisationTask.objects.filter(organization=organization)
        if is_member:
            requests = JoinRequest.objects.filter(organization=organization)
        else:
            requests = JoinRequest.objects.none()
        claimed_tasks = set(OrganisationTaskRelationships.objects.filter(user=request.user, task__organization=organization, source=OrganisationTaskRelationships.types.Claimed).values_list('task_id', flat=True))
        assigned_tasks = set(OrganisationTaskRelationships.objects.filter(task__organization=organization, source=OrganisationTaskRelationships.types.Assigned).values_list('task_id', flat=True))
        logs = get_organization_activity(organization)
        activty_logs = [
            {
                "message": render_activity(log),
                "time": log.created_at
            } 
            for log in logs
        ]
        context = {"memberships":memberships,"organization": organization, "requests": requests, "tasks": tasks,"is_member": is_member, "claimed_tasks": claimed_tasks, "assigned_tasks": assigned_tasks, "activity_logs":activty_logs}
        return render(request,"tasks/clan_members.html",context)
    elif request.method == "POST":
        if not Membership.objects.filter(user = request.user, organization = organization).exists():
            JoinRequest.objects.get_or_create(user = request.user,organization = organization)
        return redirect("membership-list",pk = pk)
    return HttpResponseNotAllowed(['GET','POST'])
    
@login_required()
def handle_join_request(request, pk):
    join_request = get_object_or_404(JoinRequest, pk=pk)
    organization = join_request.organization
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "accept":
            Membership.objects.create(user=join_request.user, organization=organization, role=Membership.Roles.Member)
            OrganizationActivity(
                organization=organization,
                activity= OrganisationActivityLog.Actions.JOIN,
                actor= request.user,
                target_user=join_request.user
            )
            join_request.delete()
        elif action == "reject":
            join_request.delete()
        return redirect("membership-list", pk=organization.pk)
    return HttpResponseNotAllowed(['POST'])

@login_required
def create_organization_task(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    if not Membership.objects.filter(user=request.user, organization=organization).exists():
        return HttpResponseForbidden("You are not a member of this organization.")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        if title:
            newTask = OrganisationTask.objects.create(
                title=title,
                description=description,
                organization=organization,
                created_by=request.user,
            ) 
            OrganizationActivity(
                organization=organization,
                actor= request.user,
                activity= OrganisationActivityLog.Actions.CREATE_TASK,
                task= newTask
            )
            return redirect("membership-list", pk=organization.pk)
        context = {
            "organization": organization,
            "error": "Title is required.",
            "title": title,
            "description": description,
            "user": request.user,
        }
        return render(request, "tasks/Create_Org_Task.html", context)

    context = {
        "organization": organization,
    }
    return render(request, "tasks/Create_Org_Task.html", context)

@login_required
def create_assigned_task(request,pk):
    organization = get_object_or_404(Organization, pk=pk)
    if not Membership.objects.filter(user = request.user,organization = organization, role__in = [Membership.Roles.Leader, Membership.Roles.Co_leader]).exists():
        return HttpResponseForbidden("You are not authorized to assign tasks in this organization.")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        assigned_users = request.POST.getlist("assigned_users")
        if title and assigned_users:
            org_task = OrganisationTask.objects.create(
                title = title, 
                description = description,
                organization = organization,
                created_by = request.user
            )
            users = User.objects.filter(pk__in=assigned_users)
            for user in users:
                OrganisationTaskRelationships.objects.create(
                    task=org_task,
                    user=user,
                    source=OrganisationTaskRelationships.types.Assigned
                )
            OrganizationActivity(
                organization=organization,
                actor=request.user,
                activity=OrganisationActivityLog.Actions.TASKASSIGNED,
                task=org_task,
            )
            return redirect("membership-list", pk=organization.pk)
        context = {
            "organization": organization,
            "error": "Title and at least one assigned user are required.",
            "title": title,
            "description": description,
            "assigned_users": assigned_users,
            "user": request.user,
        }
        return render(request, "tasks/Assign_Org_Task.html", context)
    members = Membership.objects.filter(organization=organization, role__in=[Membership.Roles.Co_leader, Membership.Roles.Elder, Membership.Roles.Member])
    context = {"organization": organization, "members": members}
    return render(request, "tasks/Assign_Org_Task.html", context)

@login_required()
def claim_task(request, pk):
    task = get_object_or_404(OrganisationTask, pk=pk)
    organization = task.organization
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "accept":
            OrganisationTaskRelationships.objects.get_or_create(
                task=task,
                user=request.user,
                source=OrganisationTaskRelationships.types.Claimed
            )
            OrganizationActivity(
                organization=organization,
                activity=OrganisationActivityLog.Actions.CLAIM_TASK,
                task = task,
                actor= request.user
            )
            return redirect("task-list")
        return redirect("membership-list", pk=organization.pk)
    return HttpResponseNotAllowed(['POST'])

def promote_member(request,org_pk,member_pk):
    organization = get_object_or_404(Organization,pk = org_pk)
    MemberPoints: dict[str,int] = {
        Membership.Roles.Member: 1, 
        Membership.Roles.Elder: 2, 
        Membership.Roles.Co_leader: 3, 
        Membership.Roles.Leader: 4
    } 
    if request.method == "POST":
        member = get_object_or_404(Membership, pk=member_pk, organization=organization)
        actor = get_object_or_404(Membership, user=request.user, organization=organization)
        if MemberPoints[actor.role]<= MemberPoints[member.role]:
            return HttpResponseForbidden("You cannot promote this member")
        if actor.role not in (Membership.Roles.Leader,Membership.Roles.Co_leader):
            return HttpResponseForbidden("You cannot promote")
        if MemberPoints[actor.role] > MemberPoints[member.role]:
            if member.role == Membership.Roles.Member:
                member.role = Membership.Roles.Elder
                member.save()
            elif member.role == Membership.Roles.Elder:
                member.role = Membership.Roles.Co_leader
                member.save()
            elif member.role == Membership.Roles.Co_leader:
                with transaction.atomic():
                    temp = member.role 
                    member.role = actor.role
                    actor.role = temp
                    member.save()
                    actor.save()
            OrganizationActivity(
                organization=organization,
                actor=request.user,
                activity= OrganisationActivityLog.Actions.PROMOTE,
                target_user= member.user
            )
        return redirect('membership-list',pk = org_pk)
    return HttpResponseNotAllowed(["POST"])

