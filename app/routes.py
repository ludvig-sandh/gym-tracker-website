import datetime
from functools import wraps

from flask import Blueprint, g, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import Exercise, ExerciseEntry, MuscleGroup, User


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

    return render_template("auth/login.html", mobile=mobile(), title="LOGGA IN")


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

    return render_template("auth/register.html", mobile=mobile(), title="REGISTRERA")


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

    exercises = exercises_query.order_by(Exercise.is_favorited.desc(), Exercise.name).all()
    delays = {exercise.id: 0.03 * index for index, exercise in enumerate(exercises)}
    latest = _get_latest_exercises(g.user.id)

    return render_template(
        "exercises/exercises.html",
        mobile=mobile(),
        title="TRÄNINGSUTVECKLING",
        exercises=exercises,
        delays=delays,
        latest=latest,
        muscle_groups=muscle_groups,
        selected_muscle_group=selected_muscle_group,
    )


def _format_entry_value(value):
    if value is None:
        return None
    return int(value) if value == int(value) else value


def _get_latest_exercises(user_id, limit=2):
    latest_exercises = (
        db.session.query(Exercise.id, Exercise.name, Exercise.is_favorited)
        .join(ExerciseEntry, ExerciseEntry.exercise_id == Exercise.id)
        .filter(Exercise.user_id == user_id)
        .group_by(Exercise.id, Exercise.name, Exercise.is_favorited)
        .order_by(db.func.max(ExerciseEntry.created_at).desc())
        .limit(limit)
        .all()
    )

    return latest_exercises


def _format_display_date(value):
    return value.strftime("%a, %d %b %Y")


def _format_chart_date(value):
    return value.strftime("%d %b %Y")


def _build_statistics_chart_data(exercise):
    entries = (
        ExerciseEntry.query.filter_by(exercise_id=exercise.id)
        .order_by(ExerciseEntry.created_at.asc(), ExerciseEntry.id.asc())
        .all()
    )

    daily_max = {}
    for entry in entries:
        entry_date = entry.created_at.date()
        current_max = daily_max.get(entry_date)
        if current_max is None or entry.value1 > current_max:
            daily_max[entry_date] = entry.value1

    current_series = []
    best_series = []
    running_best = 0
    for entry_date, max_value in sorted(daily_max.items()):
        running_best = max(running_best, max_value)
        timestamp = int(datetime.datetime.combine(entry_date, datetime.time()).timestamp() * 1000)
        current_series.append({"x": timestamp, "y": float(max_value)})
        best_series.append({"x": timestamp, "y": float(running_best)})

    return {
        "current_series": current_series,
        "best_series": best_series,
        "latest_value": _format_entry_value(current_series[-1]["y"]) if current_series else None,
        "best_value": _format_entry_value(best_series[-1]["y"]) if best_series else None,
    }


def _build_exercise_days(exercise):
    entries = (
        ExerciseEntry.query.filter_by(exercise_id=exercise.id)
        .order_by(ExerciseEntry.created_at.desc(), ExerciseEntry.id.desc())
        .all()
    )

    days = []
    today = datetime.datetime.today().date()
    for entry in entries:
        entry_date = entry.created_at.date()

        if not days or days[-1]["entry_date"] != entry_date:
            if entry_date == today:
                label_date = "Idag"
            elif entry_date == today - datetime.timedelta(days=1):
                label_date = "Igår"
            else:
                label_date = _format_display_date(entry.created_at)

            days.append(
                {
                    "entry_date": entry_date,
                    "date": label_date,
                    "volume": 0,
                    "entries": [],
                }
            )

        value1 = _format_entry_value(entry.value1)
        value2 = _format_entry_value(entry.value2)
        label_parts = [f"{exercise.param1}: {value1}"]

        if exercise.param2 and value2 is not None:
            label_parts.append(f"{exercise.param2}: {value2}")
            days[-1]["volume"] += entry.value1 * entry.value2
            label_parts.append(f"volym: {_format_entry_value(entry.value1 * entry.value2)}")

        days[-1]["entries"].append(
            {
                "entry": entry,
                "label": ", ".join(label_parts),
            }
        )

    for day in days:
        day.pop("entry_date", None)
        day["volume"] = _format_entry_value(day["volume"])

    return days


