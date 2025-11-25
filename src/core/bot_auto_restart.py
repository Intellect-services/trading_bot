"""Auto-restart bots on Flask application startup."""

import logging
import threading
import time

logger = logging.getLogger(__name__)


def auto_restart_bots(app: "Flask") -> None:
    """Auto-restart bots for users with auto-start enabled.

    This function should be called on Flask application startup.
    It runs in a separate thread to avoid blocking app startup.

    Args:
        app: Flask application instance
    """

    def _restart_bots():
        """Internal function to restart bots in background thread."""
        # Wait a bit for Flask to fully initialize
        time.sleep(5)

        try:
            from src.app import get_user_trading_bot
            from src.core.bot_state_manager import BotStateManager

            with app.app_context():
                # Get all users with auto-start enabled
                user_ids = BotStateManager.get_users_with_auto_start()

                if not user_ids:
                    logger.info("No users with auto-start enabled")
                    return

                logger.info(f"Auto-restarting bots for {len(user_ids)} user(s)")

                for user_id in user_ids:
                    try:
                        # Check if bot should be running
                        bot_state = BotStateManager.get_bot_state(user_id)

                        if bot_state.get("bot_auto_start") and bot_state.get("bot_is_running"):
                            logger.info(f"Auto-restarting bot for user {user_id}")

                            # Get or create bot instance
                            trading_bot = get_user_trading_bot(user_id)

                            if trading_bot is None:
                                logger.warning(
                                    f"Could not create bot for user {user_id} - credentials may be missing"
                                )
                                # Mark as not running since we couldn't start it
                                BotStateManager.set_bot_is_running(user_id, False)
                                continue

                            # Check if bot is already running
                            if trading_bot.is_running:
                                logger.info(f"Bot for user {user_id} is already running")
                                continue

                            # Start the bot
                            trading_bot.start()

                            # Verify it started
                            if trading_bot.is_running:
                                logger.info(f"Successfully auto-started bot for user {user_id}")
                            else:
                                logger.warning(f"Bot for user {user_id} failed to start")
                                BotStateManager.set_bot_is_running(user_id, False)

                    except Exception as e:
                        logger.error(
                            f"Error auto-restarting bot for user {user_id}: {e}", exc_info=True
                        )
                        # Mark as not running on error
                        try:
                            BotStateManager.set_bot_is_running(user_id, False)
                        except Exception:
                            pass

                logger.info("Auto-restart complete")

        except Exception as e:
            logger.error(f"Error in auto-restart thread: {e}", exc_info=True)

    # Start auto-restart in background thread
    restart_thread = threading.Thread(target=_restart_bots, daemon=True, name="BotAutoRestart")
    restart_thread.start()
    logger.info("Bot auto-restart thread started")
