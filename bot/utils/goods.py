import json

def get(callback=None) -> list | dict:
    with open("goods.json") as file:
        data = json.load(file)
    if callback is None:
        return data
    for v in data:
        if v['callback'] == callback:
            return v
    return dict()

def get_callbacks() -> list:
    with open("goods.json") as file:
        data = json.load(file)
    res = [x['callback'] for x in data]
    return res

UPGRADE_PREFIX = "upgrade_"

def get_current_tariff(callbacks: list) -> dict:
    for cb in callbacks:
        target = cb[len(UPGRADE_PREFIX):] if cb.startswith(UPGRADE_PREFIX) else cb
        good = get(target)
        if good and good.get("type") == "renew":
            return good
    return dict()

def get_upgrade_options(current: dict) -> list:
    if not current:
        return []
    options = [
        good for good in get()
        if good.get("type") == "renew"
        and good["months"] == current["months"]
        and good["data_limit"] > current["data_limit"]
    ]
    return sorted(options, key=lambda good: good["data_limit"])

def get_upgrade_price(current: dict, target: dict, currency: str):
    return target["price"][currency] - current["price"][currency]