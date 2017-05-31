from rest_framework import serializers
from phonenumber_field.modelfields import PhoneNumberField

from .models import User, Game, Team


class TeamSerializer(serializers.HyperlinkedModelSerializer):

    scores = serializers.ListField(serializers.DictField(child=serializers.DateField()))

    class Meta:
        model = Team
        fields = ('url', 'id', 'name', 'scores')


class GameSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Game
        fields = ('url', 'id', 'date_created', 'date_updated', 'distance',
                  'homeruns', 'score', 'state')


class UserSerializer(serializers.HyperlinkedModelSerializer):

    games = GameSerializer(many=True, read_only=True)
    active_game = GameSerializer(read_only=True)
    team = serializers.SlugRelatedField(required=False, slug_field='name', queryset=Team.objects.all())
    team_url = serializers.HyperlinkedRelatedField(read_only=True, source='team', view_name='team-detail')
    mobile_number = serializers.CharField(validators=PhoneNumberField().validators)

    class Meta:
        model = User
        fields = ('url', 'id', 'first_name', 'last_name', 'mobile_number',
                  'email', 'games', 'active_game', 'team', 'team_url', 'image')

    def create(self, validated_data):
        validated_data['username'] = validated_data['mobile_number']
        user = super().create(validated_data)
        game = Game.objects.create(user=user)
        user.active_game = game
        user.save()
        return user


class GameScoreSerializer(serializers.Serializer):

    score = serializers.IntegerField()
    distance = serializers.IntegerField()
    homeruns = serializers.IntegerField()
