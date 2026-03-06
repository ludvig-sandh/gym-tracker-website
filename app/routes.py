from flask import Blueprint, render_template

from app.models import Workout


main = Blueprint("main", __name__)


@main.route("/")
def index():
    workouts = Workout.query.order_by(Workout.created_at.desc()).all()
    return render_template("index.html", workouts=workouts)
