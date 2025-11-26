"""Model interface for AI trading strategies.

Provides base classes for ML models used in trading strategies.
"""

import logging
import pickle
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MLModel(ABC):
    """Abstract base class for ML models used in trading."""

    def __init__(self, model_id: str | None = None, version: str = "1.0.0") -> None:
        """Initialize the ML model.

        Args:
            model_id: Unique identifier for this model
            version: Model version string
        """
        self.model_id = model_id or f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.version = version
        self.trained = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self.metadata: dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "version": version,
            "model_id": self.model_id,
        }

    @abstractmethod
    def train(
        self,
        X: pd.DataFrame | np.ndarray,
        y: pd.Series | np.ndarray,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Train the model.

        Args:
            X: Feature matrix
            y: Target labels/values
            **kwargs: Additional training parameters

        Returns:
            Dictionary with training metrics
        """

    @abstractmethod
    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Make predictions.

        Args:
            X: Feature matrix

        Returns:
            Predictions array
        """

    @abstractmethod
    def predict_proba(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Predict class probabilities (for classification models).

        Args:
            X: Feature matrix

        Returns:
            Probability array
        """

    def save(self, filepath: str | Path) -> None:
        """Save the model to disk.

        Args:
            filepath: Path to save the model
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "model": self._get_model_object(),
            "metadata": self.metadata,
            "model_id": self.model_id,
            "version": self.version,
        }

        with open(path, "wb") as f:
            pickle.dump(model_data, f)

        self.logger.info(f"Saved model to {path}")

    def load(self, filepath: str | Path) -> None:
        """Load the model from disk.

        Args:
            filepath: Path to load the model from
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        with open(path, "rb") as f:
            model_data = pickle.load(f)

        self._set_model_object(model_data["model"])
        self.metadata = model_data.get("metadata", {})
        self.model_id = model_data.get("model_id", self.model_id)
        self.version = model_data.get("version", self.version)
        self.trained = True

        self.logger.info(f"Loaded model from {path}")

    @abstractmethod
    def _get_model_object(self) -> Any:
        """Get the underlying model object for serialization."""

    @abstractmethod
    def _set_model_object(self, model: Any) -> None:
        """Set the underlying model object from deserialization."""


class ClassificationModel(MLModel):
    """Base class for classification models (buy/sell/hold)."""

    def predict_proba(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Predict class probabilities.

        Args:
            X: Feature matrix

        Returns:
            Probability array of shape (n_samples, n_classes)
        """
        if not self.trained:
            raise ValueError("Model must be trained before making predictions")

        return self._predict_proba_impl(X)

    @abstractmethod
    def _predict_proba_impl(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Internal implementation of predict_proba."""


class RegressionModel(MLModel):
    """Base class for regression models (expected return prediction)."""

    def predict_proba(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Regression models don't have probabilities.

        Returns predictions as a single-column array for compatibility.

        Args:
            X: Feature matrix

        Returns:
            Predictions array
        """
        return self.predict(X).reshape(-1, 1)


class EnsembleModel(MLModel):
    """Ensemble model that combines multiple models."""

    def __init__(
        self,
        models: list[MLModel],
        weights: list[float] | None = None,
        model_id: str | None = None,
        version: str = "1.0.0",
    ) -> None:
        """Initialize ensemble model.

        Args:
            models: List of models to ensemble
            weights: Optional weights for each model (default: equal weights)
            model_id: Unique identifier
            version: Model version
        """
        super().__init__(model_id=model_id, version=version)
        self.models = models
        self.weights = weights or [1.0 / len(models)] * len(models)

        if len(self.weights) != len(models):
            raise ValueError("Number of weights must match number of models")

        # Normalize weights
        total_weight = sum(self.weights)
        self.weights = [w / total_weight for w in self.weights]

    def train(
        self,
        X: pd.DataFrame | np.ndarray,
        y: pd.Series | np.ndarray,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Train all models in the ensemble.

        Args:
            X: Feature matrix
            y: Target labels/values
            **kwargs: Additional training parameters

        Returns:
            Dictionary with training metrics from all models
        """
        metrics = {}
        for i, model in enumerate(self.models):
            self.logger.info(f"Training model {i+1}/{len(self.models)}")
            model_metrics = model.train(X, y, **kwargs)
            metrics[f"model_{i}"] = model_metrics

        self.trained = all(model.trained for model in self.models)
        metrics["ensemble"] = {"trained": self.trained}

        return metrics

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Make ensemble predictions.

        Args:
            X: Feature matrix

        Returns:
            Weighted average predictions
        """
        if not self.trained:
            raise ValueError("Ensemble must be trained before making predictions")

        predictions = []
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)

        # Weighted average
        weighted_pred = np.zeros_like(predictions[0])
        for pred, weight in zip(predictions, self.weights, strict=False):
            weighted_pred += pred * weight

        return weighted_pred

    def predict_proba(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Make ensemble probability predictions.

        Args:
            X: Feature matrix

        Returns:
            Weighted average probabilities
        """
        if not self.trained:
            raise ValueError("Ensemble must be trained before making predictions")

        probabilities = []
        for model in self.models:
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(X)
                probabilities.append(proba)
            else:
                # Convert regression predictions to probabilities
                pred = model.predict(X)
                # Normalize to [0, 1] range
                pred_normalized = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)
                probabilities.append(pred_normalized.reshape(-1, 1))

        # Weighted average
        weighted_proba = np.zeros_like(probabilities[0])
        for proba, weight in zip(probabilities, self.weights, strict=False):
            weighted_proba += proba * weight

        return weighted_proba

    def _get_model_object(self) -> Any:
        """Get all model objects."""
        return [model._get_model_object() for model in self.models]

    def _set_model_object(self, models: list[Any]) -> None:
        """Set all model objects."""
        for model, model_obj in zip(self.models, models, strict=False):
            model._set_model_object(model_obj)
