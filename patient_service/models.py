from db import db
from flask_bcrypt import Bcrypt
from datetime import datetime

bcrypt = Bcrypt()

# Patient table
class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    contact = db.Column(db.String(15), nullable=False)

    # Soft delete fields
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.String(120), nullable=True)  # Email of user who deleted

    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(120), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = db.Column(db.String(120), nullable=True)

    # Relationship: One patient has many medical records
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy=True, cascade='all, delete-orphan')


# User table for authentication
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='staff')
    phone = db.Column(db.String(15), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    @staticmethod
    def hash_password(password):
        """Hash a plain text password using bcrypt"""
        return bcrypt.generate_password_hash(password).decode('utf-8')

    @staticmethod
    def check_password(hashed_password, plain_password):
        """Verify a plain text password against a hashed password"""
        return bcrypt.check_password_hash(hashed_password, plain_password)


# Medical Record table (one-to-many relationship with Patient)
class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)

    # Medical record details
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(120), nullable=True)  # Email of doctor/user who created


# Audit Log table - Tracks all changes
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    # What changed
    entity_type = db.Column(db.String(50), nullable=False)  # 'patient', 'medical_record', etc.
    entity_id = db.Column(db.Integer, nullable=False)  # ID of the entity that changed
    action = db.Column(db.String(20), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'

    # Who and when
    user_email = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # What changed (store as JSON)
    changes = db.Column(db.Text, nullable=True)  # JSON string of before/after values