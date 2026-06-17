from django.forms.models import BaseModelForm
from django.shortcuts import redirect, render
from .models import Task, Organization, Membership, OrganisationTask, AssignedTasks
from django.views.generic import ListView, CreateView, TemplateView   
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login,logout

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
    else:                              # ← this else was missing
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('task-list')
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
        return super().form_valid(form)

