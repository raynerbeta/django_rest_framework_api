import datetime
from decimal import Decimal
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError,
    PermissionDenied,
    NotFound,
    APIException,
    MethodNotAllowed,
)
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    UserSerializer,
    CartSerializer,
    OrderSerializer,
    OrderItemSerializer,
)


def check_if_admin(self, raise_exception=True):
    if not self.request.user.is_superuser:
        if raise_exception:
            raise PermissionDenied({"message": "Only admin can access this method"})
        else:
            return False
    return True


def check_if_manager(self, raise_exception=True):
    if not self.request.user.groups.filter(name="Manager").exists():
        if raise_exception:
            raise PermissionDenied({"message": "Only managers can access this method"})
        else:
            return False
    return True


def check_if_delivery(self, raise_exception=True):
    if not self.request.user.groups.filter(name="Delivery_crew").exists():
        if raise_exception:
            raise PermissionDenied(
                {"message": "Only delivery crew members can access this method"}
            )
        else:
            return False
    return True


def check_if_customer(self, raise_exception=True):
    if self.request.user.groups.count() > 0 or check_if_admin(self, False):
        if raise_exception:
            raise PermissionDenied({"message": "Only customers can access this method"})
        else:
            return False
    return True


def order_queryset(self, queryset):
    ordering = self.request.query_params.get("ordering", None)
    if ordering in self.ordering_fields:
        return queryset.order_by(ordering)
    return queryset


class ManagersUserGroupView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        check_if_admin(self)
        return super().get_permissions()

    def get(self, request, *args, **kwargs):
        self.queryset = User.objects.filter(groups__name="Manager")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user_id = self.request.data.get("user_id")
        if not user_id:
            raise ValidationError({"message": "User id wasn't provided"})
        user = get_object_or_404(User, pk=user_id)
        if user.groups.filter(name="Manager").exists():
            raise ValidationError({"message": "The user is already a manager"})
        manager_group = get_object_or_404(Group, name="Manager")
        try:
            user.groups.add(manager_group)
            return Response(
                {"message": "User added as manager"}, status=status.HTTP_201_CREATED
            )
        except:
            raise APIException({"message": "The user couldn't be added"})


class ManagerUserGroupView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        check_if_admin(self)
        return super().get_permissions()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.groups.filter(name="Manager").exists():
            raise ValidationError({"message": "User is not a manager"})
        manager_group = get_object_or_404(Group, name="Manager")
        if manager_group in instance.groups.all():
            instance.groups.remove(manager_group)
        return Response(
            {"messsage": "User removed from managers"}, status=status.HTTP_200_OK
        )


class DeliveryCrewUserGroupView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        check_if_manager(self)
        return super().get_permissions()

    def get(self, request, *args, **kwargs):
        self.queryset = User.objects.filter(groups__name="Delivery_crew")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user_id = self.request.data["user_id"]
        user = get_object_or_404(User, pk=user_id)
        if user.groups.filter(name="Delivery_crew").exists():
            raise ValidationError(
                {"message": "The user is already a delivery crew member"}
            )
        delivery_group = get_object_or_404(Group, name="Delivery_crew")
        try:
            user.groups.add(delivery_group)
            return Response(
                {"message": "User added as a delivery crew member"},
                status=status.HTTP_201_CREATED,
            )
        except:
            raise APIException({"message": "The user couldn't be added"})


class DeliveryUserGroupView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        check_if_manager(self)
        return super().get_permissions()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        delivery_group = get_object_or_404(Group, name="Delivery_crew")
        if not instance.groups.filter(name="Delivery_crew").exists():
            raise ValidationError({"message": "The user is not a delivery crew member"})
        if delivery_group in instance.groups.all():
            instance.groups.remove(delivery_group)
        return Response(
            {"messsage": "User removed from delivery crew"}, status=status.HTTP_200_OK
        )


class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method in self.allowed_methods:
            if self.request.method != "GET":
                check_if_admin(self)
        return super().get_permissions()


class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ["title", "price", "category_id"]
    ordering = ["category_id"]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get("category", None)
        if category:
            queryset = queryset.filter(category=category)
        return order_queryset(self, queryset)

    def get_permissions(self):
        if self.request.method in self.allowed_methods:
            if self.request.method != "GET":
                check_if_admin(self)
        return super().get_permissions()


class MenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method in self.allowed_methods:
            if self.request.method != "GET":
                check_if_manager(self)
        return super().get_permissions()


class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    ordering_fields = ["quantity", "unit_price", "price"]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        queryset = super().get_queryset()
        return order_queryset(self, queryset)

    def get_permissions(self):
        check_if_customer(self)
        return super().get_permissions()

    def get(self, request, *args, **kwargs):
        try:
            items = Cart.objects.filter(user=request.user.id)
            res = CartSerializer(items, many=True)
            self.queryset = res.data
            return super().get(request, *args, **kwargs)
        except:
            raise APIException({"message": "The cart wasn't retrieved"})

    def post(self, request, *args, **kwargs):
        try:
            new_data = request.data.copy()
            new_data.appendlist("user_id", request.user.id)
            request._full_data = new_data
            return super().post(request, *args, **kwargs)
        except:
            raise ValidationError({"message": "User id not provided"})

    def delete(self, request, *args, **kwargs):
        try:
            to_delete = Cart.objects.filter(user=request.user.id)
            to_delete.delete()
            return Response(
                {"message": "The cart was emptied"}, status=status.HTTP_200_OK
            )
        except:
            raise APIException({"message": "The cart wasn't emptied"})


class OrdersView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    ordering_fields = ["user_id", "delivery_crew_id", "status", "date", "total"]
    ordering = ["-date", "status"]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get("status", None)
        date = self.request.query_params.get("date", None)
        if status:
            queryset = queryset.filter(status=status)
        if date:
            queryset = queryset.filter(date=date)
        return order_queryset(self, queryset)

    def get(self, request, *args, **kwargs):
        orders = Order.objects.all()
        if check_if_manager(self, False):
            pass
        elif check_if_delivery(self, False):
            orders = Order.objects.filter(delivery_crew=request.user.id)
        elif check_if_customer(self, False):
            orders = Order.objects.filter(user=request.user.id)
        else:
            raise PermissionDenied({"message": "You don't have access to this method"})
        self.queryset = orders
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        check_if_customer(self)
        cart_items = Cart.objects.filter(user=request.user.id)
        if not cart_items.exists():
            raise NotFound({"message": "The cart is empty"})
        order_items = []
        total = Decimal(0)
        for item in cart_items:
            order_items.append(
                {
                    "menuitem_id": item.menuitem.id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
            )
            total += item.price
        order = {
            "user_id": request.user.id,
            "orderitem_set": order_items,
            "total": total,
            "date": datetime.date.today(),
        }
        serializer = OrderSerializer(data=order)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                serializer.save()
                cart_items.delete()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except:
            raise APIException(
                {"message": "An error occurred while placing your order"}
            )


class OrderView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        check_if_customer(self)
        try:
            order = get_object_or_404(Order, pk=kwargs.get("pk"))
            if order.user.id != request.user.id:
                raise PermissionDenied(
                    {"message": "You don't have authorization to view this order"}
                )
            serializer = OrderItemSerializer(
                data=OrderItem.objects.filter(order=order), many=True
            )
            serializer.is_valid()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            raise NotFound()

    def update(self, request, *args, **kwargs):
        if request.method == "PUT":
            raise MethodNotAllowed(request.method)
        if check_if_manager(self, False):
            for key in list(request.data.keys()):
                if key not in ["status", "delivery_crew_id"]:
                    raise ValidationError(
                        {"message": "Managers can only update status and delivery crew"}
                    )
            if request.data.get("delivery_crew_id"):
                delivery = get_object_or_404(User, pk=request.data["delivery_crew_id"])
                if not delivery.groups.filter(name="Delivery_crew").exists():
                    raise ValidationError(
                        {"message": "Only a delivery crew member can be assigned"}
                    )
        elif check_if_delivery(self, False):
            for key in list(request.data.keys()):
                if key != "status":
                    raise ValidationError(
                        {"message": "Delivery crew can only update status"}
                    )
            if self.get_object().delivery_crew.id != request.user.id:
                raise PermissionDenied(
                    {"message": "You aren't authorized to update this order"}
                )
        else:
            raise PermissionDenied(
                {"message": "Only managers and delivery crew can access this method"}
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        groups = self.request.user.groups
        if not groups.filter(name="Manager").exists():
            raise PermissionDenied({"message": "Only managers can access this method"})
        return super().destroy(request, *args, **kwargs)
