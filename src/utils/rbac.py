"""Role-Based Access Control utilities and decorators."""

from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import jsonify, request, session

from src.models.user import User

# Role hierarchy: higher number = more permissions
ROLE_HIERARCHY = {"trader": 1, "admin": 2, "owner": 3}

# Permission definitions
PERMISSIONS = {
    "manage_users": ["admin", "owner"],
    "manage_trading": ["admin", "owner"],
    "view_all_trades": ["admin", "owner"],
    "system_config": ["owner"],
    "trade": ["trader", "admin", "owner"],
}


def has_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission.

    Args:
        user: User instance.
        permission: Permission name.

    Returns:
        True if user has permission, False otherwise.
    """
    if permission not in PERMISSIONS:
        return False

    allowed_roles = PERMISSIONS[permission]
    return user.role in allowed_roles


def has_role_or_higher(user: User, required_role: str) -> bool:
    """Check if user has required role or higher in hierarchy.

    Args:
        user: User instance.
        required_role: Minimum required role.

    Returns:
        True if user has required role or higher.
    """
    user_level = ROLE_HIERARCHY.get(user.role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 999)
    return user_level >= required_level


def get_current_user() -> User | None:
    """Get current user from session.

    Returns:
        User instance if logged in, None otherwise.
    """
    user_id = session.get("user_id")
    if not user_id:
        return None

    try:
        user = User.query.get(user_id)
        return user if user is not None else None
    except Exception:
        return None


def login_required(f: Callable) -> Callable:
    """Decorator to require user to be logged in.

    Args:
        f: Function to decorate.

    Returns:
        Decorated function.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not session.get("user_id"):
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            from flask import redirect, url_for

            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def require_email_verified(f: Callable) -> Callable:
    """Decorator to require user's email to be verified.

    Args:
        f: Function to decorate.

    Returns:
        Decorated function.
    """

    @wraps(f)
    @login_required
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if not user or not user.email_verified:
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify(
                    {
                        "status": "error",
                        "message": "Email verification required",
                        "email_verified": False,
                    }
                ), 403
            from flask import flash, redirect, url_for

            flash("Please verify your email address to continue.", "warning")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


def require_role(role: str) -> Callable[[Callable], Callable]:
    """Decorator to require specific role or higher.

    Args:
        role: Required role ('trader', 'admin', or 'owner').

    Returns:
        Decorator function.
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        @login_required
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            user = get_current_user()
            if not user:
                if request.is_json or request.headers.get("Accept") == "application/json":
                    return jsonify({"status": "error", "message": "Authentication required"}), 401
                from flask import redirect, url_for

                return redirect(url_for("login"))

            if not has_role_or_higher(user, role):
                if request.is_json or request.headers.get("Accept") == "application/json":
                    return jsonify(
                        {
                            "status": "error",
                            "message": f"Insufficient permissions. Required role: {role}",
                        }
                    ), 403
                from flask import flash, redirect, url_for

                flash("You don't have permission to access this resource.", "danger")
                return redirect(url_for("index"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_permission(permission: str) -> Callable[[Callable], Callable]:
    """Decorator to require specific permission.

    Args:
        permission: Permission name.

    Returns:
        Decorator function.
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        @login_required
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            user = get_current_user()
            if not user:
                if request.is_json or request.headers.get("Accept") == "application/json":
                    return jsonify({"status": "error", "message": "Authentication required"}), 401
                from flask import redirect, url_for

                return redirect(url_for("login"))

            if not has_permission(user, permission):
                if request.is_json or request.headers.get("Accept") == "application/json":
                    return jsonify(
                        {
                            "status": "error",
                            "message": f"Insufficient permissions. Required: {permission}",
                        }
                    ), 403
                from flask import flash, redirect, url_for

                flash("You don't have permission to access this resource.", "danger")
                return redirect(url_for("index"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_trading_enabled(f: Callable) -> Callable:
    """Decorator to require user to have trading enabled (email verified + credentials configured).

    Args:
        f: Function to decorate.

    Returns:
        Decorated function.
    """

    @wraps(f)
    @require_email_verified
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if not user or not user.can_trade():
            if request.is_json or request.headers.get("Accept") == "application/json":
                return jsonify(
                    {
                        "status": "error",
                        "message": "Trading credentials not configured. Please configure your Alpaca API credentials in Account Settings.",
                        "can_trade": False,
                    }
                ), 403
            from flask import flash, redirect, url_for

            flash("Please configure your trading credentials to enable trading.", "warning")
            return redirect(url_for("account"))
        return f(*args, **kwargs)

    return decorated_function
