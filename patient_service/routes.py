from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Patient, db
from decorators import role_required
from config import (
    MSG_PATIENT_CREATED,
    MSG_PATIENT_UPDATED,
    MSG_PATIENT_DELETED,
    ERR_MISSING_FIELDS,
    ERR_PATIENT_NOT_FOUND,
    MIN_PATIENT_AGE,
    MAX_PATIENT_AGE
)

patient_routes = Blueprint('patients', __name__)


# ============================================================
# CREATE PATIENT - Allowed: admin, doctor, nurse
# ============================================================
@patient_routes.route('/patients', methods=['POST'])
@jwt_required()
@role_required('admin', 'doctor', 'nurse')
def create_patient():
    """
    Create a new patient record.
    Allowed roles: admin, doctor, nurse
    """
    data = request.json
    current_user = get_jwt_identity()

    name = data.get('name')
    age = data.get('age')
    contact = data.get('contact')

    # Validate required fields
    if not name or not age or not contact:
        return jsonify({"error": ERR_MISSING_FIELDS}), 400

    # Validate age range
    try:
        age = int(age)
        if age < MIN_PATIENT_AGE or age > MAX_PATIENT_AGE:
            return jsonify({
                "error": f"Age must be between {MIN_PATIENT_AGE} and {MAX_PATIENT_AGE}"
            }), 400
    except ValueError:
        return jsonify({"error": "Age must be a valid number"}), 400

    # Validate name length
    if len(name.strip()) < 2:
        return jsonify({"error": "Name must be at least 2 characters long"}), 400

    # Validate contact length
    if len(contact.strip()) < 9:
        return jsonify({"error": "Contact number must be at least 9 digits"}), 400

    # Create patient
    try:
        new_patient = Patient(name=name.strip(), age=age, contact=contact.strip())
        db.session.add(new_patient)
        db.session.commit()

        return jsonify({
            "message": f"{MSG_PATIENT_CREATED} by {current_user}",
            "patient": {
                "id": new_patient.id,
                "name": new_patient.name,
                "age": new_patient.age,
                "contact": new_patient.contact
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create patient"}), 500


# ============================================================
# GET ALL PATIENTS - Allowed: all authenticated users
# ============================================================
@patient_routes.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    """
    Retrieve all patients with pagination and search.
    Query params: page (default: 1), per_page (default: 10), search (optional)
    """
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)  # Max 100 items per page

    # Get search parameter
    search = request.args.get('search', '', type=str)

    # Build query with optional search
    query = Patient.query

    if search:
        query = query.filter(Patient.name.ilike(f'%{search}%'))

    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    patients = pagination.items

    return jsonify({
        "patients": [
            {
                "id": p.id,
                "name": p.name,
                "age": p.age,
                "contact": p.contact
            }
            for p in patients
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }), 200


# ============================================================
# GET PATIENT BY ID - Allowed: all authenticated users
# ============================================================
@patient_routes.route('/patients/<int:id>', methods=['GET'])
@jwt_required()
def get_patient(id):
    """
    Retrieve a specific patient by ID.
    """
    patient = Patient.query.get(id)

    if not patient:
        return jsonify({"error": ERR_PATIENT_NOT_FOUND}), 404

    return jsonify({
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "contact": patient.contact
    }), 200


# ============================================================
# UPDATE PATIENT - Allowed: admin, doctor, nurse
# ============================================================
@patient_routes.route('/patients/<int:id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'doctor', 'nurse')
def update_patient(id):
    """
    Update an existing patient's information.
    Allowed roles: admin, doctor, nurse
    """
    patient = Patient.query.get(id)

    if not patient:
        return jsonify({"error": ERR_PATIENT_NOT_FOUND}), 404

    data = request.json

    # Validate and update fields
    try:
        # Update name if provided
        if 'name' in data:
            name = data['name'].strip()
            if len(name) < 2:
                return jsonify({"error": "Name must be at least 2 characters long"}), 400
            patient.name = name

        # Update age if provided
        if 'age' in data:
            age = int(data['age'])
            if age < MIN_PATIENT_AGE or age > MAX_PATIENT_AGE:
                return jsonify({
                    "error": f"Age must be between {MIN_PATIENT_AGE} and {MAX_PATIENT_AGE}"
                }), 400
            patient.age = age

        # Update contact if provided
        if 'contact' in data:
            contact = data['contact'].strip()
            if len(contact) < 9:
                return jsonify({"error": "Contact number must be at least 9 digits"}), 400
            patient.contact = contact

        db.session.commit()

        return jsonify({
            "message": MSG_PATIENT_UPDATED,
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "contact": patient.contact
            }
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid data format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update patient"}), 500


# ============================================================
# DELETE PATIENT - Allowed: admin only
# ============================================================
@patient_routes.route('/patients/<int:id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_patient(id):
    """
    Delete a patient from the system.
    Allowed roles: admin only
    """
    patient = Patient.query.get(id)

    if not patient:
        return jsonify({"error": ERR_PATIENT_NOT_FOUND}), 404

    try:
        db.session.delete(patient)
        db.session.commit()
        return jsonify({"message": MSG_PATIENT_DELETED}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete patient"}), 500