import logging

import glv


async def notify_admins_payment_failure(tg_id: int, callback: str, payment_id: str, provisioned: bool, error: Exception):
    text = (
        "⚠️ Сбой обработки оплаты\n\n"
        f"Пользователь: {tg_id}\n"
        f"Товар: {callback}\n"
        f"Платёж: {payment_id}\n"
        f"Выдано в панели: {'да' if provisioned else 'нет'}\n"
        f"Ошибка: {type(error).__name__}: {str(error)[:500]}"
    )
    for admin_id in glv.config['ADMINS']:
        try:
            await glv.bot.send_message(admin_id, text, parse_mode=None)
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id} about payment failure: {e}")
