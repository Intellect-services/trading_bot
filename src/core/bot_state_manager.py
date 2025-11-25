"""Bot State Manager for persisting and managing bot state across sessions."""

import logging
from datetime import datetime
from typing import Any

from src.common.models.user_settings import UserSettings
from src.infrastructure import db_config

logger = logging.getLogger(__name__)


class BotStateManager:
    """Manages bot state persistence in database."""

    BOT_AUTO_START_KEY = "bot_auto_start"
    BOT_IS_RUNNING_KEY = "bot_is_running"
    BOT_STARTED_AT_KEY = "bot_started_at"
    BOT_STOPPED_AT_KEY = "bot_stopped_at"

    @staticmethod
    def get_bot_auto_start(user_id: int) -> bool:
        """Get bot auto-start setting for user.

        Args:
            user_id: User ID

        Returns:
            True if bot should auto-start, False otherwise
        """
        try:
            with db_config.get_session() as session:
                setting = (
                    session.query(UserSettings)
                    .filter_by(user_id=user_id, key=BotStateManager.BOT_AUTO_START_KEY)
                    .first()
                )

                if setting and setting.value is not None:
                    return bool(setting.value)
                return False
        except Exception as e:
            logger.error(f"Error getting bot_auto_start for user {user_id}: {e}")
            return False

    @staticmethod
    def set_bot_auto_start(user_id: int, auto_start: bool) -> None:
        """Set bot auto-start setting for user.

        Args:
            user_id: User ID
            auto_start: Whether bot should auto-start
        """
        try:
            with db_config.get_session() as session:
                setting = (
                    session.query(UserSettings)
                    .filter_by(user_id=user_id, key=BotStateManager.BOT_AUTO_START_KEY)
                    .first()
                )

                if setting:
                    setting.value = auto_start
                    setting.updated_at = datetime.utcnow()
                else:
                    setting = UserSettings(
                        user_id=user_id, key=BotStateManager.BOT_AUTO_START_KEY, value=auto_start
                    )
                    session.add(setting)

                session.commit()
                logger.info(f"Set bot_auto_start={auto_start} for user {user_id}")
        except Exception as e:
            logger.error(f"Error setting bot_auto_start for user {user_id}: {e}")
            session.rollback()
            raise

    @staticmethod
    def get_bot_is_running(user_id: int) -> bool:
        """Get bot running status from database.

        Args:
            user_id: User ID

        Returns:
            True if bot is marked as running, False otherwise
        """
        try:
            with db_config.get_session() as session:
                setting = (
                    session.query(UserSettings)
                    .filter_by(user_id=user_id, key=BotStateManager.BOT_IS_RUNNING_KEY)
                    .first()
                )

                if setting and setting.value is not None:
                    return bool(setting.value)
                return False
        except Exception as e:
            logger.error(f"Error getting bot_is_running for user {user_id}: {e}")
            return False

    @staticmethod
    def set_bot_is_running(user_id: int, is_running: bool) -> None:
        """Set bot running status in database.

        Args:
            user_id: User ID
            is_running: Whether bot is running
        """
        try:
            with db_config.get_session() as session:
                setting = (
                    session.query(UserSettings)
                    .filter_by(user_id=user_id, key=BotStateManager.BOT_IS_RUNNING_KEY)
                    .first()
                )

                if setting:
                    setting.value = is_running
                    setting.updated_at = datetime.utcnow()
                else:
                    setting = UserSettings(
                        user_id=user_id, key=BotStateManager.BOT_IS_RUNNING_KEY, value=is_running
                    )
                    session.add(setting)

                # Update started_at or stopped_at timestamp
                if is_running:
                    started_setting = (
                        session.query(UserSettings)
                        .filter_by(user_id=user_id, key=BotStateManager.BOT_STARTED_AT_KEY)
                        .first()
                    )
                    if started_setting:
                        started_setting.value = datetime.utcnow().isoformat()
                        started_setting.updated_at = datetime.utcnow()
                    else:
                        started_setting = UserSettings(
                            user_id=user_id,
                            key=BotStateManager.BOT_STARTED_AT_KEY,
                            value=datetime.utcnow().isoformat(),
                        )
                        session.add(started_setting)
                else:
                    stopped_setting = (
                        session.query(UserSettings)
                        .filter_by(user_id=user_id, key=BotStateManager.BOT_STOPPED_AT_KEY)
                        .first()
                    )
                    if stopped_setting:
                        stopped_setting.value = datetime.utcnow().isoformat()
                        stopped_setting.updated_at = datetime.utcnow()
                    else:
                        stopped_setting = UserSettings(
                            user_id=user_id,
                            key=BotStateManager.BOT_STOPPED_AT_KEY,
                            value=datetime.utcnow().isoformat(),
                        )
                        session.add(stopped_setting)

                session.commit()
                logger.info(f"Set bot_is_running={is_running} for user {user_id}")
        except Exception as e:
            logger.error(f"Error setting bot_is_running for user {user_id}: {e}")
            session.rollback()
            raise

    @staticmethod
    def get_users_with_auto_start() -> list[int]:
        """Get list of user IDs that have auto-start enabled.

        Returns:
            List of user IDs with bot_auto_start=True
        """
        try:
            with db_config.get_session() as session:
                settings = (
                    session.query(UserSettings)
                    .filter_by(key=BotStateManager.BOT_AUTO_START_KEY, value=True)
                    .all()
                )

                return [setting.user_id for setting in settings]
        except Exception as e:
            logger.error(f"Error getting users with auto-start: {e}")
            return []

    @staticmethod
    def get_bot_state(user_id: int) -> dict[str, Any]:
        """Get complete bot state for user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with bot state information
        """
        try:
            with db_config.get_session() as session:
                settings = (
                    session.query(UserSettings)
                    .filter_by(user_id=user_id)
                    .filter(
                        UserSettings.key.in_(
                            [
                                BotStateManager.BOT_AUTO_START_KEY,
                                BotStateManager.BOT_IS_RUNNING_KEY,
                                BotStateManager.BOT_STARTED_AT_KEY,
                                BotStateManager.BOT_STOPPED_AT_KEY,
                            ]
                        )
                    )
                    .all()
                )

                state: dict[str, Any] = {
                    "bot_auto_start": False,
                    "bot_is_running": False,
                    "bot_started_at": None,
                    "bot_stopped_at": None,
                }

                for setting in settings:
                    if setting.key == BotStateManager.BOT_AUTO_START_KEY:
                        state["bot_auto_start"] = (
                            bool(setting.value) if setting.value is not None else False
                        )
                    elif setting.key == BotStateManager.BOT_IS_RUNNING_KEY:
                        state["bot_is_running"] = (
                            bool(setting.value) if setting.value is not None else False
                        )
                    elif setting.key == BotStateManager.BOT_STARTED_AT_KEY:
                        state["bot_started_at"] = setting.value
                    elif setting.key == BotStateManager.BOT_STOPPED_AT_KEY:
                        state["bot_stopped_at"] = setting.value

                return state
        except Exception as e:
            logger.error(f"Error getting bot state for user {user_id}: {e}")
            return {
                "bot_auto_start": False,
                "bot_is_running": False,
                "bot_started_at": None,
                "bot_stopped_at": None,
            }
