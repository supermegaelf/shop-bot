import logging

import httpx

import glv


def describe_error(error: Exception) -> str:
    text = f"{type(error).__name__}: {str(error)[:500]}"
    if isinstance(error, httpx.HTTPStatusError):
        text += f" | response: {error.response.text[:500]}"
    return text


async def notify_admins_payment_failure(tg_id: int, callback: str, payment_id: str, provisioned: bool, error: Exception):
    text = (
        "⚠️ Сбой обработки оплаты\n\n"
        f"Пользователь: {tg_id}\n"
        f"Товар: {callback}\n"
        f"Платёж: {payment_id}\n"
        f"Выдано в панели: {'да' if provisioned else 'нет'}\n"
        f"Ошибка: {describe_error(error)}"
    )
    for admin_id in glv.config['ADMINS']:
        try:
            await glv.bot.send_message(admin_id, text, parse_mode=None)
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id} about payment failure: {e}")
