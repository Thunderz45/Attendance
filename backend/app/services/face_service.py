import base64
import json
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class FaceService:
    def __init__(self):
        # Load OpenCV Haar Cascade face detector
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            logger.error("Failed to load OpenCV face cascade classifier.")

    def decode_base64_image(self, base64_str):
        """Decode base64 image string into OpenCV BGR image numpy array."""
        try:
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            img_bytes = base64.b64decode(base64_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            logger.error(f"Error decoding base64 image: {str(e)}")
            return None

    def detect_faces(self, img):
        """
        Detect faces in image.
        Returns list of (x, y, w, h) bounding boxes.
        """
        if img is None:
            return []
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply histogram equalization for lighting invariance
        gray = cv2.equalizeHist(gray)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        return faces

    def check_blur(self, face_gray, threshold=20.0):
        """Variance of Laplacian blur check."""
        variance = cv2.Laplacian(face_gray, cv2.CV_64F).var()
        return variance >= threshold, variance

    def extract_face_embedding(self, img, face_box=None):
        """
        Extract normalized spatial & LBP feature embedding vector (256-d) from face region.
        """
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if face_box is None:
            faces = self.detect_faces(img)
            if len(faces) != 1:
                return None
            face_box = faces[0]

        x, y, w, h = face_box
        
        # Check boundary bounds
        img_h, img_w = gray.shape
        if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
            return None

        # Extract Face ROI
        face_roi = gray[y:y+h, x:x+w]
        
        # Blur quality check
        is_sharp, _ = self.check_blur(face_roi)
        if not is_sharp:
            logger.warning("Face image too blurry for reliable embedding.")

        # Resize ROI to canonical size 128x128
        resized = cv2.resize(face_roi, (128, 128))

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        norm_face = clahe.apply(resized)

        # Extract Spatial Pyramids & Local Binary Pattern (LBP) features
        # Divide into 4x4 spatial grid (16 cells of 32x32)
        feature_vector = []
        cell_size = 32
        for r in range(4):
            for c in range(4):
                cell = norm_face[r*cell_size:(r+1)*cell_size, c*cell_size:(c+1)*cell_size]
                
                # Compute normalized histogram of intensity
                hist, _ = np.histogram(cell, bins=16, range=(0, 256))
                hist = hist.astype("float32")
                hist /= (hist.sum() + 1e-7)
                feature_vector.extend(hist)

        # Also extract downsampled direct spatial features (16x16 = 256 values)
        spatial = cv2.resize(norm_face, (16, 16)).flatten().astype("float32")
        spatial /= (np.linalg.norm(spatial) + 1e-7)

        # Combine into unified 512-d feature vector
        combined = np.hstack([np.array(feature_vector, dtype="float32"), spatial])
        # L2 Normalize final embedding vector
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm

        return combined.tolist()

    @staticmethod
    def calculate_distance(embedding1, embedding2):
        """
        Calculate Euclidean & Cosine distance between two normalized feature vectors.
        Returns float distance score (0.0 = identical, 1.0 = completely different).
        """
        vec1 = np.array(embedding1, dtype="float32")
        vec2 = np.array(embedding2, dtype="float32")

        if vec1.shape != vec2.shape:
            return 1.0

        # Cosine distance = 1 - cosine_similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 1.0

        cosine_sim = dot_product / (norm1 * norm2)
        # Clamp to [0, 1]
        cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
        distance = 1.0 - max(0.0, float(cosine_sim))
        return distance

    def find_matching_student(self, candidate_embedding, registered_embeddings, threshold=0.42):
        """
        Compare candidate embedding against a dict/list of registered embeddings:
        registered_embeddings = [(student_id, student_obj, embedding_vector)]
        Returns (matched_student_obj, best_distance) or (None, float)
        """
        if not candidate_embedding or not registered_embeddings:
            return None, 1.0

        best_distance = 1.0
        matched_student = None

        for student, stored_vector in registered_embeddings:
            dist = self.calculate_distance(candidate_embedding, stored_vector)
            if dist < best_distance:
                best_distance = dist
                matched_student = student

        if best_distance <= threshold:
            return matched_student, best_distance

        return None, best_distance

face_service = FaceService()
