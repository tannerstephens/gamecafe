from typing import Callable

from flask import (
    Flask,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
)
from flask.views import MethodView

from .models import Collection, Game, Report, User, db
from .session import clear_user, get_user, set_user

USER_ID = "user_id"


class RoleView(MethodView):
    ROUTE: str = None

    AUTHENTICATED: bool = False
    MINIMUM_ROLE: User.Role | None = None

    @classmethod
    def user_allowed(cls):
        if (cls.AUTHENTICATED or cls.MINIMUM_ROLE is not None) and (user := get_user()) is None:
            return False

        if cls.MINIMUM_ROLE is not None and user.role < cls.MINIMUM_ROLE:
            return False

        return True

    @classmethod
    def page_num(cls):
        return max(int(request.args.get("p", 1)), 1)

    @classmethod
    def per_page(cls, default=12):
        per_page = int(request.args.get("per_page", default))
        return min(max(per_page, 1), 50)

    def dispatch_request(self, **kwargs):
        if not self.user_allowed():
            return render_template("pages/404.jinja")

        return super().dispatch_request(**kwargs)

    @classmethod
    def _register(cls, app: Flask):
        view = cls.as_view(cls.__name__)
        app.add_url_rule(cls.ROUTE, view_func=view)

    @classmethod
    def _get_subviews(cls):
        for subview in cls.__subclasses__():
            yield from subview._get_subviews()
            yield subview

    @classmethod
    def register_all_subviews(cls, app: Flask):
        registered = set()

        for subview in cls._get_subviews():
            if subview in registered:
                continue

            registered.add(subview)
            if subview.ROUTE is not None:
                subview._register(app)


class PageView(RoleView):
    TEMPLATE_PATH: str = None

    def get_template_context(self, *args, **kwargs):
        return {}

    def get(self, *args, **kwargs):
        if self.TEMPLATE_PATH is None:
            raise NotImplementedError("`TEMPLATE_PATH` must be defined")

        template_context = self.get_template_context(*args, **kwargs)

        return render_template(self.TEMPLATE_PATH, **template_context)


class FormView(PageView):
    def post(self, *args, **kwargs):
        return self.handle_form_submission(*args, **kwargs)

    def handle_form_submission(self, *args, **kwargs):
        raise NotImplementedError()


class ApiError(Exception):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.message = message
        self.code = code


class ApiView(RoleView):
    class ApiCommon(MethodView):
        def __init__(self, api_view: type["ApiView"]):
            super().__init__()

            self.api_view = api_view

        def response(self, fn: Callable, *args, **kwargs):
            data = {}

            try:
                result = fn(*args, **kwargs)
                data["success"] = True

                code = None

                if isinstance(result, tuple):
                    data["data"] = result[0]
                    code = result[1]
                elif result:
                    data["data"] = result

            except ApiError as e:
                result = None
                data["success"] = False
                data["error"] = e.message
                code = e.code

            return jsonify(data), code

        def dispatch_request(self, **kwargs):
            if not self.api_view.user_allowed():
                return render_template("pages/404.jinja")

            return super().dispatch_request(**kwargs)

    class GroupApi(ApiCommon):
        def get(self):
            return self.response(self.api_view.list)

        def post(self):
            return self.response(self.api_view.create)

    class ItemApi(ApiCommon):
        def get(self, key):
            return self.response(self.api_view.read, key=key)

        def patch(self, key):
            return self.response(self.api_view.update, key=key)

        def delete(self, key):
            return self.response(self.api_view.delete, key=key)

    @classmethod
    def _register(cls, app: Flask):
        group_view = cls.GroupApi.as_view(f"{cls.__name__}-group", cls)
        item_view = cls.ItemApi.as_view(f"{cls.__name__}-items", cls)

        app.add_url_rule(cls.ROUTE, view_func=group_view)
        app.add_url_rule(f"{cls.ROUTE}/<key>", view_func=item_view)

    @classmethod
    def create(cls):
        raise ApiError("Not Allowed", 405)

    @classmethod
    def list(cls):
        raise ApiError("Not Allowed", 405)

    @classmethod
    def read(cls, key):
        raise ApiError("Not Allowed", 405)

    @classmethod
    def update(cls, key):
        raise ApiError("Not Allowed", 405)

    @classmethod
    def delete(cls, key):
        raise ApiError("Not Allowed", 405)


class Home(PageView):
    TEMPLATE_PATH = "pages/home.jinja"
    ROUTE = "/"

    def get_template_context(self, *args, **kwargs):
        return dict(collection=Collection.get_highlighted_collection())


class Login(FormView):
    TEMPLATE_PATH = "pages/login.jinja"
    ROUTE = "/login"

    def get(self):
        if get_user() is not None:
            return redirect("/")

        return super().get()

    def handle_form_submission(self, *args, **kwargs):
        username = request.form["username"]
        password = request.form["password"]

        if (user := User.get_by_username(username)) is None or not user.check_password(password):
            flash("Incorrect username or password", "danger")
            return render_template(self.TEMPLATE_PATH)

        set_user(user)
        flash("Successfully logged in", "success")
        return redirect("/")


class Logout(PageView):
    ROUTE = "/logout"

    def get(self, *args, **kwargs):
        clear_user()
        flash("You have been logged out", "success")
        return redirect("/")


