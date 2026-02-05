from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Patient, MedicalRecord, db
from decorators import role_required
from utils import log_audit, send_notification_event
from export import export_patients_to_csv, export_medical_records_to_csv
from datetime import datetime
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
# CREATE PATIENT
# ============================================================
@patient_routes.route('/patients', methods=['POST'])
@jwt_required()
@role_required('admin', 'doctor', 'nurse')
def create_patient():
    """Create a new patient with audit logging and notification"""
    data = request.json
    current_user = get_jwt_identity()

    name = data.get('name')
    age = data.get('age')
    contact = data.get('contact')

    if not name or not age or not contact:
        return jsonify({"error": ERR_MISSING_FIELDS}), 400

    try:
        age = int(age)
        if age < MIN_PATIENT_AGE or age > MAX_PATIENT_AGE:
            return jsonify({
                "error": f"Age must be between {MIN_PATIENT_AGE} and {MAX_PATIENT_AGE}"
            }), 400
    except ValueError:
        return jsonify({"error": "Age must be a valid number"}), 400

    if len(name.strip()) < 2:
        return jsonify({"error": "Name must be at least 2 characters long"}), 400

    if len(contact.strip()) < 9:
        return jsonify({"error": "Contact number must be at least 9 digits"}), 400

    try:
        new_patient = Patient(
            name=name.strip(),
            age=age,
            contact=contact.strip(),
            created_by=current_user
        )
        db.session.add(new_patient)
        db.session.commit()

        # Log audit trail
        log_audit('patient', new_patient.id, 'CREATE', current_user, {
            'name': new_patient.name,
            'age': new_patient.age,
            'contact': new_patient.contact
        })

        # Send notification event (placeholder for notification service)
        send_notification_event('patient_created', {
            'patient_id': new_patient.id,
            'patient_name': new_patient.name,
            'patient_contact': new_patient.contact,
            'created_by': current_user
        })

        return jsonify({
            "message": f"{MSG_PATIENT_CREATED} by {current_user}",
            "patient": {
                "id": new_patient.id,
                "name": new_patient.name,
                "age": new_patient.age,
                "contact": new_patient.contact,
                "created_at": new_patient.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create patient"}), 500


# ============================================================
# GET ALL PATIENTS (excluding soft-deleted)
# ============================================================
@patient_routes.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    """Retrieve all active (non-deleted) patients with pagination and search"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)
    search = request.args.get('search', '', type=str)
    include_deleted = request.args.get('include_deleted', 'false', type=str).lower() == 'true'

    # Base query: exclude soft-deleted patients by default
    query = Patient.query

    if not include_deleted:
        query = query.filter_by(is_deleted=False)

    if search:
        query = query.filter(Patient.name.ilike(f'%{search}%'))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    patients = pagination.items

    return jsonify({
        "patients": [
            {
                "id": p.id,
                "name": p.name,
                "age": p.age,
                "contact": p.contact,
                "created_at": p.created_at.isoformat(),
                "is_deleted": p.is_deleted
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
# EXPORT PATIENTS TO CSV
# ============================================================
@patient_routes.route('/patients/export', methods=['GET'])
@jwt_required()
@role_required('admin', 'doctor')
def export_patients():
    """Export all patients to CSV format"""
    include_deleted = request.args.get('include_deleted', 'false', type=str).lower() == 'true'

    query = Patient.query
    if not include_deleted:
        query = query.filter_by(is_deleted=False)

    patients = query.all()
    csv_data = export_patients_to_csv(patients)

    # Create response with CSV data
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=patients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    return response


# ============================================================
# GET PATIENT BY ID
# ============================================================
@patient_routes.route('/patients/<int:id>', methods=['GET'])
@jwt_required()
def get_patient(id):
    """Retrieve a specific patient by ID"""
    patient = Patient.query.filter_by(id=id, is_deleted=False).first()

    if not patient:
        return jsonify({"error": ERR_PATIENT_NOT_FOUND}), 404

    return jsonify({
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "contact": patient.contact,
        "created_at": patient.created_at.isoformat(),
        "created_by": patient.created_by,
        "updated_at": patient.updated_at.isoformat() if patient.updated_at else None,
        "updated_by": patient.updated_by
    }), 200


# ============================================================
# UPDATE PATIENT
# ============================================================
@patient_routes.route('/patients/<int:id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'doctor', 'nurse')
def update_patient(id):
    """Update patient with audit logging"""
    current_user = get_jwt_identity()
    patient = Patient.query.filter_by(id=id, is_deleted=False).first()

    if not patient:
        return jsonify({"error": ERR_PATIENT_NOT_FOUND}), 404

    data = request.json
    changes = {}

    try:
        if 'name' in data:
            name = data['name'].strip()
            if len(name) < 2:
                return jsonify({"error": "Name must be at least 2 characters long"}), 400
            if patient.name != name:
                changes['name'] = {'old': patient.name, 'new': name}
                patient.name = name

        if 'age' in data:
            age = int(data['age'])
            if age < MIN_PATIENT_AGE or age > MAX_PATIENT_AGE:
                return jsonify({
                    "error": f"Age must be between {MIN_PATIENT_AGE} and {MAX_PATIENT_AGE}"
                }), 400
            if patient.age != age:
                changes['age'] = {'old': patient.age, 'new': age}
                patient.age = age

        if 'contact' in data:
            contact = data['contact'].strip()
            if len(contact) < 9:
                return jsonify({"error": "Contact number must be at least 9 digits"}), 400
            if patient.contact != contact:
                changes['contact'] = {'old': patient.contact, 'new': contact}
                patient.contact = contact

        patient.updated_by = current_user
        patient.updated_at = datetime.utcnow()

        db.session.commit()

        # Log audit trail if there were changes
        if changes:
            log_audit('patient', patient.id, 'UPDATE', current_user, changes)

        return jsonify({
            "message": MSG_PATIENT_UPDATED,
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "contact": patient.contact,
                "updated_at": patient.updated_at.isoformat()
            }
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid data format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update patient"}), 500


# ============================================================
# SOFT DELETE PATIENT
# ============================================================
@patient_routes.route('/patients/<int:id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_patient(id):
    """Soft delete a patient (mark as deleted)"""
    current_user = get_jwt_identity()
    patient = Patient.query.filter_by(id=id, is_deleted=False).first()

    if not patient:
        return jsonify({"error": ERR_PATIENT_NOT_FOUND}), 404

    try:
        patient.is_deleted = True
        patient.deleted_at = datetime.utcnow()
        patient.deleted_by = current_user

        db.session.commit()

        # Log audit trail
        log_audit('patient', patient.id, 'DELETE', current_user, {
            'deleted_at': patient.deleted_at.isoformat()
        })

        return jsonify({"message": MSG_PATIENT_DELETED}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete patient"}), 500


# ============================================================
# RESTORE SOFT-DELETED PATIENT
# ============================================================
@patient_routes.route('/patients/<int:id>/restore', methods=['POST'])
@jwt_required()
@role_required('admin')
def restore_patient(id):
    """Restore a soft-deleted patient"""
    current_user = get_jwt_identity()
    patient = Patient.query.filter_by(id=id, is_deleted=True).first()

    if not patient:
        return jsonify({"error": "Patient not found or not deleted"}), 404

    try:
        patient.is_deleted = False
        patient.deleted_at = None
        patient.deleted_by = None
        patient.updated_by = current_user
        patient.updated_at = datetime.utcnow()

        db.session.commit()

        # Log audit trail
        log_audit('patient', patient.id, 'RESTORE', current_user, {
            'restored_at': patient.updated_at.isoformat()
        })

        return jsonify({"message": "Patient restored successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to restore patient"}), 500


# ============================================================
# MEDICAL RECORDS - CREATE
# ============================================================
@patient_routes.route('/patients/<int:patient_id>/medical-records', methods=['POST'])
@jwt_required()
@role_required('admin', 'doctor')
def create_medical_record(patient_id):
    """Create a medical record for a patient"""
    current_user = get_jwt_identity()
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first()

    if not patient:
        return jsonify({"error": ERR_PATIENT_NOT_FOUND}), 404

    data = request.json
    diagnosis = data.get('diagnosis')
    prescription = data.get('prescription')
    notes = data.get('notes')

    if not diagnosis:
        return jsonify({"error": "Diagnosis is required"}), 400

    try:
        record = MedicalRecord(
            patient_id=patient_id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes,
            created_by=current_user
        )
        db.session.add(record)
        db.session.commit()

        # Log audit trail
        log_audit('medical_record', record.id, 'CREATE', current_user, {
            'patient_id': patient_id,
            'diagnosis': diagnosis
        })

        return jsonify({
            "message": "Medical record created successfully",
            "record": {
                "id": record.id,
                "patient_id": record.patient_id,
                "diagnosis": record.diagnosis,
                "prescription": record.prescription,
                "notes": record.notes,
                "visit_date": record.visit_date.isoformat(),
                "created_by": record.created_by
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create medical record"}), 500


# ============================================================
# MEDICAL RECORDS - GET ALL FOR PATIENT
# ============================================================
@patient_routes.route('/patients/<int:patient_id>/medical-records', methods=['GET'])
@jwt_required()
def get_medical_records(patient_id):
    """Get all medical records for a patient"""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first()

    if not patient:
        return jsonify({"error": ERR_PATIENT_NOT_FOUND}), 404

    records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.visit_date.desc()).all()

    return jsonify({
        "patient": {
            "id": patient.id,
            "name": patient.name
        },
        "records": [
            {
                "id": r.id,
                "diagnosis": r.diagnosis,
                "prescription": r.prescription,
                "notes": r.notes,
                "visit_date": r.visit_date.isoformat(),
                "created_by": r.created_by
            }
            for r in records
        ]
    }), 200


# ============================================================
# AUDIT LOGS - GET FOR PATIENT
# ============================================================
@patient_routes.route('/patients/<int:patient_id>/audit-logs', methods=['GET'])
@jwt_required()
@role_required('admin', 'doctor')
def get_patient_audit_logs(patient_id):
    """Get audit logs for a specific patient"""
    from models import AuditLog

    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": ERR_PATIENT_NOT_FOUND}), 404

    logs = AuditLog.query.filter_by(
        entity_type='patient',
        entity_id=patient_id
    ).order_by(AuditLog.timestamp.desc()).all()

    return jsonify({
        "patient_id": patient_id,
        "audit_logs": [
            {
                "id": log.id,
                "action": log.action,
                "user_email": log.user_email,
                "timestamp": log.timestamp.isoformat(),
                "changes": log.changes
            }
            for log in logs
        ]
    }), 200