import datetime
import hashlib
import pathlib
from typing import Optional
import re
import sqlite3
import time

import bs4
import requests

from config import TOKEN, USER_TOKEN


URL = 'https://communityfurniture.org'
PRODUCT_TYPES = [
    'sofa',
    'chair',
    'table',
    'home-decor',
]
DATABASE_PATH = pathlib.Path.cwd() / 'items.db'
SCHEMA_PATH = pathlib.Path.cwd() / 'schema.sql'


def send_alert(title: str, price: float, url: str):
    params = {
        'token': TOKEN,
        'user': USER_TOKEN,
        'message': f'{title} for ${price}',
        'url': url,
    }
    requests.post('https://api.pushover.net/1/messages.json', params)


def init_schema(conn: sqlite3.Connection, schema_path: pathlib.Path) -> None:
    with open(schema_path) as f:
        query = f.read()
    conn.executescript(query)


def insert_records(results: list[dict], conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    header = results[0].keys()
    cols = ','.join(list(header))
    placeholder = ','.join(['?'] * len(header))
    query = f"INSERT OR IGNORE INTO items ({cols}) VALUES ({placeholder})"

    cursor.executemany(query, [tuple(d.values()) for d in results])
    conn.commit()


def update_alert_sent(conn: sqlite3.Connection, schema_path: pathlib.Path, dt_str: str, item_id: str) -> None:
    cursor.execute('UPDATE items SET alert_sent_dt = ? WHERE item_id = ?', (dt_str, item_id))
    conn.commit()


def hashstr(s: str) -> str:
    """Hash input string into fixed 32-length string with MD5"""
    m = hashlib.md5()
    m.update(bytearray(s, encoding='utf8'))
    return m.hexdigest()


def parse_price(price_div: bs4.Tag) -> Optional[float]:
    """Parse the first seen price in a string into float"""
    if not price_div:
        return None

    price = re.search(r'\$\d+\.\d+', price_div.text)

    if price:
        return float(price.group().replace("$", ""))
    return None


def url_to_soup(url: str) -> bs4.BeautifulSoup:
    """Request given url and return bs4 soup object"""
    r = requests.get(url)
    return bs4.BeautifulSoup(r.content, 'html.parser')


def parse_items(soup: bs4.BeautifulSoup, product_type: str) -> list[dict]:
    """Parse items on the community furniture page into a list of dicts"""
    results = []
    items = soup.find_all('div', {'class': 'summary-item'})

    for item in items:
        link = item.find('a')
        href = link.attrs.get('href')

        product_mark = item.find('div', {'class': 'product-mark'})
        sold = product_mark is not None and product_mark.text.strip().lower() == 'sold'

        price_div = item.find('div', {'class': 'product-price'})
        price = parse_price(price_div)

        results.append({
            'item_id': hashstr(href),
            'product_type': product_type,
            'title': link.attrs.get('data-title'),
            'sold': sold,
            'price': price,
            'url': URL + href,
        })
    return results


def main():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    init_schema(conn, SCHEMA_PATH)

    for product_type in PRODUCT_TYPES:
        url = f'{URL}/{product_type}'
        soup = url_to_soup(url)
        results = parse_items(soup, product_type)
        insert_records(results, conn, cursor)

    never_seen_sofas = cursor.execute('SELECT item_id, title, price, url FROM never_seen_sofas').fetchall()
    for sofa in never_seen_sofas:
        item_id, title, price, url = sofa
        send_alert(title, price, url)

        now = datetime.datetime.now().isoformat()
        update_alert_sent(conn, cursor, now, item_id)

        time.sleep(10)

    conn.close()


if __name__ == '__main__':
    main()
