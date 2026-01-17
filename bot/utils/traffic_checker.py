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
    
    notification_count = 0
    error_count = 0
    
    for user_row in users:
        try:
            # Extract tg_id from Row object
            # In SQLAlchemy 2.0, Row objects have _mapping dict with column values
            if hasattr(user_row, '_mapping'):
                tg_id = user_row._mapping.get('tg_id')
            elif hasattr(user_row, '__getitem__'):
                # Row tuple: (id, tg_id, vpn_id, test)
                tg_id = user_row[1] if len(user_row) > 1 else None
            elif hasattr(user_row, 'tg_id'):
                # Already a model object
                tg_id = user_row.tg_id
            else:
                logging.warning(f"Cannot extract tg_id from user_row. Type: {type(user_row)}, Value: {user_row}")
                continue
            
            if tg_id is None:
                logging.warning(f"tg_id is None for user_row: {user_row}")
                continue
            
            panel_profile = await panel.get_panel_user(tg_id)
            
            if not panel_profile or not panel_profile.data_limit:
                logging.debug(f"User {tg_id}: no profile or data_limit")
                continue
            
            # Validate data to prevent division by zero and negative values
            if panel_profile.data_limit <= 0:
                logging.warning(f"User {tg_id}: invalid data_limit: {panel_profile.data_limit}")
                continue
            
            if panel_profile.used_traffic < 0:
                logging.warning(f"User {tg_id}: negative used_traffic: {panel_profile.used_traffic}")
                continue
            
            traffic_usage = panel_profile.used_traffic / panel_profile.data_limit
            logging.info(f"User {tg_id}: traffic usage {traffic_usage*100:.1f}% ({panel_profile.used_traffic}/{panel_profile.data_limit})")
            
            if traffic_usage > TRAFFIC_THRESHOLD:
                last_notification = await get_last_traffic_notification(tg_id, "traffic_75_percent")
                
                if last_notification:
                    last_sent = last_notification[0].sent_at
                    time_since_last = datetime.now() - last_sent
                    
                    if time_since_last < timedelta(hours=NOTIFICATION_COOLDOWN_HOURS):
                        continue
                
                try:
                    chat_member = await bot.get_chat_member(tg_id, tg_id)
                    if not chat_member:
                        continue
                    
                    # Always show 25% remaining when threshold (75%) is exceeded
                    remaining_percent = 25
                    message = get_i18n_string("message_reached_usage_percent", chat_member.user.language_code).format(
                        name=chat_member.user.first_name,
                        amount=remaining_percent
                    )
                    keyboard = get_buy_more_traffic_keyboard(chat_member.user.language_code, back=False, from_notification=True)
                    
                    await EphemeralNotification.send_ephemeral(
                        bot=bot,
                        chat_id=tg_id,
                        text=message,
                        reply_markup=keyboard,
                        lang=chat_member.user.language_code
                    )
                    
                    await add_traffic_notification(tg_id, "traffic_75_percent")
                    notification_count += 1
                    logging.info(f"Sent traffic notification to user {tg_id} (usage: {traffic_usage*100:.1f}%)")
                    
                except Exception as e:
                    logging.warning(f"Failed to send traffic notification to user {tg_id}: {e}")
                    error_count += 1
                    
        except Exception as e:
            logging.debug(f"Error checking traffic for user {tg_id if 'tg_id' in locals() else 'unknown'}: {e}")
            error_count += 1
    
    logging.info(f"Traffic check completed. Sent: {notification_count}, Errors: {error_count}")
