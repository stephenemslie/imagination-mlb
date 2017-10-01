import string
import random

import factory
from factory.fuzzy import FuzzyChoice


class TeamFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'game.Team'

    name = factory.Sequence(lambda n: 'team-{}'.format(n))


class AdminUserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'game.User'

    is_staff = True
    is_active = True
    username = factory.Faker('user_name')
    password = factory.PostGenerationMethodCall('set_password', 'adm1n')


class ShowFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'game.Show'

    name = factory.Faker('word')
    date = factory.Faker('date')
    welcome_message = "Welcome message"
    recall_message = "Recall message"
    souvenir_message = "Souvenir message. Url is: {}"


class PlayerUserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'game.User'

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    mobile_number = factory.LazyFunction(lambda: '+4477{}'.format(''.join(random.choices(string.digits, k=8))))
    username = factory.LazyAttribute(lambda obj: obj.mobile_number)
    team = factory.SubFactory(TeamFactory)
    handedness = FuzzyChoice(('L', 'R'))


class GameFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'game.Game'

    user = factory.SubFactory(PlayerUserFactory)
    show = factory.SubFactory(ShowFactory)

    @factory.post_generation
    def set_active_game(self, create, extracted, **kwargs):
        self.user.active_game_id = self.pk
        self.user.save()
        self.save()
