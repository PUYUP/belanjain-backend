from rest_framework import serializers

from utils.generals import get_model

Category = get_model('shoptask', 'Category')
Brand = get_model('shoptask', 'Brand')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
