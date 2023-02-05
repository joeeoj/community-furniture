import hashlib
from typing import Optional
import re

import bs4
import requests


URL = 'https://communityfurniture.org'
PRODUCT_TYPES = [
    'all',
    'sofa',
    'chair',
    'table',
    'home-decor',
    'movein-essentials',
]


def hashstr(s: str) -> str:
    m = hashlib.md5()
    m.update(bytearray(s, encoding='utf8'))
    return m.hexdigest()


def parse_price(price_str: str) -> Optional[float]:
    price = re.search(r'\$\d+\.\d+', price_str)

    if price:
        return float(price.group().replace("$", ""))
    return None


def parse_items(soup: bs4.BeautifulSoup) -> list[dict]:
    results = []
    items = soup.find_all('div', {'class': 'summary-item'})

    for item in items:
        link = item.find('a')
        href = link.attrs.get('href')

        product_mark = item.find('div', {'class': 'product-mark'})
        sold = True if product_mark and product_mark.text.strip().lower() == 'sold' else False

        price_div = item.find('div', {'class': 'product-price'})
        price = 0 if not price_div else parse_price(price_div.text)

        results.append({
            'id': hashstr(href),
            'title': link.attrs.get('data-title'),
            'url': URL + href,
            'sold': sold,
            'price': price,
        })
    return results


# if __name__ == '__main__':
r = requests.get(f'{URL}/sofa')
soup = bs4.BeautifulSoup(r.content, 'html.parser')
results = parse_items(soup)

