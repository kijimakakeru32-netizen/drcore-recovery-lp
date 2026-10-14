"""Shared Recovery campaign, price and trainer sections for the static build."""
import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent


def escape(value):
    return html.escape(str(value), quote=True)


def read_data(name):
    return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))


def trial_cta(position, href='#trial'):
    offer = read_data('recovery-offer.json')
    external = ' target="_blank" rel="noopener" data-reservation' if href.startswith('https://') else ''
    return f'''<a class="cta-fixed" href="{escape(href)}"{external} data-position="{escape(position)}"><span class="cta-fixed__inner"><span class="cta-fixed__top"><span class="cta-fixed__duration">初回<strong>{offer['trial_minutes']}</strong>分</span><time datetime="{escape(offer['deadline'])}">{escape(offer['deadline_label'])}</time><span class="cta-fixed__price"><b>{offer['trial_price']:,}</b><span>円</span></span></span><span class="cta-fixed__main">{escape(offer['button_label'])}<i class="cta-fixed__arrow" aria-hidden="true">→</i></span></span></a>'''


def trial_banner(position, href='#trial', hero=False):
    offer = read_data('recovery-offer.json')
    classes = f'campaign-banner campaign-banner--{escape(position)}'
    if hero:
        classes += ' hero-trial'
    return f'''<div class="{classes}"><div class="wrap campaign-banner-inner"><p class="campaign-banner-description">{escape(offer['included'])}</p>{trial_cta(position, href)}</div></div>'''


def render_pricing():
    data = read_data('recovery-plans.json')
    groups = [
        (1, '平日10:00〜15:00でご利用の場合', 0),
        (2, '平日（上記以外）＆土日祝でご利用の場合', data['other_hours_surcharge']),
    ]
    blocks = []
    for number, condition, surcharge in groups:
        rows = []
        for plan in data['plans']:
            per_session = plan['per_session'] + surcharge
            monthly = plan['sessions'] * per_session
            rows.append(f'''<tr data-sessions="{plan['sessions']}" data-monthly="{monthly}" data-per-session="{per_session}"><th scope="row"><span>{escape(plan['name'])}</span><small>月{plan['sessions']}回</small></th><td><strong>{monthly:,}</strong><span>円</span></td><td><b>{per_session:,}</b><span>円</span></td></tr>''')
        blocks.append(f'''<article class="rate-plan rate-plan--{number}" data-rate-plan="{number}" aria-labelledby="rate-plan-{number}"><h3 id="rate-plan-{number}"><span class="rate-plan-label">プラン{number}：</span><span class="rate-plan-condition">{escape(condition)}</span></h3><div class="price-table-wrap"><table class="price-table"><caption class="visually-hidden">プラン{number}：{escape(condition)}の月額・1回あたり料金</caption><thead><tr><th scope="col">プラン</th><th scope="col">月額料金</th><th scope="col">1回あたり</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></article>''')
    return '<div class="rate-plans">' + ''.join(blocks) + '</div>'


def render_trainers():
    cards = []
    for trainer in read_data('trainers.json'):
        image = f'''<img src="./{escape(trainer['photo'])}" alt="{escape(trainer['label'])}" width="{trainer['width']}" height="{trainer['height']}" loading="lazy" decoding="async" style="object-position:{escape(trainer['object_position'])}">'''
        cards.append(f'''<article class="trainer-card" data-trainer-id="{escape(trainer['id'])}"><figure>{image}</figure><h3><span>{escape(trainer['surname'])}</span><span>トレーナー</span></h3></article>''')
    return '<div class="trainer-grid">' + ''.join(cards) + '</div>'


def load_stores():
    """Maintain the two Recovery pages and their links from one source."""
    stores = read_data('recovery-stores.json')
    slugs = set()
    for store in stores:
        slug = store['slug']
        if not slug or any(character not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for character in slug) or slug in slugs:
            raise ValueError(f'Invalid or duplicate Recovery store slug: {slug!r}')
        slugs.add(slug)
        if not store['reserve'].startswith('https://reserve.quick-reserve.com/'):
            raise ValueError(f'{slug}: use the approved HTTPS booking URL')
        image = (ROOT / 'dist' / store['photo']).resolve()
        if not image.is_relative_to((ROOT / 'dist/assets').resolve()) or not image.is_file():
            raise ValueError(f'{slug}: local store photo is missing')
    return stores


def render_store_cards(stores, site_prefix='./', current_store=None):
    cards = []
    for store in stores:
        current = bool(current_store and store['slug'] == current_store['slug'])
        href = '#access' if current else f"{site_prefix}gyms/{store['slug']}/"
        detail = 'この店舗のアクセスを見る' if current else '店舗の詳細・体験予約'
        cards.append(f'''<a class="studio studio-link" href="{escape(href)}" data-store-link="{escape(store['name'])}"><img src="./{escape(store['photo'])}" alt="Dr.core{escape(store['name'])}の店内" width="{store['photo_width']}" height="{store['photo_height']}" loading="lazy" decoding="async"><div class="studio-body"><div class="studio-title"><h3>{escape(store['name'])}</h3><p>{escape(store['station'])} 徒歩<strong>{escape(store['minutes'])}</strong>分</p></div><p class="studio-address">{escape(store['address'])}<br>{escape(store['building'])}</p><span class="studio-detail-link">{detail}<span aria-hidden="true">→</span></span></div></a>''')
    return '<div class="studio-grid">' + ''.join(cards) + '</div>'


