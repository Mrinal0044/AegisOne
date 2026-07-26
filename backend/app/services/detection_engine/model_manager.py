import os
import pickle
import json
import logging
import time
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest

from app.services.detection_engine.interfaces import DetectionModel

logger = logging.getLogger("app.services.detection_engine.model_manager")
MODEL_STORE_DIR = os.getenv("MODEL_STORE_DIR")
if not MODEL_STORE_DIR:
    # Check if /app exists and is writable, otherwise fall back to host workspace directory
    if os.path.exists("/app") and os.access("/app", os.W_OK):
        MODEL_STORE_DIR = "/app/model_store"
    else:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        MODEL_STORE_DIR = os.path.join(backend_dir, "model_store")


class IsolationForestModel(DetectionModel):
    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.clf = IsolationForest(contamination=self.contamination, random_state=self.random_state)
        self._is_trained = False
        self.features_count = 0

    def train(self, data: List[List[float]]) -> None:
        X = np.array(data)
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)
        self.features_count = X.shape[1]
        
        # Fit model
        self.clf.fit(X)
        self._is_trained = True

    def predict(self, vector: List[float]) -> Dict[str, Any]:
        if not self._is_trained:
            return {"anomaly_score": 0.0, "prediction": 1, "confidence": 1.0}
            
        x = np.array(vector).reshape(1, -1)
        # sklearn IsolationForest predict returns -1 for anomaly, 1 for normal
        pred = int(self.clf.predict(x)[0])
        
        # decision_function returns negative values for anomalies, positive for normal
        decision = float(self.clf.decision_function(x)[0])
        
        # Normalize anomaly score: convert to a scale where higher is more anomalous
        # decision_function lies in [-0.5, 0.5] approx. 
        # Convert decision to anomaly score in [0.0, 1.0]
        anomaly_score = float(np.clip(0.5 - decision, 0.0, 1.0))
        
        # Confidence score: proportional to distance from the boundary
        confidence = float(np.clip(abs(decision) / 0.5, 0.5, 1.0))
        
        return {
            "anomaly_score": anomaly_score,
            "prediction": pred,
            "confidence": confidence
        }

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump({
                "clf": self.clf,
                "contamination": self.contamination,
                "random_state": self.random_state,
                "is_trained": self._is_trained,
                "features_count": self.features_count
            }, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            payload = pickle.load(f)
            self.clf = payload["clf"]
            self.contamination = payload["contamination"]
            self.random_state = payload["random_state"]
            self._is_trained = payload["is_trained"]
            self.features_count = payload["features_count"]

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "algorithm": "IsolationForest",
            "contamination": self.contamination,
            "random_state": self.random_state,
            "is_trained": self._is_trained,
            "features_count": self.features_count
        }


class ModelManager:
    _instance: Optional["ModelManager"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._models: Dict[str, DetectionModel] = {}
        self._manifest: Dict[str, Any] = {}
        
        # Ensure model directory exists
        if not os.path.exists(MODEL_STORE_DIR):
            os.makedirs(MODEL_STORE_DIR, exist_ok=True)
            
        self._load_manifest()

    def _load_manifest(self) -> None:
        manifest_path = os.path.join(MODEL_STORE_DIR, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r") as f:
                    self._manifest = json.load(f)
            except Exception as e:
                logger.error(f"Error loading manifest: {e}")
                self._manifest = {}
        else:
            self._manifest = {}

    def _save_manifest(self) -> None:
        manifest_path = os.path.join(MODEL_STORE_DIR, "manifest.json")
        try:
            with open(manifest_path, "w") as f:
                json.dump(self._manifest, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving manifest: {e}")

    def get_model(self, model_key: str) -> Optional[DetectionModel]:
        """Load from cache or disk on demand."""
        if model_key in self._models:
            return self._models[model_key]

        # Check if saved model exists on disk
        model_path = os.path.join(MODEL_STORE_DIR, f"{model_key}.pkl")
        if os.path.exists(model_path):
            try:
                model = IsolationForestModel()
                model.load(model_path)
                self._models[model_key] = model
                return model
            except Exception as e:
                logger.error(f"Error loading model {model_key} from disk: {e}")
                
        return None

    def save_model(self, model_key: str, model: DetectionModel, training_size: int, duration_sec: float) -> None:
        """Cache model in memory, save binary to disk, and update manifest metadata."""
        model_path = os.path.join(MODEL_STORE_DIR, f"{model_key}.pkl")
        try:
            model.save(model_path)
            self._models[model_key] = model
            
            # Update manifest
            info = model.get_model_info()
            self._manifest[model_key] = {
                "model_name": model_key,
                "version": self._manifest.get(model_key, {}).get("version", 0) + 1,
                "algorithm": info["algorithm"],
                "features_count": info["features_count"],
                "training_dataset_size": training_size,
                "training_duration_seconds": round(duration_sec, 4),
                "training_time": datetime.utcnow().isoformat() + "Z",
                "status": "ACTIVE"
            }
            self._save_manifest()
        except Exception as e:
            logger.error(f"Error saving model {model_key}: {e}", exc_info=True)

    def list_models(self) -> List[Dict[str, Any]]:
        return list(self._manifest.values())

    def get_manifest(self) -> Dict[str, Any]:
        return self._manifest

    def clear_all_models(self) -> None:
        """Clear memory cache, delete model files, and truncate manifest."""
        self._models.clear()
        self._manifest.clear()
        self._save_manifest()
        for filename in os.listdir(MODEL_STORE_DIR):
            if filename.endswith(".pkl") or filename == "manifest.json":
                try:
                    os.remove(os.path.join(MODEL_STORE_DIR, filename))
                except Exception as e:
                    logger.error(f"Failed to delete {filename}: {e}")
        self._load_manifest()


model_manager = ModelManager()
from datetime import datetime
