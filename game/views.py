from django.db.models import Sum
from django.db.models.functions import Trunc

from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, DateFilter
from django_fsm import can_proceed

from .models import User, Game, Team
from .serializers import UserSerializer, GameSerializer, GameScoreSerializer, TeamSerializer


class DateFilterMixin:

    def filter_date(self, queryset, name, value):
        annotate_name = '{}_date'.format(name)
        return queryset.annotate(**{annotate_name: Trunc(name, 'day')})\
                       .filter(**{annotate_name: value})


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class UserFilter(FilterSet, DateFilterMixin):
    game_created = DateFilter(name='active_game__date_created', method='filter_date')
    game_updated = DateFilter(name='active_game__date_updated', method='filter_date')
    state = CharFilter(name='active_game__state')
    team = CharFilter(name='team__name')

    class Meta:
        model = User
        fields = ('state', 'is_finalist', 'team', 'handedness', 'signed_waiver')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().annotate(score=Sum('games__score'))
    serializer_class = UserSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filter_class = UserFilter
    ordering_fields = ('score', 'date_updated', 'date_created',
                       ('active_game__date_created', 'game_created'),
                       ('active_game__date_updated', 'game_updated'))
    ordering = 'active_game__date_updated'

    def get_queryset(self):
        return self.queryset.filter(is_staff=False, is_superuser=False, is_active=True)


class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    @detail_route(methods=['POST'])
    def confirm(self, request, pk=None):
        game = self.get_object()
        if not can_proceed(game.confirm):
            error = {'error': 'Illegal state change {} -> {}'.format(game.state, 'confirmed')}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        game.confirm()
        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def queue(self, request, pk=None):
        game = self.get_object()
        if not can_proceed(game.queue):
            error = {'error': 'Illegal state change {} -> {}'.format(game.state, 'queued')}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        game.queue()
        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def play(self, request, pk=None):
        game = self.get_object()
        if not can_proceed(game.play):
            error = {'error': 'Illegal state change {} -> {}'.format(game.state, 'playing')}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        game.play()
        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def recall(self, request, pk=None):
        game = self.get_object()
        if not can_proceed(game.recall):
            error = {'error': 'Illegal state change {} -> {}'.format(game.state, 'recalled')}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        game.recall()
        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def complete(self, request, pk=None):
        game = self.get_object()
        serializer = GameScoreSerializer(data=request.data)
        if serializer.is_valid():
            if not can_proceed(game.complete):
                error = {'error': 'Illegal state change {} -> {}'.format(game.state, 'completed')}
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
            game.complete(**serializer.data)
            game.save()
            serializer = self.get_serializer(game)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['POST'])
    def cancel(self, request, pk=None):
        game = self.get_object()
        game.cancel()
        game.save()
        serializer = self.get_serializer(game)
        return Response(serializer.data)


@api_view(['POST'])
def set_lighting(request):
    return Response({'Succes': True})
