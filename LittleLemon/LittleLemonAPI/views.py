import datetime
from decimal import Decimal
from multiprocessing.managers import BaseManager
from django.http import QueryDict
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
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


class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method != "GET":
            if not self.request.user.groups.filter(name="Manager").exists():
                raise PermissionDenied(
                    {"message": "Only managers can access this method"}
                )
        return super().get_permissions()


class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ["title", "price", "category_id"]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        queryset = super().get_queryset()
        ordering = self.request.query_params.get("ordering", None)
        if ordering in self.ordering_fields:
            queryset = queryset.order_by(ordering)
        return queryset

    def get_permissions(self):
        if self.request.method != "GET":
            if not self.request.user.groups.filter(name="Manager").exists():
                raise PermissionDenied(
                    {"message": "Only managers can access this method"}
                )
        return super().get_permissions()


class MenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method != "GET":
            if not self.request.user.groups.filter(name="Manager").exists():
                raise PermissionDenied(
                    {"message": "Only managers can access this method"}
                )
        return super().get_permissions()


class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    ordering_fields = ["quantity", "unit_price", "price"]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        queryset = super().get_queryset()
        ordering = self.request.query_params.get("ordering", None)
        if ordering in self.ordering_fields:
            queryset = queryset.order_by(ordering)
        return queryset

    def get_permissions(self):
        groups = self.request.user.groups.count()
        is_admin = self.request.user.is_superuser
        if groups > 0 or is_admin:
            raise PermissionDenied({"message": "Only customers can access this method"})
        return super().get_permissions()

    def get(self, request, *args, **kwargs):
        try:
            items = Cart.objects.filter(user=request.user.id)
            res = CartSerializer(items, many=True)
            self.queryset = res.data
            return super().get(request, *args, **kwargs)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        try:
            new_data = request.data.copy()
            new_data.appendlist("user_id", request.user.id)
            request._full_data = new_data
            return super().post(request, *args, **kwargs)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            to_delete = Cart.objects.filter(user=request.user.id)
            to_delete.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class OrdersView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    ordering_fields = ["user_id", "delivery_crew_id", "status", "date", "total"]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_queryset(self):
        queryset = super().get_queryset()
        date_search = self.request.query_params.get("date", None)
        if date_search:
            queryset = queryset.filter(date=date_search)
        ordering = self.request.query_params.get("ordering", None)
        if ordering in self.ordering_fields:
            queryset = queryset.order_by(ordering)
        return queryset

    def get(self, request, *args, **kwargs):
        orders = Order.objects.all()
        groups = self.request.user.groups
        if groups.filter(name="Manager").exists():
            pass
        elif groups.filter(name="Delivery_crew").exists():
            orders = Order.objects.filter(delivery_crew=request.user.id)
        elif groups.count() == 0:
            orders = Order.objects.filter(user=request.user.id)
        else:
            raise PermissionDenied({"message": "Only customers can access this method"})
        self.queryset = orders
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        groups = self.request.user.groups.count()
        if not groups == 0:
            raise PermissionDenied({"message": "Only customers can access this method"})
        cart_items = Cart.objects.filter(user=request.user.id)
        if not cart_items.exists():
            return Response(
                {"message": "The cart is empty"}, status=status.HTTP_400_BAD_REQUEST
            )
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
        serializer.save()
        cart_items.delete()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        groups = self.request.user.groups
        if groups.count() > 0 or request.user.is_superuser:
            raise PermissionDenied({"message": "Only customers can access this method"})
        try:
            order = Order.objects.get(pk=kwargs.get("pk"))
            if order is None:
                return Response(
                    {"message": "The order doesn't exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
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
            return Response(status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        groups = self.request.user.groups
        if groups.filter(name="Manager").exists():
            for key in list(request.data.keys()):
                if key not in ["status", "delivery_crew_id"]:
                    del request.data[key]
        elif groups.filter(name="Delivery_crew").exists():
            for key in list(request.data.keys()):
                if key != "status":
                    del request.data[key]
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
