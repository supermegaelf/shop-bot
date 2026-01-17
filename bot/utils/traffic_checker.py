import logging
from datetime import datetime, timedelta
from aiogram import Bot

from db.methods import get_all_active_users, get_last_traffic_notification, add_traffic_notification
from db.models import VPNUsers
from panel import get_panel
from keyboards import get_buy_more_traffic_keyboard
from utils.ephemeral import EphemeralNotification
from utils.lang import get_i18n_string

TRAFFIC_THRESHOLD = 0.75
NOTIFICATION_COOLDOWN_HOURS = 24

async def check_users_traffic(bot: Bot):
    logging.info("Starting traffic check for all active users")
    
    panel = get_panel()
    users = await get_all_active_users()
    
    logging.info(f"Found {len(users)} active users")
    if users:
        logging.info(f"First user type: {type(users[0])}, value: {users[0]}")
        logging.info(f"First user attributes: {dir(users[0])}")
        if hasattr(users[0], '_mapping'):
            logging.info(f"First user _mapping: {users[0]._mapping}")
    
    notification_count = 0
    error_count = 0
    
    for user_row in users:
        try:
            # Extract model from Row object
            # In SQLAlchemy 2.0, Row objects can be accessed via index or _mapping
            if hasattr(user_row, '_mapping'):
                user = user_row._mapping.get(VPNUsers) or user_row._mapping.get('VPNUsers')
            elif hasattr(user_row, '__getitem__'):
                # Try to get model by index - might be at different positions
                user = None
                for i in range(len(user_row)):
                    item = user_row[i]
                    if hasattr(item, 'tg_id'):
                        user = item
                        break
                if user is None:
                    user = user_row[0] if len(user_row) > 0 else user_row
            else:
                user = user_row
            
            if not hasattr(user, 'tg_id'):
                logging.warning(f"User object has no tg_id attribute. Type: {type(user)}, Value: {user}")
                continue
            
            panel_profile = await panel.get_panel_user(user.tg_id)
            
            if not panel_profile or not panel_profile.data_limit:
                logging.debug(f"User {user.tg_id}: no profile or data_limit")
                continue
            
            traffic_usage = panel_profile.used_traffic / panel_profile.data_limit
            logging.info(f"User {user.tg_id}: traffic usage {traffic_usage*100:.1f}% ({panel_profile.used_traffic}/{panel_profile.data_limit})")
            
            if traffic_usage > TRAFFIC_THRESHOLD:
                last_notification = await get_last_traffic_notification(user.tg_id, "traffic_75_percent")
                
                if last_notification:
                    last_sent = last_notification[0].sent_at
                    time_since_last = datetime.now() - last_sent
                    
                    if time_since_last < timedelta(hours=NOTIFICATION_COOLDOWN_HOURS):
                        continue
                
                try:
                    chat_member = await bot.get_chat_member(user.tg_id, user.tg_id)
                    if not chat_member:
                        continue
                    
                    remaining_percent = int((1 - traffic_usage) * 100)
                    message = get_i18n_string("message_reached_usage_percent", chat_member.user.language_code).format(
                        name=chat_member.user.first_name,
                        amount=remaining_percent
                    )
                    keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)
                    
                    await EphemeralNotification.send_ephemeral(
                        bot=bot,
                        chat_id=user.tg_id,
                        text=message,
                        reply_markup=keyboard,
                        lang=chat_member.user.language_code
                    )
                    
                    await add_traffic_notification(user.tg_id, "traffic_75_percent")
                    notification_count += 1
                    logging.info(f"Sent traffic notification to user {user.tg_id} (usage: {traffic_usage*100:.1f}%)")
                    
                except Exception as e:
                    logging.warning(f"Failed to send traffic notification to user {user.tg_id}: {e}")
                    error_count += 1
                    
        except Exception as e:
            logging.debug(f"Error checking traffic for user {user.tg_id}: {e}")
            error_count += 1
    
    logging.info(f"Traffic check completed. Sent: {notification_count}, Errors: {error_count}")
