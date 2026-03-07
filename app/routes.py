from functools import wraps

from flask import Blueprint, g, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import Exercise, MuscleGroup, User


main = Blueprint("main", __name__)


def display_error(msg, path):
    return redirect(url_for("main.error", error_msg=msg, error_url=path))


def mobile():
    user_agent = request.headers.get('User-Agent')
    signs_of_mobile = [
        "Android",
        "webOS",
        "iPhone",
        "iPad",
        "iPod",
        "IEMobile",
        "Opera Mini"
    ]
    for sign in signs_of_mobile:
        if sign in user_agent:
            return True
    return False


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
    return redirect(url_for("main.exercises_index"))


@main.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("main.exercises_index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(name=name).first()

        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("main.exercises_index"))
        else:
            return display_error("Invalid name or password.", url_for("main.login"))

    return render_template("auth/login.html", mobile=mobile())


@main.route("/register", methods=["GET", "POST"])
def register():
    if g.user is not None:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        repeat_password = request.form.get("repeat_password", "")

        if not name or not password:
            return display_error("Name and password are required.", url_for("main.register"))
        elif password != repeat_password:
            return display_error("Passwords do not match.", url_for("main.register"))
        elif User.query.filter_by(name=name).first():
            return display_error("A user with that name already exists.", url_for("main.register"))
        else:
            user = User(name=name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("main.login"))

    return render_template("auth/register.html", mobile=mobile())


@main.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@main.route("/error")
def error():
    return render_template(
        "error.html",
        mobile=mobile(),
        title="FEL",
        error_msg=request.args.get("error_msg", ""),
        error_url=request.args.get("error_url", url_for("main.index")),
    )

@main.route("/exercise")
@main.route("/exercises")
@login_required
def exercises_index():
    selected_muscle_group = request.args.get("muscle_group", "").strip()
    muscle_groups = MuscleGroup.ordered().all()

    exercises_query = Exercise.query.filter_by(user_id=g.user.id)

    if selected_muscle_group:
        valid_group = next((group for group in muscle_groups if group.name == selected_muscle_group), None)
        if valid_group is None:
            return display_error("Invalid muscle group filter.", url_for("main.exercises_index"))

        exercises_query = exercises_query.join(Exercise.muscle_groups).filter(MuscleGroup.name == selected_muscle_group)

    exercises = exercises_query.order_by(Exercise.name).all()

    return render_template(
        "exercises/exercises.html",
        mobile=mobile(),
        exercises=exercises,
        muscle_groups=muscle_groups,
        selected_muscle_group=selected_muscle_group,
    )


@main.route("/exercise/new", methods=["GET", "POST"])
@main.route("/exercises/new", methods=["GET", "POST"])
@login_required
def exercises_new():
    muscle_groups = MuscleGroup.ordered().all()
    selected_muscle_group = request.args.get("muscle_group", "").strip()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        param1 = request.form.get("param1", "").strip()
        param2 = request.form.get("param2", "").strip() or None
        is_favorited = request.form.get("is_favorited") == "on"
        selected_group_ids = request.form.getlist("muscle_groups")

        if not name:
            return display_error("Namnet får inte vara tomt.", url_for("main.exercises_new"))
        if not param1:
            return display_error("Första värdet får inte vara tomt.", url_for("main.exercises_new"))
        if not selected_group_ids:
            return display_error("Välj minst en muskelgrupp.", url_for("main.exercises_new"))

        selected_muscle_groups = MuscleGroup.query.filter(MuscleGroup.id.in_(selected_group_ids)).all() if selected_group_ids else []

        if len(selected_muscle_groups) != len(selected_group_ids):
            return display_error("En eller fler muskelgrupper är ogiltiga.", url_for("main.exercises_new"))

        exercise = Exercise(
            name=name,
            user_id=g.user.id,
            param1=param1,
            param2=param2,
            is_favorited=is_favorited,
        )
        exercise.muscle_groups = selected_muscle_groups

        db.session.add(exercise)
        db.session.commit()
        return redirect(url_for("main.exercises_index"))

    return render_template(
        "exercises/new.html",
        mobile=mobile(),
        muscle_groups=muscle_groups,
        selected_muscle_group=selected_muscle_group,
    )
