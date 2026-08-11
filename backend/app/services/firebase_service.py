import logging
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from flask import current_app

logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        self.project_id = "attendance-a6f14"
        self.db = None
        self._init_firebase()

    def _init_firebase(self):
        """Initialize Firebase Admin SDK or fallback to Firestore REST API."""
        try:
            if not firebase_admin._apps:
                # Initialize with project ID
                app = firebase_admin.initialize_app(options={'projectId': self.project_id})
            self.db = firestore.client()
            logger.info("Firebase Admin SDK initialized successfully for project attendance-a6f14.")
        except Exception as e:
            logger.info("Firebase Admin SDK default credentials not present. Using Firestore REST API handler.")
            self.db = None

    def sync_student(self, student_dict):
        """Sync a student record to Firebase Firestore collection 'students'."""
        try:
            doc_id = str(student_dict.get('student_id') or student_dict.get('id'))
            if self.db:
                self.db.collection('students').document(doc_id).set(student_dict, merge=True)
                logger.info(f"Synced student {doc_id} to Firestore via SDK.")
            else:
                self._rest_post('students', doc_id, student_dict)
        except Exception as e:
            logger.error(f"Firebase sync student error: {str(e)}")

    def sync_attendance(self, attendance_dict):
        """Sync attendance log entry to Firebase Firestore collection 'attendances'."""
        try:
            doc_id = f"{attendance_dict.get('student_id')}_{attendance_dict.get('attendance_date')}"
            if self.db:
                self.db.collection('attendances').document(doc_id).set(attendance_dict, merge=True)
                logger.info(f"Synced attendance record {doc_id} to Firestore via SDK.")
            else:
                self._rest_post('attendances', doc_id, attendance_dict)
        except Exception as e:
            logger.error(f"Firebase sync attendance error: {str(e)}")

    def _rest_post(self, collection, doc_id, data_dict):
        """Fallback REST API call to Firebase Firestore REST Endpoint."""
        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/{collection}?documentId={doc_id}"
            fields = {}
            for k, v in data_dict.items():
                if isinstance(v, bool):
                    fields[k] = {"booleanValue": v}
                elif isinstance(v, int):
                    fields[k] = {"integerValue": str(v)}
                elif isinstance(v, float):
                    fields[k] = {"doubleValue": v}
                else:
                    fields[k] = {"stringValue": str(v) if v is not None else ""}

            payload = {"fields": fields}
            res = requests.patch(f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/{collection}/{doc_id}", json=payload, timeout=3)
            return res.status_code in [200, 201]
        except Exception as err:
            logger.warning(f"Firebase REST sync notice: {str(err)}")
            return False

firebase_service = FirebaseService()
