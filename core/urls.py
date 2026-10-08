from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("users/", views.users, name="users"),
    path("users/add/", views.user_create, name="user_create"),

    path("bicycles/", views.bicycles, name="bicycles"),
    path("bicycles/add/", views.bicycle_create, name="bicycle_create"),

    path("maintenance/", views.maintenance_list, name="maintenance"),
    path("maintenance/add/", views.maintenance_create, name="maintenance_create"),
    path(
        "maintenance/<int:pk>/status/<str:status>/",
        views.maintenance_update_status,
        name="maintenance_update_status",
    ),
]
