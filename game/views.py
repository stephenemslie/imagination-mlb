from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter

from .models import User, Game
from .serializers import UserSerializer, GameSerializer, GameScoreSerializer


class UserFilter(FilterSet):
    state = CharFilter(name='active_game__state')
    team = CharFilter(name='team__name')

    class Meta:
        model = User
        fields = ('state', 'is_finalist', 'team')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = UserFilter

    def get_queryset(self):
        return self.queryset.filter(is_staff=False, is_superuser=False, is_active=True)


class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    @detail_route(methods=['POST'])
    def confirm(self, request, pk=None):
        game = self.get_object()
        game.confirm()
        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def queue(self, request, pk=None):
        game = self.get_object()
        game.queue()
        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def play(self, request, pk=None):
        game = self.get_object()
        game.play()
        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def recall(self, request, pk=None):
        game = self.get_object()
        game.recall()
        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def complete(self, request, pk=None):
        game = self.get_object()
        serializer = GameScoreSerializer(data=request.data)
        if serializer.is_valid():
            game.complete(**serializer.data)
            game.save()
            serializer = self.get_serializer(game)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
