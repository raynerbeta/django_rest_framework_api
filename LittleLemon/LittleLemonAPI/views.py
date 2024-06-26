from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer, CartSerializer, OrderSerializer, OrderItemSerializer

class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get_permissions(self):
        if self.request.method != 'GET':
            if not self.request.user.groups.filter(name='Manager').exists():
                raise PermissionDenied({
                    'message': 'Only managers can access this method'
                })
        return super().get_permissions()

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get_permissions(self):
        if self.request.method != 'GET':
            if not self.request.user.groups.filter(name='Manager').exists():
                raise PermissionDenied({
                    'message': 'Only managers can access this method'
                })
        return super().get_permissions()
    
class MenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get_permissions(self):
        if self.request.method != 'GET':
            if not self.request.user.groups.filter(name='Manager').exists():
                raise PermissionDenied({
                    'message': 'Only managers can access this method'
                })
        return super().get_permissions()
    
class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def delete(self, request, *args, **kwargs):
        Cart.objects.filter(user=request.user).delete()
        return super().delete(request, *args, **kwargs)
    
    def get_permissions(self):
        if self.request.method != 'GET':
            if self.request.user.groups.filter().exists():
                raise PermissionDenied({
                    'message': 'Only customers can access this method'
                })
        return super().get_permissions()