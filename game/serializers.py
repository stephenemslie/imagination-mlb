import uuid

from rest_framework import serializers
from phonenumber_field.modelfields import PhoneNumberField

from .models import User, Game, Team, Show
from .tasks import create_user_hook


class AuthenticatedFieldsMixin:

    def to_representation(self, obj):
        data = super().to_representation(obj)
        user = self.context['request'].user
        auth_fields = getattr(self.Meta, 'auth_fields', [])
        if user and not user.is_staff:
            for field in auth_fields:
                data.pop(field)
        return data


class TeamSerializer(serializers.HyperlinkedModelSerializer):

    scores = serializers.ListField(serializers.DictField(child=serializers.DateField()))

    class Meta:
        model = Team
        fields = ('url', 'id', 'name', 'scores')


class BaseUserSerializer(AuthenticatedFieldsMixin, serializers.ModelSerializer):

    team = serializers.SlugRelatedField(required=False, allow_null=True, slug_field='name', queryset=Team.objects.all())
    team_url = serializers.HyperlinkedRelatedField(read_only=True, source='team', view_name='team-detail')
    mobile_number = serializers.CharField(validators=PhoneNumberField().validators, allow_blank=True, required=False)
    show = serializers.PrimaryKeyRelatedField(queryset=Show.objects.all(), required=False, write_only=True)

    class Meta:
        model = User
        fields = ('url', 'id', 'first_name', 'last_name', 'mobile_number',
                  'email', 'games', 'active_game', 'team', 'team_url', 'image',
                  'handedness', 'signed_waiver', 'show', 'profile_id')
        extra_kwargs = {'handedness': {'required': True},
                        'first_name': {'required': True}}
        auth_fields = ('mobile_number', 'email')

    def create(self, validated_data):
        validated_data['username'] = str(uuid.uuid4())
        show = validated_data.pop('show', None)
        if show is None:
            show = Show.objects.order_by('-date')[0]
        user = super().create(validated_data)
        game = Game.objects.create(user=user, show=show)
        user.active_game = game
        user.save()
        if user.mobile_number:
            user.send_welcome_sms()
        create_user_hook.delay(user.pk)
        return user


class ShowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Show
        fields = ('id', 'name', 'date')


class BaseGameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Game
        fields = ('url', 'id', 'user', 'user_id', 'date_created',
                  'date_queued', 'date_recalled', 'date_confirmed',
                  'date_playing', 'date_completed', 'date_cancelled',
                  'distance', 'homeruns', 'score', 'state', 'souvenir_image', 'show')
        read_only_fields = ('url', 'id', 'date_created', 'date_updated',
                            'date_queued', 'date_recalled', 'date_confirmed',
                            'date_playing', 'date_completed', 'date_cancelled',
                            'state')


class GameSerializer(BaseGameSerializer):

    user = BaseUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    show = ShowSerializer(required=False)

    def create(self, validated_data):
        active_game = validated_data['user_id'].active_game
        if active_game and active_game.state not in ('completed', 'cancelled'):
            detail = "User's active game must be completed or cancelled first."
            raise serializers.ValidationError(detail)
        validated_data['user'] = validated_data.pop('user_id')
        if validated_data.get('show') is None:
            validated_data['show'] = Show.objects.order_by('-date')[0]
        game = super().create(validated_data)
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


class LightingSerializer(serializers.Serializer):

    event = serializers.ChoiceField(choices=('LA', 'Boston', 'attractor', 'in-game'))