def _get_user_exercise_entry(exercise_id, entry_id):
    exercise = Exercise.query.filter_by(id=exercise_id, user_id=g.user.id).first()

    if exercise is None:
        return None, None

    entry = ExerciseEntry.query.filter_by(id=entry_id, exercise_id=exercise.id).first()
    return exercise, entry


@main.route("/exercise/<int:exercise_id>")
@main.route("/exercises/<int:exercise_id>")
@login_required
def exercises_show(exercise_id):
    exercise = Exercise.query.filter_by(id=exercise_id, user_id=g.user.id).first()

    if exercise is None:
        return display_error("Denna övningen finns inte.", url_for("main.exercises_index"))

    return render_template(
        "exercises/show.html",
        mobile=mobile(),
        title=exercise.name,
        exercise=exercise,
        days=_build_exercise_days(exercise),
    )


@main.route("/exercise/<int:exercise_id>/statistics")
@main.route("/exercises/<int:exercise_id>/statistics")
@login_required
def exercises_statistics(exercise_id):
    exercise = Exercise.query.filter_by(id=exercise_id, user_id=g.user.id).first()

    if exercise is None:
        return display_error("Denna övningen finns inte.", url_for("main.exercises_index"))

    return render_template(
        "exercises/statistics.html",
        mobile=mobile(),
        title=f"STATISTIK - {exercise.name.upper()}",
        exercise=exercise,
        chart=_build_statistics_chart_data(exercise),
    )


@main.route("/exercise/<int:exercise_id>/entries", methods=["POST"])
@main.route("/exercises/<int:exercise_id>/entries", methods=["POST"])
@login_required
def exercise_entries_create(exercise_id):
    exercise = Exercise.query.filter_by(id=exercise_id, user_id=g.user.id).first()

    if exercise is None:
        return display_error("Denna övningen finns inte.", url_for("main.exercises_index"))

    value1_raw = request.form.get("value1", "").strip()
    value2_raw = request.form.get("value2", "").strip()

    if not value1_raw:
        return display_error("Första värdet får inte vara tomt.", url_for("main.exercises_show", exercise_id=exercise.id))

    if exercise.param2 and not value2_raw:
        return display_error("Andra värdet får inte vara tomt.", url_for("main.exercises_show", exercise_id=exercise.id))

    try:
        value1 = float(value1_raw)
        value2 = float(value2_raw) if value2_raw else None
    except ValueError:
        return display_error("Värdena måste vara siffror.", url_for("main.exercises_show", exercise_id=exercise.id))

    entry = ExerciseEntry(
        exercise_id=exercise.id,
        value1=value1,
        value2=value2,
    )
    db.session.add(entry)
    db.session.commit()

    return redirect(url_for("main.exercises_show", exercise_id=exercise.id))


