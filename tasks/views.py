from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.shortcuts import redirect, render, get_object_or_404
from .models import Task, Organization, Membership, OrganisationTask, AssignedTasks
from django.views.generic import ListView, CreateView, TemplateView , UpdateView
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
    else:                              
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.META.get("HTTP_REFERER","/"))
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

class MembershipListView(ListView):
    model =Membership
    template_name = 'tasks/clan_members.html'
    context_object_name = 'memberships'
    def get_queryset(self):
        return Membership.objects.filter(
            organization_id=self.kwargs['pk']
        )
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        organization = get_object_or_404(Organization,pk = self.kwargs['pk'])
        context['organization'] = organization
        return context

"""I was making form for joining a clan, 0the doubt i had was, how do i make sure of organization and user so they're saved with an accurate role"""

class MemberJoinView(LoginRequiredMixin,CreateView):
    model = Membership
    template_name = 'tasks/clan_join.html'
    fields = ['role']
    def get_success_url(self) :
        return reverse_lazy('membership-list',kwargs = {'pk':self.kwargs['pk']})
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.organization_id = self.kwargs['pk']
        return super().form_valid(form)

"""I will render request for joining in the same page as clanMembers. The request would be a post request which would append on the clan page not to us. and then, I will click accept as a member, which would then allow user to be part of organization member. Essently, MY accept sign would appened him to my clan's database"""