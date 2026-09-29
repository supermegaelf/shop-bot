import logging

import httpx

import glv


def describe_error(error: Exception) -> str:
    text = f"{type(error).__name__}: {str(error)[:500]}"
    if isinstance(error, httpx.HTTPStatusError):
        text += f" | response: {error.response.text[:500]}"
    return text


async def _send_to_admins(text: str):
    for admin_id in glv.config['ADMINS']:
        try:
            await glv.bot.send_message(admin_id, text, parse_mode=None)
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")


async def notify_admins_payment_failure(tg_id: int, callback: str, payment_id: str, provisioned: bool, error: Exception):
    text = (
        "⚠️ Сбой обработки оплаты\n\n"
        f"Пользователь: {tg_id}\n"
        f"Товар: {callback}\n"
        f"Платёж: {payment_id}\n"
        f"Выдано в панели: {'да' if provisioned else 'нет'}\n"
        f"Ошибка: {describe_error(error)}"
    )
    await _send_to_admins(text)


async def notify_admins_referral_failure(referee_id: int, payment_id, failures: list):
    text = (
        "⚠️ Сбой начисления реферального бонуса\n\n"
        f"Приглашённый: {referee_id}\n"
        f"Платёж (строка в БД): {payment_id}\n\n"
        + "\n".join(failures)
    )
    await _send_to_admins(text)
