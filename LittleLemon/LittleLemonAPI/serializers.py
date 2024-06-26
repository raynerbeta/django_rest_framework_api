from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, MenuItem, Cart, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id',
            'title'
        ]


class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id',
            'title',
            'price',
            'featured',
            'category',
            'category_id'
        ]
        # depth = 1


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email'
        ]


class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)    

    class Meta:
        model = Cart
        fields = [
            'user',
            'user_id',
            'menuitem',
            'menuitem_id',
            'quantity',
            'unit_price',
            'price'
        ]
        #obtener unit_price de menuitem
        extra_kwargs = {
            'unit_price': {
                'min_val': 0
            }
        }


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    delivery_crew = UserSerializer(read_only=True)
    delivery_crew_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'user',
            'user_id',
            'delivery_crew',
            'delivery_crew_id',
            'status',
            'total',
            'date'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    order_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'order',
            'order_id',
            'menuitem',
            'menuitem_id',
            'quantity',
            'unit_price'
        ]