@main.route("/exercise/<int:exercise_id>/entries/<int:entry_id>/edit", methods=["GET", "POST"])
@main.route("/exercises/<int:exercise_id>/entries/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def exercise_entries_edit(exercise_id, entry_id):
    exercise, entry = _get_user_exercise_entry(exercise_id, entry_id)

    if exercise is None:
        return display_error("Denna övningen finns inte.", url_for("main.exercises_index"))
    if entry is None:
        return display_error("Detta inlägget finns inte.", url_for("main.exercises_show", exercise_id=exercise.id))

    if request.method == "POST":
        value1_raw = request.form.get("value1", "").strip()
        value2_raw = request.form.get("value2", "").strip()

        if not value1_raw:
            return display_error("Första värdet får inte vara tomt.", request.path)
        if exercise.param2 and not value2_raw:
            return display_error("Andra värdet får inte vara tomt.", request.path)

        try:
            entry.value1 = float(value1_raw)
            entry.value2 = float(value2_raw) if value2_raw else None
        except ValueError:
            return display_error("Värdena måste vara siffror.", request.path)

        db.session.commit()
        return redirect(url_for("main.exercises_show", exercise_id=exercise.id))

    return render_template(
        "exercise_events/edit.html",
        mobile=mobile(),
        title="REDIGERA INLAGG",
        exercise=exercise,
        exercise_entry=entry,
        created_at_display=_format_display_date(entry.created_at),
    )


@main.route("/exercise/<int:exercise_id>/entries/<int:entry_id>/delete", methods=["GET", "POST"])
@main.route("/exercises/<int:exercise_id>/entries/<int:entry_id>/delete", methods=["GET", "POST"])
@login_required
def exercise_entries_delete(exercise_id, entry_id):
    exercise, entry = _get_user_exercise_entry(exercise_id, entry_id)

    if exercise is None:
        return display_error("Denna övningen finns inte.", url_for("main.exercises_index"))
    if entry is None:
        return display_error("Detta inlägget finns inte.", url_for("main.exercises_show", exercise_id=exercise.id))

    if request.method == "POST":
        db.session.delete(entry)
        db.session.commit()
        return redirect(url_for("main.exercises_show", exercise_id=exercise.id))

    return render_template(
        "exercise_events/delete.html",
        mobile=mobile(),
        title="RADERA INLAGG",
        exercise=exercise,
        exercise_entry=entry,
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

@main.route("/exercise/<int:exercise_id>/edit", methods=["GET", "POST"])
@main.route("/exercises/<int:exercise_id>/edit", methods=["GET", "POST"])
@login_required
def exercises_edit(exercise_id):
    exercise = Exercise.query.filter_by(id=exercise_id, user_id=g.user.id).first()

    if exercise is None:
        return display_error("Denna övningen finns inte.", url_for("main.exercises_index"))

    muscle_groups = MuscleGroup.ordered().all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        param1 = request.form.get("param1", "").strip()
        param2 = request.form.get("param2", "").strip() or None
        is_favorited = request.form.get("is_favorited") == "on"
        selected_group_ids = request.form.getlist("muscle_groups")

        if not name:
            return display_error("Namnet får inte vara tomt.", request.path)
        if not param1:
            return display_error("Första värdet får inte vara tomt.", request.path)
        if not selected_group_ids:
            return display_error("Välj minst en muskelgrupp.", request.path)

        selected_muscle_groups = MuscleGroup.query.filter(MuscleGroup.id.in_(selected_group_ids)).all()

        if len(selected_muscle_groups) != len(selected_group_ids):
            return display_error("En eller fler muskelgrupper är ogiltiga.", request.path)

        exercise.name = name
        exercise.param1 = param1
        exercise.param2 = param2
        exercise.is_favorited = is_favorited
        exercise.muscle_groups = selected_muscle_groups

        db.session.commit()
        return redirect(url_for("main.exercises_show", exercise_id=exercise.id))

    selected_muscle_group_ids = {group.id for group in exercise.muscle_groups}

    return render_template(
        "exercises/edit.html",
        mobile=mobile(),
        title="REDIGERA ÖVNING",
        exercise=exercise,
        muscle_groups=muscle_groups,
        selected_muscle_group_ids=selected_muscle_group_ids,
    )


@main.route("/exercise/<int:exercise_id>/delete", methods=["GET", "POST"])
@main.route("/exercises/<int:exercise_id>/delete", methods=["GET", "POST"])
@login_required
def exercises_delete(exercise_id):
    exercise = Exercise.query.filter_by(id=exercise_id, user_id=g.user.id).first()

    if exercise is None:
        return display_error("Denna övningen finns inte.", url_for("main.exercises_index"))

    if request.method == "POST":
        db.session.delete(exercise)
        db.session.commit()
        return redirect(url_for("main.exercises_index"))

    return render_template(
        "exercises/delete.html",
        mobile=mobile(),
        title="RADERA " + exercise.name.upper(),
        exercise=exercise,
    )
