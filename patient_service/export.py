"""
Export functionality for generating reports
"""

import csv
import io
from datetime import datetime


def export_patients_to_csv(patients):
    """
    Export a list of patients to CSV format

    Args:
        patients (list): List of Patient objects

    Returns:
        str: CSV data as string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['ID', 'Name', 'Age', 'Contact', 'Created At', 'Created By'])

    # Write patient data
    for patient in patients:
        writer.writerow([
            patient.id,
            patient.name,
            patient.age,
            patient.contact,
            patient.created_at.strftime('%Y-%m-%d %H:%M:%S') if patient.created_at else '',
            patient.created_by or 'N/A'
        ])

    return output.getvalue()


def export_medical_records_to_csv(records):
    """
    Export medical records to CSV format

    Args:
        records (list): List of MedicalRecord objects

    Returns:
        str: CSV data as string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['ID', 'Patient ID', 'Patient Name', 'Diagnosis', 'Prescription', 'Visit Date', 'Doctor'])

    # Write record data
    for record in records:
        writer.writerow([
            record.id,
            record.patient_id,
            record.patient.name,
            record.diagnosis,
            record.prescription or 'N/A',
            record.visit_date.strftime('%Y-%m-%d %H:%M:%S') if record.visit_date else '',
            record.created_by or 'N/A'
        ])

    return output.getvalue()