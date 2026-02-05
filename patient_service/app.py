"""
Patient Service - Main Application Entry Point

This is the main Flask application file for the Patient Service microservice.
It initializes the Flask app, configures the database and JWT authentication,
registers blueprints (route modules), and creates database tables.

Author: Healthcare Management System Team
Date: 2026
"""

# ============================================================
# IMPORTS
# ============================================================
# Import Flask class to create the application instance
from flask import Flask

# Import database instance and initialization function
from db import db, init_db

# Import authentication routes (login, register) and JWT manager
from auth_routes import auth_routes, jwt

# Import patient CRUD routes
from routes import patient_routes

# Import configuration constants from config file
from config import JWT_SECRET_KEY, DATABASE_URI


# ============================================================
# APPLICATION INITIALIZATION
# ============================================================
# Create the Flask application instance
# __name__ helps Flask determine the root path for the application
app = Flask(__name__)

# Enable pretty-printing of JSON responses (useful for debugging)
# This makes API responses more readable in browsers and testing tools
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


# ============================================================
# DATABASE CONFIGURATION
# ============================================================
# Configure SQLAlchemy database connection
# In production, use environment variables instead of hardcoding credentials
# Example: app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI

# Disable Flask-SQLAlchemy modification tracking
# This feature tracks changes to objects and emits signals, but adds overhead
# Set to False for better performance (SQLAlchemy's own tracking is sufficient)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set database connection pool size (optional but recommended for production)
# Controls the number of connections maintained by the pool
app.config['SQLALCHEMY_POOL_SIZE'] = 10

# Set connection pool timeout (optional)
# Maximum time to wait for a connection from the pool
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30

# Enable SQL query echoing for debugging (disable in production)
# When True, all SQL statements will be logged to the console
app.config['SQLALCHEMY_ECHO'] = False


# ============================================================
# JWT CONFIGURATION
# ============================================================
# Secret key for signing JWT tokens
# IMPORTANT: In production, use a strong random key stored in environment variables
# Never commit real secret keys to version control!
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

# Configure JWT token expiration time (optional)
# Tokens will automatically expire after this duration
from datetime import timedelta
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Configure where to look for JWT tokens (optional)
# By default, looks in the Authorization header as "Bearer <token>"
app.config['JWT_TOKEN_LOCATION'] = ['headers']

# Configure JWT error messages (optional)
app.config['JWT_ERROR_MESSAGE_KEY'] = 'error'


# ============================================================
# INITIALIZE EXTENSIONS
# ============================================================
# Initialize the database with the Flask app
# This connects SQLAlchemy to the Flask application
init_db(app)

# Initialize JWT manager with the Flask app
# This enables JWT token creation and validation for protected routes
jwt.init_app(app)


# ============================================================
# DATABASE TABLES CREATION
# ============================================================
# Create database tables automatically if they don't exist
# This should be done within an application context
with app.app_context():
    # db.create_all() inspects all models and creates corresponding tables
    # It will NOT drop existing tables or modify schemas
    # For schema changes, use database migrations (e.g., Flask-Migrate/Alembic)
    db.create_all()
    print("=" * 60)
    print("✓ Database tables created successfully!")
    print("✓ Patient Service is ready to accept requests")
    print("=" * 60)


# ============================================================
# REGISTER BLUEPRINTS (ROUTE MODULES)
# ============================================================
# Blueprints are a way to organize routes into modular components
# Each blueprint can have its own URL prefix, templates, and static files

# Register authentication routes
# These handle user registration, login, and token generation
# URL prefix: /auth
# Available endpoints:
#   - POST /auth/register - Register a new user
#   - POST /auth/login - Login and receive JWT token
app.register_blueprint(auth_routes, url_prefix='/auth')

# Register patient management routes
# These handle CRUD operations for patient records
# No URL prefix (routes start from root /)
# Available endpoints:
#   - POST /patients - Create a new patient
#   - GET /patients - Get all patients (with optional filters)
#   - GET /patients/<id> - Get a specific patient
#   - PUT /patients/<id> - Update a patient
#   - DELETE /patients/<id> - Soft delete a patient
#   - DELETE /patients/<id>/permanent - Permanently delete a patient
app.register_blueprint(patient_routes)


# ============================================================
# CUSTOM ERROR HANDLERS (OPTIONAL)
# ============================================================
# Define custom error handlers for better API responses

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return {
        "error": "Resource not found",
        "message": "The requested endpoint does not exist"
    }, 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors"""
    # Rollback any pending database transactions
    db.session.rollback()
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again later."
    }, 500


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors"""
    return {
        "error": "Method not allowed",
        "message": "The HTTP method is not allowed for this endpoint"
    }, 405


# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================
@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the service is running.
    Useful for monitoring tools and load balancers.
    
    Returns:
        JSON response with service status
    """
    return {
        "status": "healthy",
        "service": "Patient Service",
        "version": "1.0.0"
    }, 200


@app.route('/', methods=['GET'])
def home():
    """
    Root endpoint - provides API information.
    
    Returns:
        JSON response with API details and available endpoints
    """
    return {
        "service": "Healthcare Management System - Patient Service",
        "version": "1.0.0",
        "description": "Microservice for managing patient records",
        "endpoints": {
            "authentication": {
                "register": "POST /auth/register",
                "login": "POST /auth/login"
            },
            "patients": {
                "create": "POST /patients",
                "list": "GET /patients",
                "get": "GET /patients/<id>",
                "update": "PUT /patients/<id>",
                "soft_delete": "DELETE /patients/<id>",
                "hard_delete": "DELETE /patients/<id>/permanent"
            },
            "system": {
                "health": "GET /health",
                "info": "GET /"
            }
        },
        "documentation": "See README.md for detailed API documentation"
    }, 200


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================
# This block only runs when the script is executed directly
# It will NOT run when imported as a module
if __name__ == "__main__":
    # Run the Flask development server
    # WARNING: Do NOT use the development server in production!
    # Use a production WSGI server like Gunicorn, uWSGI, or Waitress
    
    # Configuration for development server:
    # - debug=True: Enables auto-reload on code changes and detailed error pages
    # - host='127.0.0.1': Listen only on localhost (change to '0.0.0.0' to allow external access)
    # - port=5000: The port number to run the server on
    
    print("\n" + "=" * 60)
    print("🏥 Starting Patient Service...")
    print("=" * 60)
    print("📍 Server URL: http://127.0.0.1:5000")
    print("📖 API Documentation: http://127.0.0.1:5000/")
    print("💚 Health Check: http://127.0.0.1:5000/health")
    print("=" * 60)
    print("⚠️  Debug mode is ON - Do not use in production!")
    print("=" * 60 + "\n")
    
    app.run(
        debug=True,           # Enable debug mode (auto-reload + detailed errors)
        host='127.0.0.1',     # Listen on localhost only
        port=5000,            # Port number
        use_reloader=True     # Enable auto-reload on file changes
    )