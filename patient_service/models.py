from db import db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

# Patient table
class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    contact = db.Column(db.String(15), nullable=False)

# User table for authentication
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # Basic user information
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Role of the user (e.g., 'admin', 'doctor', 'nurse', 'receptionist')
    role = db.Column(db.String(50), nullable=False, default='staff')

    # Contact information
    phone = db.Column(db.String(8), nullable=True)

    # Account status
    is_active = db.Column(db.Boolean, default=True)

    @staticmethod
    def hash_password(password):
        """Hash a plain text password using bcrypt"""
        return bcrypt.generate_password_hash(password).decode('utf-8')

    @staticmethod
    def check_password(hashed_password, plain_password):
        """Verify a plain text password against a hashed password"""
        return bcrypt.check_password_hash(hashed_password, plain_password)