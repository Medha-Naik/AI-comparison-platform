import os
import json
from datetime import datetime
from threading import Lock


_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
_HISTORY_PATH = os.path.join(_DATA_DIR, 'price_history.json')
_lock = Lock()


def _ensure_store_file():
    if not os.path.isdir(_DATA_DIR):
        os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.isfile(_HISTORY_PATH):
        with open(_HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump({}, f)


def _load_all() -> dict:
    _ensure_store_file()
    with open(_HISTORY_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save_all(data: dict) -> None:
    tmp_path = _HISTORY_PATH + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, _HISTORY_PATH)


def generate_offer_key(offer: dict) -> str:
    """
    Create a stable key for an offer combining store and a stable identifier.
    Preference order: url, title.
    """
    store = (offer.get('store') or '').strip().lower()
    url = (offer.get('url') or '').strip()
    title = (offer.get('title') or '').strip().lower()
    base = url if url else title
    return f"{store}|{base}"


def record_price(offer: dict, price: int) -> str:
    """
    Record today's price for the offer. Returns the offer key used.
    If a record for today already exists with the same price, do nothing.
    """
    key = generate_offer_key(offer)
    if not key or price is None:
        return key

    today = datetime.utcnow().strftime('%Y-%m-%d')

    with _lock:
        data = _load_all()
        history = data.get(key, [])

        if history and history[-1].get('date') == today:
            # Update same-day entry if price differs
            if history[-1].get('price') != price:
                history[-1]['price'] = price
        else:
            history.append({'date': today, 'price': price})

        data[key] = history
        _save_all(data)

    return key


def get_history(key: str) -> list:
    if not key:
        return []
    with _lock:
        data = _load_all()
        return data.get(key, [])


