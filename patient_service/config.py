"""
Configuration file for the Patient Service
Contains constants, allowed values, and configuration settings
"""

# ============================================================
# USER ROLES
# ============================================================
# Define all allowed user roles in the healthcare system
# These roles determine what actions users can perform
ALLOWED_ROLES = [
    'admin',          # Full system access, can manage all users and data
    'doctor',         # Can view/manage patients, appointments, medical records
    'nurse',          # Can view/update patient information, assist doctors
    'receptionist',   # Can manage appointments, basic patient registration
    'staff'           # General staff with limited access
]

# Default role for new users if not specified
DEFAULT_ROLE = 'staff'


# ============================================================
# PASSWORD VALIDATION
# ============================================================
# Minimum password length requirement
MIN_PASSWORD_LENGTH = 6

# Set to True to enforce complex password rules (uppercase, lowercase, numbers, symbols)
ENFORCE_COMPLEX_PASSWORD = False


# ============================================================
# EMAIL VALIDATION
# ============================================================
# Regular expression pattern for validating email addresses
EMAIL_REGEX_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


# ============================================================
# JWT CONFIGURATION
# ============================================================
# Secret key for JWT token generation (CHANGE THIS IN PRODUCTION!)
JWT_SECRET_KEY = 'your_secret_key_change_this_in_production'

# Token expiration time (in hours)
JWT_ACCESS_TOKEN_EXPIRES_HOURS = 24


# ============================================================
# DATABASE CONFIGURATION
# ============================================================
# Database connection string
# Format: postgresql://username:password@host:port/database_name
DATABASE_URI = 'postgresql://postgres:YOUR_PASSWORD@localhost:5432/healthcare_patients'

# Set to False to disable SQLAlchemy modification tracking (improves performance)
SQLALCHEMY_TRACK_MODIFICATIONS = False


# ============================================================
# PATIENT VALIDATION
# ============================================================
# Minimum and maximum age for patients
MIN_PATIENT_AGE = 0
MAX_PATIENT_AGE = 150

# Phone number validation pattern (adjust based on your region)
PHONE_REGEX_PATTERN = r'^\+?1?\d{9,15}$'


# ============================================================
# API RESPONSE MESSAGES
# ============================================================
# Success messages
MSG_USER_REGISTERED = "User registered successfully"
MSG_LOGIN_SUCCESSFUL = "Login successful"
MSG_PATIENT_CREATED = "Patient created successfully"
MSG_PATIENT_UPDATED = "Patient updated successfully"
MSG_PATIENT_DELETED = "Patient deleted successfully"

# Error messages
ERR_MISSING_FIELDS = "All required fields must be provided"
ERR_INVALID_EMAIL = "Invalid email format"
ERR_INVALID_PASSWORD = "Password must be at least {} characters long"
ERR_INVALID_ROLE = "Invalid role. Allowed roles: {}"
ERR_USERNAME_EXISTS = "Username already exists"
ERR_EMAIL_EXISTS = "Email already registered"
ERR_INVALID_CREDENTIALS = "Invalid email or password"
ERR_ACCOUNT_INACTIVE = "Account is inactive. Please contact administrator"
ERR_PATIENT_NOT_FOUND = "Patient not found"
ERR_UNAUTHORIZED = "Unauthorized access"