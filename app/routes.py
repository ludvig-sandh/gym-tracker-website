from functools import wraps

from flask import Blueprint, g, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import User


main = Blueprint("main", __name__)


def display_error(msg, path):
    return redirect(url_for("main.error", error_msg=msg, error_url=path))


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("main.login"))

        return view(*args, **kwargs)

    return wrapped_view


@main.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)


@main.route("/")
@login_required
def index():
    return render_template("index.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    message = None

    if g.user is not None:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(name=name).first()

        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("main.index"))
        else:
            return display_error("Invalid name or password.", url_for("main.login"))

    return render_template("auth/login.html", message=message)


@main.route("/register", methods=["GET", "POST"])
def register():
    message = None

    if g.user is not None:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        repeat_password = request.form.get("repeat_password", "")

        if not name or not password:
            message = "Name and password are required."
        elif password != repeat_password:
            message = "Passwords do not match."
        elif User.query.filter_by(name=name).first():
            message = "A user with that name already exists."
        else:
            user = User(name=name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("main.login"))

    return render_template("auth/register.html", message=message)


@main.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@main.route("/error")
def error():
    return render_template(
        "error.html",
        title="FEL",
        error_msg=request.args.get("error_msg", ""),
        error_url=request.args.get("error_url", url_for("main.index")),
    )
