from decimal import Decimal
from rest_framework import serializers
from rest_framework.exceptions import ParseError
from django.contrib.auth.models import User
from .models import Category, MenuItem, Cart, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title"]


class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "featured", "category", "category_id"]
        # depth = 1


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class CartSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)
    unit_price = serializers.DecimalField(
        max_digits=6, decimal_places=2, read_only=True
    )
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = [
            "user_id",
            "menuitem",
            "menuitem_id",
            "quantity",
            "unit_price",
            "price",
        ]

    def get_unit_price(self, obj):
        return obj.unit_price

    def get_price(self, obj):
        return obj.price

    def create(self, validated_data):
        menuitem_id = validated_data["menuitem_id"]
        quantity = validated_data["quantity"]
        unit_price = None
        price = None
        try:
            unit_price = MenuItem.objects.get(pk=menuitem_id).price
            price = quantity * unit_price
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Menu item doesn't exist")
        validated_data["unit_price"] = unit_price
        validated_data["price"] = price
        return Cart.objects.create(**validated_data)


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    delivery_crew = UserSerializer(read_only=True)
    delivery_crew_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            "user",
            "user_id",
            "delivery_crew",
            "delivery_crew_id",
            "status",
            "total",
            "date",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    order_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "order",
            "order_id",
            "menuitem",
            "menuitem_id",
            "quantity",
            "unit_price",
        ]
