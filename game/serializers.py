from rest_framework import serializers
from .models import User, Game


class GameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Game
        fields = ('id', 'date_created', 'date_updated', 'distance', 'homeruns', 'score', 'state')


class UserSerializer(serializers.ModelSerializer):

    games = GameSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'mobile_number', 'email', 'games', 'active_game')