class Register(Login):
    TEMPLATE_PATH = "pages/register.jinja"
    ROUTE = "/register"

    def handle_form_submission(self, *args, **kwargs):
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"].lower()

        username_taken = email_taken = errors = False

        if User.get_by_username(username) is not None:
            flash("That username is taken", "danger")
            errors = True
            username_taken = True

        if User.get_by_email(email) is not None:
            flash("That email is taken", "danger")
            errors = True
            email_taken = True

        if not User.validate_password(password):
            flash("That password is invalid, it must be 8 or more characters", "danger")
            errors = True

        if errors:
            return render_template(
                self.TEMPLATE_PATH,
                oldusername=username,
                oldemail=email,
                username_taken=username_taken,
                email_taken=email_taken,
            )

        User(email, username, password).save()

        flash("Successfully registered, you may now log in", "success")

        return redirect("/")


class Users(PageView):
    TEMPLATE_PATH = "pages/users.jinja"
    ROUTE = "/users"

    MINIMUM_ROLE = User.Role.ADMIN

    def get_template_context(self, *args, **kwargs):
        return dict(page=User.paginate(self.page_num(), 10))


class UsersApi(ApiView):
    ROUTE = "/api/users"

    MINIMUM_ROLE = User.Role.ADMIN

    @classmethod
    def update(cls, key):
        if (new_role := request.json.get("role")) is None:
            return {}, 204

        if (user := User.get_by_id(key)) is None:
            raise ApiError("Not Found", 404)

        user.role = user.Role[new_role.upper()]

        user.save()

        return user

    @classmethod
    def delete(cls, key):
        if (user := User.get_by_id(key)) is None:
            raise ApiError("Not Found", 404)

        if user is get_user():
            raise ApiError("Cannot delete self", 405)

        user.delete()


class GamesView(PageView):
    TEMPLATE_PATH = "pages/games.jinja"
    ROUTE = "/games"

    def get_template_context(self, *args, **kwargs):
        return dict(page=Game.paginate(self.page_num(), 12))


class ListCollections(PageView):
    TEMPLATE_PATH = "pages/collections.jinja"
    ROUTE = "/collections"

    def get_template_context(self, *args, **kwargs):
        return dict(page=Collection.paginate(self.page_num(), self.per_page()))


class NewCollection(FormView):
    TEMPLATE_PATH = "pages/create_edit_collection.jinja"
    ROUTE = "/collections/new"

    MINIMUM_ROLE = User.Role.EDITOR

    def handle_form_submission(self, *args, **kwargs):
        name = request.form["name"]
        description = request.form.get("description")
        highlighted = request.form.get("highlight", "off") == "on"

        game_ids = [int(gid) for gid in request.form.getlist("games")]

        new_collection = Collection(name, description).save(commit=False)

        if highlighted:
            new_collection.highlight()

        for game_id in game_ids:
            game = Game.get_by_id(game_id)

            if game:
                new_collection.games.append(game)

        new_collection.save()

        flash("Collection created", "success")

        return redirect(f"/collections/{new_collection.id}")


class ViewCollection(PageView):
    TEMPLATE_PATH = "pages/collection.jinja"
    ROUTE = "/collections/<int:collection_id>"

    def get_template_context(self, collection_id: int, *args, **kwargs):
        collection = Collection.get_by_id(collection_id)

        return dict(collection=collection)


class EditCollection(ViewCollection, FormView):
    TEMPLATE_PATH = "pages/create_edit_collection.jinja"
    ROUTE = "/collections/<int:collection_id>/edit"

    MINIMUM_ROLE = User.Role.EDITOR

    def handle_form_submission(self, collection_id: int, *args, **kwargs):
        name = request.form["name"]
        description = request.form.get("description")
        highlighted = request.form.get("highlight", "off") == "on"

        game_ids = [int(gid) for gid in request.form.getlist("games")]

        collection = Collection.get_by_id(collection_id)

        collection.name = name
        collection.description = description

        if highlighted and not collection.highlighted:
            collection.highlight()
        else:
            collection.highlighted = highlighted

        games = []

        for game_id in game_ids:
            game = Game.get_by_id(game_id)

            if game:
                games.append(game)

        collection.games = games

        collection.save()

        flash("Collection updated successfully", "success")

        return redirect(f"/collections/{collection.id}")


class GamesApi(ApiView):
    ROUTE = "/api/games"

    @classmethod
    def list(cls):
        query = request.args.get("q")

        stmt = Game.select()

        if query:
            stmt = stmt.where(Game.name.regexp_match(query, "i"))

        return Game.paginate(cls.page_num(), cls.per_page(), stmt=stmt)


class GameImage(RoleView):
    ROUTE = "/games/<int:game_id>/image"

    def get(self, game_id):
        if (game := Game.get_by_bgg_id(game_id)) is None or game.image_path is None:
            return render_template("pages/404.jinja")

        return send_file(game.image_path, mimetype="image/png")


class ReportForm(FormView):
    ROUTE = "/report"
    TEMPLATE_PATH = "pages/make-report.jinja"

    def handle_form_submission(self, *args, **kwargs):
        game_id = int(request.form["id"])
        description = request.form.get("description", "")
        title = request.form.get("title", "")

        if game_id == -1:
            game_name = title
            game = None
        else:
            if (game := Game.get_by_id(game_id)) is None:
                raise Exception()

            game_name = game.name

        new_report = Report(game_name, description)
        new_report.game = game

        new_report.save()

        flash("Thank you for your report!", "success")

        return redirect("/")


class ReportsView(PageView):
    ROUTE = "/reports"
    TEMPLATE_PATH = "pages/reports.jinja"

    MINIMUM_ROLE = User.Role.EDITOR

    def get_template_context(self, *args, **kwargs):
        return {"page": Report.paginate(self.page_num(), 15)}
