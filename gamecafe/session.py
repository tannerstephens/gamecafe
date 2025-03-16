from flask import g, session

from .models import User

USER_ID = "user_id"


def get_user() -> User | None:
    if "user" not in g:
        if (user_id := session.get(USER_ID)) is None or (user := User.get_by_id(user_id)) is None:
            g.user = None
        else:
            g.user = user

    return g.user


def set_user(user: User):
    session[USER_ID] = user.id
    g.user = user


def clear_user():
    session.pop(USER_ID, None)
    g.user = None
