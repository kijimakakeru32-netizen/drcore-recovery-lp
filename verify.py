#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check the three entrypoints, production copy, assets and reservation targets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import re
from build import STORES

ROOT = Path(__file__).resolve().parent / 'dist'

class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.assets, self.reservations = [], [], [], []
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'a':
            self.links.append(a.get('href', ''))
            if 'data-reservation' in a:
                self.reservations.append(a['href'])
        if tag in ['img', 'script', 'link']:
            ref = a.get('src', a.get('href', ''))
            if ref and not urlparse(ref).scheme:
                self.assets.append(urlparse(ref).path)

prices = []
pages = list(ROOT.rglob('index.html'))
assert len(pages) == 3
for file in pages:
    source = file.read_text()
    scan = Scan()
    scan.feed(source)
    assert not re.search(r'プレオープン|先行登録|PRE.?OPEN|オープン予定|開業準備|内装工事|data-open-form|U18|3169', source, re.I), file
    assert scan.h1 == 1 and len(scan.ids) == len(set(scan.ids)), file
    assert all((file.parent / asset).exists() for asset in scan.assets), file
    for link in scan.links:
        parsed = urlparse(link)
        if parsed.scheme:
            continue
        dest = (file.parent / unquote(parsed.path)).resolve() if parsed.path else file
        if dest.is_dir():
            dest /= 'index.html'
        assert dest.exists(), (file, link)
        if parsed.fragment:
            other = Scan()
            other.feed(dest.read_text())
            assert parsed.fragment in other.ids, (file, link)
    if 'gyms' in file.parts:
        expected = STORES[file.parent.name]['reserve']
        assert len(scan.reservations) == 6
        assert all(url == expected for url in scan.reservations), file
        access = re.search(r'<section[^>]*id="access".*?</section>', source, re.S).group()
        assert STORES[file.parent.name]['address'] in access
        other_slug = next(slug for slug in STORES if slug != file.parent.name)
        assert STORES[other_slug]['name'] not in access
    else:
        assert not scan.reservations
        assert 'id="access"' not in source
    price = re.search(r'<section[^>]*id="price".*?</section>', source, re.S).group()
    prices.append(re.findall(r'¥[\d,]+', price))
    print(f'{file.relative_to(ROOT)}: OK — {len(scan.links)} links, {len(scan.reservations)} reservation links')
assert all(values == prices[0] for values in prices)
assert {'¥1,000', '¥14,000', '¥24,000', '¥46,000', '¥88,000', '¥21,000', '¥40,000', '¥76,000', '¥33,000', '¥0'}.issubset(prices[0])
print('All three pages, shared prices, assets and reservation links passed.')
