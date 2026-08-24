from django.urls import path, include
from projects import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('projects/create/', views.create_project_view, name='create_project'),
    path('projects/<slug:code>/', views.project_gantt_view, name='project_gantt'),
    path('team/', views.team_management_view, name='team_management'),
    path('team/create/', views.create_team_user_view, name='create_team_user'),
    path('team/<int:user_id>/edit/', views.edit_team_user_view, name='edit_team_user'),
    path('team/<int:user_id>/delete/', views.delete_team_user_view, name='delete_team_user'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('api/', include('projects.api.urls')),
]
