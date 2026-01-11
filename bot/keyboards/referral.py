from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.lang import get_i18n_string

def get_referral_menu_keyboard(lang: str = 'ru', referral_link: str = '') -> InlineKeyboardMarkup:
    share_text = get_i18n_string("referral_share_button", lang)
    back_text = get_i18n_string("button_back", lang)
    
    share_message = get_i18n_string("referral_inline_message", lang).format(referral_link=referral_link)
    
    keyboard = [
        [InlineKeyboardButton(text=share_text, switch_inline_query=share_message)],
        [InlineKeyboardButton(text=back_text, callback_data="back_to_profile")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_referral_notification_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    referral_text = get_i18n_string("main_menu_referral", lang)
    dismiss_text = get_i18n_string("button_dismiss", lang)
    
    keyboard = [
        [InlineKeyboardButton(text=referral_text, callback_data="referral_menu")],
        [InlineKeyboardButton(text=dismiss_text, callback_data="dismiss_notification")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_referral_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    stats_text = get_i18n_string("button_referral_stats", lang)
    list_text = get_i18n_string("button_referral_list", lang)
    back_text = get_i18n_string("button_back", lang)
    
    keyboard = [
        [InlineKeyboardButton(text=stats_text, callback_data="admin_referral_stats")],
        [InlineKeyboardButton(text=list_text, callback_data="admin_referral_list")],
        [InlineKeyboardButton(text=back_text, callback_data="admin_management")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_referral_stats_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    back_text = get_i18n_string("button_back", lang)
    
    keyboard = [
        [InlineKeyboardButton(text=back_text, callback_data="admin_referrals")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_referral_list_keyboard(page: int, total_pages: int, lang: str = 'ru', has_referrers: bool = True) -> InlineKeyboardMarkup:
    search_text = get_i18n_string("button_referral_search", lang)
    back_text = get_i18n_string("button_back", lang)
    
    keyboard = []
    
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton(text="⏪", callback_data=f"admin_referral_page_{page-1}"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton(text="⏩", callback_data=f"admin_referral_page_{page+1}"))
        
        if nav_row:
            keyboard.append(nav_row)
    
    if has_referrers:
        keyboard.append([InlineKeyboardButton(text=search_text, callback_data="admin_referral_search")])
    
    keyboard.append([InlineKeyboardButton(text=back_text, callback_data="admin_referrals")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_referral_user_keyboard(user_id: int, page: int, total_pages: int, lang: str = 'ru') -> InlineKeyboardMarkup:
    back_text = get_i18n_string("button_back", lang)
    
    keyboard = []
    
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"admin_referral_user_{user_id}_page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"admin_referral_user_{user_id}_page_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton(text=back_text, callback_data="admin_referral_list")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_referral_search_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    back_text = get_i18n_string("button_back", lang)
    
    keyboard = [
        [InlineKeyboardButton(text=back_text, callback_data="admin_referral_list")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
