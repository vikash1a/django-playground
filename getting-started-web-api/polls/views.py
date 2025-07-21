from django.http import HttpResponse
from rest_framework import generics
from .models import Item
from .serializers import ItemSerializer


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


class ItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer