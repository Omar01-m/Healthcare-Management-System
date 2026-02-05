"""
Custom decorators for role-based access control
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from models import User

def role_required(*allowed_roles):
    """
    Decorator to restrict access to routes based on user roles.

    Usage:
        @role_required('admin', 'doctor')
        def some_route():
            # Only admins and doctors can access this
            pass

    Args:
        *allowed_roles: Variable number of role names that are allowed to access the route

    Returns:
        The decorated function if user has required role, otherwise 403 Forbidden error
    """
    def decorator(fn):
        @wraps(fn)  # Preserves the original function's metadata
        def wrapper(*args, **kwargs):
            # Get the current user's email from the JWT token
            # This was set during login when we created the access token
            current_user_email = get_jwt_identity()

            # Query the database to find the user by email
            # We need to check their role
            user = User.query.filter_by(email=current_user_email).first()

            # If user doesn't exist in database (shouldn't happen with valid JWT)
            if not user:
                return jsonify({
                    "error": "User not found"
                }), 404

            # Check if the user's account is active
            # Inactive accounts should not be able to perform actions
            if not user.is_active:
                return jsonify({
                    "error": "Account is inactive"
                }), 403

            # Check if the user's role is in the list of allowed roles
            # Convert to lowercase for case-insensitive comparison
            if user.role.lower() not in [role.lower() for role in allowed_roles]:
                return jsonify({
                    "error": f"Access denied. This action requires one of the following roles: {', '.join(allowed_roles)}"
                }), 403

            # If all checks pass, execute the original function
            return fn(*args, **kwargs)

        return wrapper
    return decorator