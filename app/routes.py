from flask import Blueprint, redirect, render_template, request, url_for

from app.extensions import db
from app.models import User


main = Blueprint("main", __name__)


@main.route("/")
def index():
    return redirect(url_for("main.login"))


@main.route("/login", methods=["GET", "POST"])
def login():
    message = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(name=name).first()

        if user and user.check_password(password):
            message = f"Logged in as {user.name}."
        else:
            message = "Invalid name or password."

    return render_template("login.html", message=message)


@main.route("/register", methods=["GET", "POST"])
def register():
    message = None

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

    return render_template("register.html", message=message)
