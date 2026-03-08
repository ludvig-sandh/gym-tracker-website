import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.extensions import db
from app.models import Exercise, ExerciseEntry, MuscleGroup, User, seed_muscle_groups


LEGACY_POST_DATE_FORMAT = "%a, %b %d, %Y - %H:%M"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import legacy gym tracker JSON into the current SQLite schema."
    )
    parser.add_argument("input_json", help="Path to the legacy JSON export.")
    parser.add_argument("output_db", help="Path to the SQLite database file to create.")
    return parser.parse_args()


def build_app(database_path):
    app = Flask(__name__, instance_relative_config=False)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def ensure_fresh_database(database_path):
    database_file = Path(database_path)
    database_file.parent.mkdir(parents=True, exist_ok=True)
    if database_file.exists():
        database_file.unlink()


def load_legacy_data(input_json):
    with open(input_json, "r", encoding="utf-8") as file:
        return json.load(file)


def import_users(legacy_users):
    for legacy_user in legacy_users:
        user = User(
            id=legacy_user["id"],
            name=legacy_user["name"],
        )
        user.set_password(legacy_user["account_id"])
        db.session.add(user)


def import_exercises(legacy_events):
    exercises_by_id = {}
    for legacy_event in legacy_events:
        exercise = Exercise(
            id=legacy_event["id"],
            name=legacy_event["name"],
            user_id=legacy_event["user_id"],
            param1=legacy_event["param1"],
            param2=legacy_event["param2"] or None,
            is_favorited=bool(legacy_event["liked"]),
        )
        db.session.add(exercise)
        exercises_by_id[exercise.id] = exercise
    return exercises_by_id


def import_entries(legacy_posts, exercises_by_id):
    for legacy_post in legacy_posts:
        exercise = exercises_by_id.get(legacy_post["event_id"])
        if exercise is None:
            continue

        entry = ExerciseEntry(
            id=legacy_post["id"],
            exercise_id=exercise.id,
            value1=legacy_post["value1"],
            value2=legacy_post["value2"] if exercise.param2 else None,
            created_at=datetime.strptime(legacy_post["date"], LEGACY_POST_DATE_FORMAT),
        )
        db.session.add(entry)


def import_muscle_groups(legacy_relations, exercises_by_id):
    muscle_groups_by_id = {group.id: group for group in MuscleGroup.query.all()}

    for relation in legacy_relations:
        exercise = exercises_by_id.get(relation["event_id"])
        muscle_group = muscle_groups_by_id.get(relation["topic_id"])

        if exercise is None or muscle_group is None:
            continue

        if muscle_group not in exercise.muscle_groups:
            exercise.muscle_groups.append(muscle_group)


def main():
    args = parse_args()
    output_db = os.path.abspath(args.output_db)
    ensure_fresh_database(output_db)
    legacy_data = load_legacy_data(args.input_json)
    app = build_app(output_db)

    with app.app_context():
        db.create_all()
        seed_muscle_groups()

        import_users(legacy_data.get("Users", []))
        exercises_by_id = import_exercises(legacy_data.get("Events", []))
        import_entries(legacy_data.get("Posts", []), exercises_by_id)
        import_muscle_groups(legacy_data.get("Events_Topics_Rel", []), exercises_by_id)

        db.session.commit()

    print(f"Created SQLite database at {output_db}")


if __name__ == "__main__":
    main()
