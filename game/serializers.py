from rest_framework import serializers
from phonenumber_field.modelfields import PhoneNumberField

from .models import User, Game, Team


class TeamSerializer(serializers.HyperlinkedModelSerializer):

    scores = serializers.ListField(serializers.DictField(child=serializers.DateField()))

    class Meta:
        model = Team
        fields = ('url', 'id', 'name', 'scores')


class BaseUserSerializer(serializers.ModelSerializer):

    team = serializers.SlugRelatedField(required=False, allow_null=True, slug_field='name', queryset=Team.objects.all())
    team_url = serializers.HyperlinkedRelatedField(read_only=True, source='team', view_name='team-detail')
    mobile_number = serializers.CharField(validators=PhoneNumberField().validators)

    class Meta:
        model = User
        fields = ('url', 'id', 'first_name', 'last_name', 'mobile_number',
                  'email', 'games', 'active_game', 'team', 'team_url', 'image',
                  'handedness', 'signed_waiver')
        extra_kwargs = {'handedness': {'required': True},
                        'first_name': {'required': True}}

    def create(self, validated_data):
        validated_data['username'] = validated_data['mobile_number']
        user = super().create(validated_data)
        game = Game.objects.create(user=user)
        user.active_game = game
        user.save()
        return user


class BaseGameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Game
        fields = ('url', 'id', 'user', 'user_id', 'date_created', 'date_updated',
                  'distance', 'homeruns', 'score', 'state')
        read_only_fields = ('url', 'id', 'date_created', 'date_updated', 'state')


class GameSerializer(BaseGameSerializer):

    user = BaseUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def create(self, validated_data):
        active_game = validated_data['user_id'].active_game
        if active_game and active_game.state not in ('completed', 'cancelled'):
            detail = "User's active game must be completed or cancelled first."
            raise serializers.ValidationError(detail)
        game = super().create({'user': validated_data['user_id']})
        game.user.active_game = game
        game.user.save()
        return game


class UserSerializer(BaseUserSerializer):

    games = BaseGameSerializer(many=True, read_only=True)
    active_game = BaseGameSerializer(read_only=True)


class GameScoreSerializer(serializers.Serializer):

    score = serializers.IntegerField()
    distance = serializers.IntegerField()
    homeruns = serializers.IntegerField()
