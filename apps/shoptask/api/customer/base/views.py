from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.generals import get_model

from .serializers import CategorySerializer, BrandSerializer

Category = get_model('shoptask', 'Category')
Brand = get_model('shoptask', 'Brand')


class CategoryApiView(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated],
    }

    def list(self, request, format=None):
        context = {'request': self.request}
        queryset = Category.objects.filter(is_active=True, is_delete=False)
        serializer = CategorySerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)


class BrandApiView(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated],
    }

    def list(self, request, format=None):
        context = {'request': self.request}
        queryset = Brand.objects.filter(is_active=True, is_delete=False)
        serializer = BrandSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
