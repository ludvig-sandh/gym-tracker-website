from flask import Blueprint, redirect, render_template, request, url_for

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

        user = User.query.filter_by(name=name, password=password).first()

        if user:
            message = f"Logged in as {user.name}."
        else:
            message = "Invalid name or password."

    return render_template("login.html", message=message)
