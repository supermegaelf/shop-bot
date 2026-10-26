from datetime import datetime, UTC

MONTHS_RU = {
    1: "янв", 2: "фев", 3: "мар", 4: "апр",
    5: "мая", 6: "июн", 7: "июл", 8: "авг",
    9: "сен", 10: "окт", 11: "ноя", 12: "дек"
}

MONTHS_EN = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}

MONTHS_RU_GENITIVE = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}

MONTHS_EN_FULL = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


def next_traffic_reset(expire: datetime | None) -> datetime | None:
    now = datetime.now(UTC)
    next_reset = datetime(now.year + now.month // 12, now.month % 12 + 1, 1, tzinfo=UTC)
    if expire and expire < next_reset:
        return None
    return next_reset
