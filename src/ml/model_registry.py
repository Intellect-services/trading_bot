"""Model registry for versioning and tracking ML models."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for tracking ML models, versions, and performance metrics."""

    def __init__(self, registry_path: str | Path = "models/registry.json") -> None:
        """Initialize model registry.

        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._registry: dict[str, Any] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path) as f:
                    self._registry = json.load(f)
                self.logger.info(f"Loaded registry with {len(self._registry)} models")
            except Exception as e:
                self.logger.error(f"Error loading registry: {e}")
                self._registry = {}
        else:
            self._registry = {}

    def _save_registry(self) -> None:
        """Save registry to disk."""
        try:
            with open(self.registry_path, "w") as f:
                json.dump(self._registry, f, indent=2, default=str)
            self.logger.debug("Saved registry to disk")
        except Exception as e:
            self.logger.error(f"Error saving registry: {e}")

    def register_model(
        self,
        model_id: str,
        version: str,
        model_path: str | Path,
        model_type: str,
        training_metrics: dict[str, Any] | None = None,
        feature_set: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a new model version.

        Args:
            model_id: Unique model identifier
            version: Model version string
            model_path: Path to saved model file
            model_type: Type of model (e.g., 'classification', 'regression')
            training_metrics: Training performance metrics
            feature_set: List of feature names used
            metadata: Additional metadata
        """
        if model_id not in self._registry:
            self._registry[model_id] = {
                "versions": [],
                "created_at": datetime.now().isoformat(),
                "latest_version": None,
            }

        version_info = {
            "version": version,
            "model_path": str(model_path),
            "model_type": model_type,
            "training_metrics": training_metrics or {},
            "feature_set": feature_set or [],
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
            "status": "active",
            "performance_metrics": {},
        }

        self._registry[model_id]["versions"].append(version_info)
        self._registry[model_id]["latest_version"] = version

        self._save_registry()
        self.logger.info(f"Registered model {model_id} version {version}")

    def get_model_info(self, model_id: str, version: str | None = None) -> dict[str, Any] | None:
        """Get information about a model.

        Args:
            model_id: Model identifier
            version: Optional specific version (default: latest)

        Returns:
            Model information dictionary or None if not found
        """
        if model_id not in self._registry:
            return None

        model_info = self._registry[model_id]

        if version is None:
            version = model_info.get("latest_version")

        if version is None:
            return None

        # Find version
        for v_info in model_info["versions"]:
            if v_info["version"] == version:
                return {
                    "model_id": model_id,
                    **v_info,
                }

        return None

    def update_performance_metrics(
        self,
        model_id: str,
        version: str,
        metrics: dict[str, Any],
    ) -> None:
        """Update performance metrics for a model.

        Args:
            model_id: Model identifier
            version: Model version
            metrics: Performance metrics dictionary
        """
        if model_id not in self._registry:
            self.logger.warning(f"Model {model_id} not found in registry")
            return

        # Find version
        for v_info in self._registry[model_id]["versions"]:
            if v_info["version"] == version:
                v_info["performance_metrics"].update(metrics)
                v_info["performance_metrics"]["last_updated"] = datetime.now().isoformat()
                self._save_registry()
                self.logger.info(f"Updated performance metrics for {model_id} v{version}")
                return

        self.logger.warning(f"Version {version} not found for model {model_id}")

    def list_models(self) -> list[dict[str, Any]]:
        """List all registered models.

        Returns:
            List of model information dictionaries
        """
        models = []
        for model_id, info in self._registry.items():
            models.append(
                {
                    "model_id": model_id,
                    "latest_version": info.get("latest_version"),
                    "created_at": info.get("created_at"),
                    "num_versions": len(info.get("versions", [])),
                }
            )
        return models

    def get_latest_version(self, model_id: str) -> str | None:
        """Get the latest version for a model.

        Args:
            model_id: Model identifier

        Returns:
            Latest version string or None
        """
        if model_id not in self._registry:
            return None
        return self._registry[model_id].get("latest_version")

    def deactivate_model(self, model_id: str, version: str) -> None:
        """Deactivate a model version.

        Args:
            model_id: Model identifier
            version: Model version
        """
        if model_id not in self._registry:
            return

        for v_info in self._registry[model_id]["versions"]:
            if v_info["version"] == version:
                v_info["status"] = "inactive"
                self._save_registry()
                self.logger.info(f"Deactivated model {model_id} version {version}")
                return

    def compare_versions(self, model_id: str, version1: str, version2: str) -> dict[str, Any]:
        """Compare two model versions.

        Args:
            model_id: Model identifier
            version1: First version
            version2: Second version

        Returns:
            Comparison dictionary
        """
        info1 = self.get_model_info(model_id, version1)
        info2 = self.get_model_info(model_id, version2)

        if not info1 or not info2:
            return {}

        return {
            "version1": info1,
            "version2": info2,
            "comparison": {
                "training_metrics": self._compare_dicts(
                    info1.get("training_metrics", {}),
                    info2.get("training_metrics", {}),
                ),
                "performance_metrics": self._compare_dicts(
                    info1.get("performance_metrics", {}),
                    info2.get("performance_metrics", {}),
                ),
            },
        }

    @staticmethod
    def _compare_dicts(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
        """Compare two dictionaries."""
        all_keys = set(dict1.keys()) | set(dict2.keys())
        comparison = {}
        for key in all_keys:
            val1 = dict1.get(key)
            val2 = dict2.get(key)
            if val1 != val2:
                comparison[key] = {"version1": val1, "version2": val2}
        return comparison


class ModelMonitor:
    """Monitor model performance in production."""

    def __init__(self, registry: ModelRegistry) -> None:
        """Initialize model monitor.

        Args:
            registry: Model registry instance
        """
        self.registry = registry
        self.logger = logging.getLogger(__name__)
        self.performance_history: list[dict[str, Any]] = []

    def log_prediction(
        self,
        model_id: str,
        version: str,
        prediction: float,
        confidence: float,
        actual_outcome: float | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """Log a model prediction.

        Args:
            model_id: Model identifier
            version: Model version
            prediction: Model prediction
            confidence: Prediction confidence
            actual_outcome: Actual outcome (if available)
            timestamp: Prediction timestamp
        """
        log_entry = {
            "model_id": model_id,
            "version": version,
            "prediction": prediction,
            "confidence": confidence,
            "actual_outcome": actual_outcome,
            "timestamp": (timestamp or datetime.now()).isoformat(),
        }

        self.performance_history.append(log_entry)

        # Update metrics periodically
        if len(self.performance_history) % 100 == 0:
            self._update_metrics(model_id, version)

    def calculate_metrics(
        self, model_id: str, version: str, min_confidence: float = 0.5
    ) -> dict[str, Any]:
        """Calculate performance metrics for a model.

        Args:
            model_id: Model identifier
            version: Model version
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary with performance metrics
        """
        model_predictions = [
            p
            for p in self.performance_history
            if p["model_id"] == model_id
            and p["version"] == version
            and p.get("confidence", 0) >= min_confidence
            and p.get("actual_outcome") is not None
        ]

        if not model_predictions:
            return {"error": "Insufficient data for metrics calculation"}

        predictions = [p["prediction"] for p in model_predictions]
        outcomes = [p["actual_outcome"] for p in model_predictions]

        # Calculate accuracy (for classification)
        if all(isinstance(p, (int, float)) and p in [-1, 0, 1] for p in predictions):
            correct = sum(1 for p, o in zip(predictions, outcomes, strict=False) if p == o)
            accuracy = correct / len(predictions) if predictions else 0.0

            # Precision/recall for buy signals
            buy_predictions = [i for i, p in enumerate(predictions) if p == 1]
            if buy_predictions:
                buy_outcomes = [outcomes[i] for i in buy_predictions]
                true_positives = sum(1 for o in buy_outcomes if o == 1)
                precision = true_positives / len(buy_predictions) if buy_predictions else 0.0
            else:
                precision = 0.0

            # Recall
            actual_buys = [i for i, o in enumerate(outcomes) if o == 1]
            if actual_buys:
                predicted_buys = [predictions[i] for i in actual_buys]
                true_positives = sum(1 for p in predicted_buys if p == 1)
                recall = true_positives / len(actual_buys) if actual_buys else 0.0
            else:
                recall = 0.0

            return {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": 2 * (precision * recall) / (precision + recall + 1e-8),
                "total_predictions": len(model_predictions),
            }

        # Calculate MSE/R2 for regression
        import numpy as np

        predictions_array = np.array(predictions)
        outcomes_array = np.array(outcomes)

        mse = float(np.mean((predictions_array - outcomes_array) ** 2))
        mae = float(np.mean(np.abs(predictions_array - outcomes_array)))

        return {
            "mse": mse,
            "mae": mae,
            "rmse": float(np.sqrt(mse)),
            "total_predictions": len(model_predictions),
        }

    def _update_metrics(self, model_id: str, version: str) -> None:
        """Update metrics in registry."""
        metrics = self.calculate_metrics(model_id, version)
        self.registry.update_performance_metrics(model_id, version, metrics)
