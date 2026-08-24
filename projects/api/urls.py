from django.urls import path, include
from rest_framework.routers import DefaultRouter
from projects.api.views import (
    ProjectViewSet, TaskViewSet, TaskDependencyViewSet, UserViewSet
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='api-project')
router.register(r'tasks', TaskViewSet, basename='api-task')
router.register(r'dependencies', TaskDependencyViewSet, basename='api-dependency')
router.register(r'users', UserViewSet, basename='api-user')

urlpatterns = [
    path('', include(router.urls)),
]
