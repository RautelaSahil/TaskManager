from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.shortcuts import redirect, render, get_object_or_404
from .models import Task, Organization, Membership, OrganisationTask, AssignedTasks,JoinRequest
from django.views.generic import ListView, CreateView, TemplateView , UpdateView
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,logout
from django.http import HttpResponseNotAllowed

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
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

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
    
class OrganizationCreateView(LoginRequiredMixin,CreateView):
    model = Organization
    template_name = 'tasks/Create_Organizations.html'
    fields = ['name','description']
    success_url = reverse_lazy('organizations')
    def form_valid(self,form):
        form.instance.save()
        Membership.objects.create(user = self.request.user,organization = form.instance,role = "leader")
        return super().form_valid(form)

class OrganizationUpdateView(LoginRequiredMixin,UpdateView):
    model = Organization
    template_name = 'tasks/Edit_Org.html'
    fields = ['description']
    success_url = reverse_lazy('organizations')
    def get_queryset(self):
        return Organization.objects.filter(
            membership__user=self.request.user
        )
#==========================================================================#
#------------------------- MEMBERSHIP LOGIC -------------------------------#
#==========================================================================#
@login_required()
def membership_list(request,pk):
    organization = get_object_or_404(Organization,pk = pk)
    if request.method == "GET":
        memberships = Membership.objects.filter(organization=organization)
        is_member = memberships.filter(user=request.user).exists()
        if is_member:
            requests = JoinRequest.objects.filter(organization=organization)
        else:
            requests = JoinRequest.objects.none()
        context = {"memberships":memberships,"organization": organization, "requests": requests}
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
            Membership.objects.create(user=join_request.user, organization=organization, role="member")
            join_request.delete()
        elif action == "reject":
            join_request.delete()
        return redirect("membership-list", pk=organization.pk)
    return HttpResponseNotAllowed(['POST'])