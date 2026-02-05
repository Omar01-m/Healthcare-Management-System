# Import necessary modules from Flask for handling HTTP requests and responses
from flask import Blueprint, request, jsonify

# Import JWT modules for creating and managing JSON Web Tokens
from flask_jwt_extended import JWTManager, create_access_token

# Import the User model and database instance from models.py
from models import User, db

# Import configuration constants
from config import (
    ALLOWED_ROLES,
    MIN_PASSWORD_LENGTH,
    EMAIL_REGEX_PATTERN,
    MSG_USER_REGISTERED,
    MSG_LOGIN_SUCCESSFUL,
    ERR_MISSING_FIELDS,
    ERR_INVALID_EMAIL,
    ERR_INVALID_PASSWORD,
    ERR_INVALID_ROLE,
    ERR_USERNAME_EXISTS,
    ERR_EMAIL_EXISTS,
    ERR_INVALID_CREDENTIALS,
    ERR_ACCOUNT_INACTIVE
)

# Import regex for email validation
import re

# Create a Blueprint named 'auth' to organize authentication-related routes
auth_routes = Blueprint('auth', __name__)

# Initialize JWTManager to handle JWT token creation and validation
jwt = JWTManager()


# ============================================================
# HELPER FUNCTION: Email Validation
# ============================================================
def is_valid_email(email):
    """
    Validate email format using a regular expression from config.

    Args:
        email (str): The email address to validate

    Returns:
        bool: True if email format is valid, False otherwise
    """
    return re.match(EMAIL_REGEX_PATTERN, email) is not None


# ============================================================
# ROUTE: User Registration
# ============================================================
@auth_routes.route('/register', methods=['POST'])
def register():
    """
    Register a new user in the system.

    Expected JSON body:
    {
        "full_name": "string",
        "email": "string",
        "username": "string",
        "password": "string",
        "role": "string",
        "phone": "string"  (optional)
    }
    """

    # Get the JSON data sent in the request body
    data = request.json

    # Extract all required fields from the request data
    full_name = data.get('full_name')
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    # Extract optional fields
    phone = data.get('phone')

    # ============================================================
    # VALIDATION: Check Required Fields
    # ============================================================
    if not full_name or not email or not username or not password or not role:
        return jsonify({"error": ERR_MISSING_FIELDS}), 400

    # ============================================================
    # VALIDATION: Email Format
    # ============================================================
    if not is_valid_email(email):
        return jsonify({"error": ERR_INVALID_EMAIL}), 400

    # ============================================================
    # VALIDATION: Password Strength
    # ============================================================
    # Use the minimum password length from config
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({
            "error": ERR_INVALID_PASSWORD.format(MIN_PASSWORD_LENGTH)
        }), 400

    # ============================================================
    # VALIDATION: Valid Role
    # ============================================================
    # Check if the role is in the allowed roles list from config
    if role.lower() not in ALLOWED_ROLES:
        return jsonify({
            "error": ERR_INVALID_ROLE.format(', '.join(ALLOWED_ROLES))
        }), 400

    # ============================================================
    # VALIDATION: Check for Duplicate Username
    # ============================================================
    if User.query.filter_by(username=username).first():
        return jsonify({"error": ERR_USERNAME_EXISTS}), 400

    # ============================================================
    # VALIDATION: Check for Duplicate Email
    # ============================================================
    if User.query.filter_by(email=email).first():
        return jsonify({"error": ERR_EMAIL_EXISTS}), 400

    # ============================================================
    # CREATE NEW USER
    # ============================================================
    new_user = User(
        full_name=full_name,
        email=email.lower(),
        username=username,
        password=User.hash_password(password),
        role=role.lower(),
        phone=phone
    )

    db.session.add(new_user)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to register user. Please try again."}), 500

    # Return success message from config
    return jsonify({
        "message": MSG_USER_REGISTERED,
        "user": {
            "id": new_user.id,
            "full_name": new_user.full_name,
            "email": new_user.email,
            "username": new_user.username,
            "role": new_user.role
        }
    }), 201


# ============================================================
# ROUTE: User Login
# ============================================================
@auth_routes.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and return a JWT token.

    Expected JSON body:
    {
        "email": "string",
        "password": "string"
    }
    """

    # Get the JSON data from the request body
    data = request.json

    # Extract email and password from the request
    email = data.get('email')
    password = data.get('password')

    # ============================================================
    # VALIDATION: Check Required Fields
    # ============================================================
    if not email or not password:
        return jsonify({"error": ERR_MISSING_FIELDS}), 400

    # ============================================================
    # VALIDATION: Email Format
    # ============================================================
    if not is_valid_email(email):
        return jsonify({"error": ERR_INVALID_EMAIL}), 400

    # ============================================================
    # AUTHENTICATION: Find User and Verify Password
    # ============================================================
    user = User.query.filter_by(email=email.lower()).first()

    if not user or not User.check_password(user.password, password):
        return jsonify({"error": ERR_INVALID_CREDENTIALS}), 401

    # ============================================================
    # CHECK: Account Status
    # ============================================================
    if not user.is_active:
        return jsonify({"error": ERR_ACCOUNT_INACTIVE}), 401

    # ============================================================
    # GENERATE JWT TOKEN
    # ============================================================
    access_token = create_access_token(identity=user.email)

    # Return success message from config
    return jsonify({
        "message": MSG_LOGIN_SUCCESSFUL,
        "access_token": access_token,
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "phone": user.phone
        }
    }), 200