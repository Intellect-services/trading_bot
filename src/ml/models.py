"""Concrete ML model implementations for trading strategies.

Provides lightweight model implementations using scikit-learn.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.model_selection import train_test_split

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RandomForestClassifier = None  # type: ignore[assignment, misc]
    RandomForestRegressor = None  # type: ignore[assignment, misc]

from src.ml.model_interface import ClassificationModel, RegressionModel

logger = logging.getLogger(__name__)


class SklearnClassificationModel(ClassificationModel):
    """Scikit-learn based classification model for entry/exit signals."""

    def __init__(
        self,
        model_id: str | None = None,
        version: str = "1.0.0",
        n_estimators: int = 100,
        max_depth: int = 10,
        min_samples_split: int = 5,
        random_state: int = 42,
    ) -> None:
        """Initialize sklearn classification model.

        Args:
            model_id: Unique model identifier
            version: Model version
            n_estimators: Number of trees in random forest
            max_depth: Maximum tree depth
            min_samples_split: Minimum samples to split a node
            random_state: Random seed
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required for SklearnClassificationModel. "
                "Install it with: pip install scikit-learn"
            )
        super().__init__(model_id=model_id, version=version)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self.model: RandomForestClassifier | None = None

    def train(
        self,
        X: pd.DataFrame | np.ndarray,
        y: pd.Series | np.ndarray,
        test_size: float = 0.2,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Train the classification model.

        Args:
            X: Feature matrix
            y: Target labels (buy=1, hold=0, sell=-1)
            test_size: Fraction of data to use for testing
            **kwargs: Additional training parameters

        Returns:
            Dictionary with training metrics
        """
        # Convert to numpy if needed
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, (pd.Series, pd.DataFrame)):
            y = y.values

        # Handle NaN values
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]

        if len(X) == 0:
            raise ValueError("No valid training data after removing NaN values")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=y if len(np.unique(y)) > 1 else None,
        )

        # Initialize and train model
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=self.random_state,
            n_jobs=-1,
        )

        self.model.fit(X_train, y_train)

        # Calculate metrics
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        # Feature importance
        if hasattr(self.model, "feature_importances_"):
            feature_importance = self.model.feature_importances_.tolist()
        else:
            feature_importance = []

        self.trained = True
        self.metadata.update(
            {
                "train_score": float(train_score),
                "test_score": float(test_score),
                "n_samples": len(X_train),
                "n_features": X_train.shape[1],
                "n_classes": len(np.unique(y)),
                "feature_importance": feature_importance,
            }
        )

        metrics = {
            "train_accuracy": float(train_score),
            "test_accuracy": float(test_score),
            "n_samples": len(X_train),
        }

        logger.info(
            f"Trained classification model: train_acc={train_score:.3f}, test_acc={test_score:.3f}"
        )

        return metrics

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Make predictions.

        Args:
            X: Feature matrix

        Returns:
            Predicted class labels
        """
        if not self.trained or self.model is None:
            raise ValueError("Model must be trained before making predictions")

        if isinstance(X, pd.DataFrame):
            X = X.values

        # Handle NaN
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        return self.model.predict(X)

    def _predict_proba_impl(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Internal implementation of predict_proba."""
        if isinstance(X, pd.DataFrame):
            X = X.values

        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        return self.model.predict_proba(X)  # type: ignore[union-attr]

    def _get_model_object(self) -> Any:
        """Get the underlying model object."""
        return self.model

    def _set_model_object(self, model: Any) -> None:
        """Set the underlying model object."""
        self.model = model


class SklearnRegressionModel(RegressionModel):
    """Scikit-learn based regression model for expected return prediction."""

    def __init__(
        self,
        model_id: str | None = None,
        version: str = "1.0.0",
        n_estimators: int = 100,
        max_depth: int = 10,
        min_samples_split: int = 5,
        random_state: int = 42,
    ) -> None:
        """Initialize sklearn regression model.

        Args:
            model_id: Unique model identifier
            version: Model version
            n_estimators: Number of trees in random forest
            max_depth: Maximum tree depth
            min_samples_split: Minimum samples to split a node
            random_state: Random seed
        """
        super().__init__(model_id=model_id, version=version)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self.model: RandomForestRegressor | None = None

    def train(
        self,
        X: pd.DataFrame | np.ndarray,
        y: pd.Series | np.ndarray,
        test_size: float = 0.2,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Train the regression model.

        Args:
            X: Feature matrix
            y: Target values (expected returns)
            test_size: Fraction of data to use for testing
            **kwargs: Additional training parameters

        Returns:
            Dictionary with training metrics
        """
        # Convert to numpy if needed
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, (pd.Series, pd.DataFrame)):
            y = y.values

        # Handle NaN values
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]

        if len(X) == 0:
            raise ValueError("No valid training data after removing NaN values")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state
        )

        # Initialize and train model
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=self.random_state,
            n_jobs=-1,
        )

        self.model.fit(X_train, y_train)

        # Calculate metrics
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        # Calculate MSE
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        train_mse = float(np.mean((train_pred - y_train) ** 2))
        test_mse = float(np.mean((test_pred - y_test) ** 2))

        # Feature importance
        if hasattr(self.model, "feature_importances_"):
            feature_importance = self.model.feature_importances_.tolist()
        else:
            feature_importance = []

        self.trained = True
        self.metadata.update(
            {
                "train_score": float(train_score),
                "test_score": float(test_score),
                "train_mse": train_mse,
                "test_mse": test_mse,
                "n_samples": len(X_train),
                "n_features": X_train.shape[1],
                "feature_importance": feature_importance,
            }
        )

        metrics = {
            "train_r2": float(train_score),
            "test_r2": float(test_score),
            "train_mse": train_mse,
            "test_mse": test_mse,
            "n_samples": len(X_train),
        }

        logger.info(
            f"Trained regression model: train_r2={train_score:.3f}, test_r2={test_score:.3f}, "
            f"test_mse={test_mse:.6f}"
        )

        return metrics

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Make predictions.

        Args:
            X: Feature matrix

        Returns:
            Predicted expected returns
        """
        if not self.trained or self.model is None:
            raise ValueError("Model must be trained before making predictions")

        if isinstance(X, pd.DataFrame):
            X = X.values

        # Handle NaN
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        return self.model.predict(X)

    def _get_model_object(self) -> Any:
        """Get the underlying model object."""
        return self.model

    def _set_model_object(self, model: Any) -> None:
        """Set the underlying model object."""
        self.model = model
