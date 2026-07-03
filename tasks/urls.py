from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/edit', views.TaskUpdateView.as_view(), name = 'task-edit'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('organizations/',views.OrganizationListView.as_view(),name = 'organizations'),
    path('organizations/create',views.OrganizationCreateView.as_view(),name = 'org-create'),
    path('organizations/<int:pk>/members',views.membership_list,name = 'membership-list'),
    path('organizations/<int:pk>/edit', views.OrganizationUpdateView.as_view(), name='org_edit'),
    path('join-request/<int:pk>/', views.handle_join_request, name='accept-request'),
]