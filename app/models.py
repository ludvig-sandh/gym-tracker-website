from app.extensions import db
from werkzeug.security import check_password_hash, generate_password_hash


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
    param1 = db.Column(db.String(80), nullable=False, default="Weight")
    param2 = db.Column(db.String(80), nullable=False, default="Reps")
    is_favorited = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="exercises")

    def __repr__(self):
        return f"<Exercise {self.name}>"
