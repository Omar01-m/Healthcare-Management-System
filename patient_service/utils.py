"""
Utility functions for the Patient Service
"""

from models import AuditLog, db
from datetime import datetime
import json


def log_audit(entity_type, entity_id, action, user_email, changes=None):
    """
    Log an audit trail entry

    Args:
        entity_type (str): Type of entity ('patient', 'medical_record', etc.)
        entity_id (int): ID of the entity
        action (str): Action performed ('CREATE', 'UPDATE', 'DELETE')
        user_email (str): Email of user who performed the action
        changes (dict): Dictionary of changes (optional)
    """
    try:
        audit_entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_email=user_email,
            timestamp=datetime.utcnow(),
            changes=json.dumps(changes) if changes else None
        )
        db.session.add(audit_entry)
        db.session.commit()
    except Exception as e:
        print(f"Failed to log audit: {str(e)}")


def send_notification_event(event_type, data):
    """
    Placeholder for sending notification events
    In production, this would send a message to RabbitMQ/message queue
    that the Notification Service would consume

    Args:
        event_type (str): Type of event ('patient_created', 'appointment_booked', etc.)
        data (dict): Event data
    """
    # For now, just log it
    print(f"📧 NOTIFICATION EVENT: {event_type}")
    print(f"   Data: {json.dumps(data, indent=2)}")

    # TODO: In production, send to message queue
    # Example: rabbitmq_client.publish(exchange='notifications', routing_key=event_type, body=json.dumps(data))