def render_store_access(store):
    if not store:
        return ''
    query = quote(store['address'] + ' ' + store['building'])
    map_url = 'https://www.google.com/maps/search/?api=1&query=' + query
    return f'''<section class="section recovery-store-access" id="access" aria-labelledby="access-title"><div class="wrap"><div class="center-heading"><p class="section-eyebrow">ACCESS / {escape(store['en'])}</p><h2 id="access-title"><span>Dr.core Recovery {escape(store['name'])}</span><span>店舗情報・アクセス</span></h2></div><div class="recovery-access-grid"><figure class="recovery-access-photo"><img src="./{escape(store['photo'])}" alt="Dr.core{escape(store['name'])}の店内" width="{store['photo_width']}" height="{store['photo_height']}" loading="lazy" decoding="async"></figure><div class="recovery-access-content"><dl><div><dt>店舗名</dt><dd>Dr.core Recovery {escape(store['name'])}<small>自重ストレッチ／完全予約制</small></dd></div><div><dt>住所</dt><dd>{escape(store['address'])}<br>{escape(store['building'])}</dd></div><div><dt>アクセス</dt><dd>{escape(store['access'])}<small>{escape(store['access_sub'])}</small></dd></div></dl><a class="recovery-map-link" href="{escape(map_url)}" target="_blank" rel="noopener">Google マップで開く<span aria-hidden="true">↗</span></a><a class="recovery-page-top" href="#top">このページの先頭へ<span aria-hidden="true">↑</span></a></div></div></div></section>'''


def render_booking_content(markup, store=None):
    if store:
        visit_photo = f'''<img src="./{escape(store['photo'])}" alt="Dr.core{escape(store['name'])}の店内" width="{store['photo_width']}" height="{store['photo_height']}" loading="lazy" decoding="async">'''
        booking_copy = 'ページ内の「初回体験予約」から、Web予約にお進みください。'
        booking_link = f'''<a class="text-link" href="{escape(store['reserve'])}" target="_blank" rel="noopener" data-reservation>初回体験予約 <span aria-hidden="true">→</span></a>'''
        visit_copy = f"ご予約の日時に、{escape(store['name'])}へお越しください。店舗の場所や駅からのアクセスは、店舗情報をご確認ください。"
        visit_link = '<a class="text-link" href="#access">店舗情報を見る <span aria-hidden="true">→</span></a>'
        faq_booking = 'このページの「初回体験予約」ボタンから、Web予約にお進みください。'
    else:
        first = load_stores()[0]
        visit_photo = f'''<img src="./{escape(first['photo'])}" alt="Dr.core{escape(first['name'])}の店内" width="{first['photo_width']}" height="{first['photo_height']}" loading="lazy" decoding="async">'''
        booking_copy = '店舗を選び、店舗ページの「初回体験予約」からWeb予約にお進みください。'
        booking_link = '<a class="text-link" href="#locations">店舗を選ぶ <span aria-hidden="true">→</span></a>'
        visit_copy = 'ご予約の日時に、選んだ店舗へお越しください。月島店・本八幡店の場所は、店舗一覧からご確認いただけます。'
        visit_link = '<a class="text-link" href="#locations">店舗一覧を見る <span aria-hidden="true">→</span></a>'
        faq_booking = '<a href="#locations">店舗一覧</a>から店舗を選び、店舗ページの「初回体験予約」からWeb予約にお進みください。'
    for marker, value in {
        '{{RESERVATION_FLOW_COPY}}': booking_copy,
        '{{RESERVATION_FLOW_LINK}}': booking_link,
        '{{STORE_VISIT_PHOTO}}': visit_photo,
        '{{STORE_VISIT_COPY}}': visit_copy,
        '{{STORE_VISIT_LINK}}': visit_link,
        '{{RESERVATION_FAQ}}': faq_booking,
    }.items():
        markup = markup.replace(marker, value)
    return markup


def render_sections(source, store=None):
    destination = store['reserve'] if store else '#locations'
    replacements = {
        '{{CTA_HERO}}': trial_banner('hero', destination, hero=True),
        '{{CTA_INTRO}}': trial_banner('intro', destination),
        '{{CTA_PRICE}}': trial_banner('price', destination),
        '{{CTA_BOTTOM}}': trial_banner('bottom', destination),
        '{{CTA_STICKY}}': trial_banner('sticky', destination),
        '{{RATE_PLANS}}': render_pricing(),
        '{{TRAINER_CARDS}}': render_trainers(),
        '{{RECOVERY_FLOW}}': render_booking_content((ROOT / 'templates/partials/recovery-flow.html').read_text(encoding='utf-8'), store),
        '{{RECOVERY_FAQ}}': render_booking_content((ROOT / 'templates/partials/recovery-faq.html').read_text(encoding='utf-8'), store),
    }
    for marker, markup in replacements.items():
        source = source.replace(marker, markup)
    return source
