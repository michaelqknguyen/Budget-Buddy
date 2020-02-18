from budgetbuddy.users.tests.factories import UserFactory


def create_another_user():
    user = UserFactory()
    user.save()
    return user
