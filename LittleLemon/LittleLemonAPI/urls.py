from django.urls import path
from . import views

urlpatterns = [
    path("categories", views.CategoriesView.as_view()),
    path("menu-items", views.MenuItemsView.as_view()),
    path("menu-items/<int:pk>", views.MenuItemView.as_view()),
    path("cart/menu-items", views.CartView.as_view()),
    path("orders", views.OrdersView.as_view()),
    path("orders/<int:pk>", views.OrderView.as_view()),
    path("groups/manager/users", views.ManagersUserGroupView.as_view()),
    path("groups/manager/users/<int:pk>", views.ManagerUserGroupView.as_view()),
    path("groups/delivery-crew/users", views.DeliveryCrewUserGroupView.as_view()),
    path("groups/delivery-crew/users/<int:pk>", views.DeliveryUserGroupView.as_view()),
]
