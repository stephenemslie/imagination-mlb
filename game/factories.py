import string
import random

import factory


class TeamFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'game.Team'

    name = factory.Faker('word')


class AdminUserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'game.User'

    is_staff = True
    is_active = True
    username = factory.Faker('user_name')
    password = factory.PostGenerationMethodCall('set_password', 'adm1n')


class PlayerUserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'game.User'

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    mobile_number = factory.LazyFunction(lambda: '+4477{}'.format(''.join(random.choices(string.digits, k=8))))
    username = factory.LazyAttribute(lambda obj: obj.mobile_number)
    team = factory.SubFactory(TeamFactory)


class GameFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'game.Game'

    user = factory.SubFactory(PlayerUserFactory)
