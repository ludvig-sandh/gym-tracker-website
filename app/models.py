from datetime import datetime

from app.extensions import db
from werkzeug.security import check_password_hash, generate_password_hash


exercise_muscle_groups = db.Table(
    "exercise_muscle_groups",
    db.Column("exercise_id", db.Integer, db.ForeignKey("exercise.id"), primary_key=True),
    db.Column("muscle_group_id", db.Integer, db.ForeignKey("muscle_group.id"), primary_key=True),
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    exercises = db.relationship("Exercise", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.name}>"


class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    param1 = db.Column(db.String(80), nullable=False)
    param2 = db.Column(db.String(80), nullable=True)
    is_favorited = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="exercises")
    muscle_groups = db.relationship("MuscleGroup", secondary=exercise_muscle_groups, back_populates="exercises")
    entries = db.relationship("ExerciseEntry", back_populates="exercise", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exercise {self.name}>"


class ExerciseEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise.id"), nullable=False)
    value1 = db.Column(db.Float, nullable=False)
    value2 = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    exercise = db.relationship("Exercise", back_populates="entries")

    def __repr__(self):
        return f"<ExerciseEntry {self.exercise_id}:{self.id}>"


class MuscleGroup(db.Model):
    CHEST = "Bröst"
    SHOULDERS = "Axlar"
    BICEPS = "Biceps"
    TRICEPS = "Triceps"
    BACK = "Rygg"
    LEGS = "Ben"
    ABS = "Mage"
    OTHER = "Övrigt"

    ALL = (
        CHEST,
        SHOULDERS,
        BICEPS,
        TRICEPS,
        BACK,
        LEGS,
        ABS,
        OTHER,
    )
    ORDER = {name: index for index, name in enumerate(ALL)}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    exercises = db.relationship("Exercise", secondary=exercise_muscle_groups, back_populates="muscle_groups")

    @classmethod
    def ordered(cls):
        return cls.query.order_by(
            db.case(
                cls.ORDER,
                value=cls.name,
                else_=len(cls.ORDER),
            )
        )

    def __repr__(self):
        return f"<MuscleGroup {self.name}>"


def seed_muscle_groups():
    existing_names = {name for (name,) in db.session.query(MuscleGroup.name).all()}
    missing_groups = [MuscleGroup(name=name) for name in MuscleGroup.ALL if name not in existing_names]

    if missing_groups:
        db.session.add_all(missing_groups)
        db.session.commit()
