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


def reservation_url(store=None):
    return store['reserve'] if store else read_data('recovery-offer.json')['reserve']


def trial_cta(position, href='#trial'):
    offer = read_data('recovery-offer.json')
    external = ' target="_blank" rel="noopener" data-reservation' if href.startswith('https://') else ''
    top = f'''<span class="cta-fixed__top"><time datetime="{escape(offer['deadline'])}">{escape(offer['deadline_label'])}</time><span class="cta-fixed__duration">初回<strong>{offer['trial_minutes']}</strong>分</span><span class="cta-fixed__price"><b>{offer['trial_price']:,}</b><span>円</span></span></span>''' if position == 'sticky' else ''
    return f'''<a class="cta-fixed" href="{escape(href)}"{external} data-position="{escape(position)}"><span class="cta-fixed__inner">{top}<span class="cta-fixed__main">{escape(offer['button_label'])}<i class="cta-fixed__arrow" aria-hidden="true">&#9656;</i></span></span></a>'''


def campaign_icon(kind):
    drawings = {
        'assessment': '<rect x="9" y="7" width="22" height="28" rx="2"/><path d="M16 7V4h8v3M15 15h10M15 21h10M15 27h7"/>',
        'stretch': '<circle cx="24" cy="7" r="3"/><path d="m21 14-6 8-7 6m13-14 7 6 5-1m-13-2 2 10 6 9m-6-9-9 8"/>',
        'plan': '<path d="M6 35h29M10 29V20h5v9M20 29V14h5v15M30 29V6h5v23"/>',
    }
    return '<svg viewBox="0 0 42 42" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + drawings[kind] + '</svg>'


def campaign_laurel():
    return '''<svg class="campaign-laurel" viewBox="0 0 36 80" fill="currentColor" aria-hidden="true"><path d="M27 76C8 56 8 30 25 6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M24 11c-9-2-12 5-9 11 7-1 11-5 9-11M17 24C7 23 5 30 10 36c6-2 10-6 7-12M12 39C2 40 2 48 8 52c6-3 8-9 4-13M13 55C4 59 7 67 14 68c5-5 5-10-1-13M25 17c8 1 8 9 2 13-5-3-6-8-2-13M20 32c9 2 8 10 1 13-5-4-5-9-1-13M20 49c9 2 9 9 2 13-5-3-6-8-2-13M25 65c9-1 12 5 9 11-6 1-10-3-9-11"/></svg>'''


def trial_banner(position, href='#trial'):
    offer = read_data('recovery-offer.json')
    classes = f'campaign-banner campaign-banner--{escape(position)}'
    description = f'<p class="campaign-banner-description">{escape(offer["included"])}</p>'
    web_note = escape(offer['web_note']).replace('WEB予約', 'WEB予約<br>', 1)
    if position == 'sticky':
        return f'''<div class="{classes}"><div class="wrap campaign-banner-inner">{description}{trial_cta(position, href)}</div></div>'''
    steps = []
    for step in offer['experience']:
        label = escape(step['label']).replace('＆', '＆<br>')
        steps.append(f'''<li data-trial-step="{escape(step['id'])}" data-minutes="{step['minutes']}"><span class="campaign-step-icon">{campaign_icon(step['icon'])}</span><span class="campaign-step-label">{label}</span><span class="campaign-step-minutes"><strong>{step['minutes']}</strong>分</span></li>''')
    return f'''<div class="{classes}"><div class="wrap campaign-banner-inner"><div class="campaign-creative"><p class="campaign-headline">あなたの柔軟性に合わせて、<span>マンツーマン。</span></p><div class="campaign-offer">{campaign_laurel()}<time datetime="{escape(offer['deadline'])}">{escape(offer['deadline_label'])}</time><p class="campaign-offer-price"><span>初回</span><strong>{offer['trial_price']:,}</strong><span>円</span><span class="campaign-offer-caption">キャンペーン実施中</span></p>{campaign_laurel()}</div><div class="campaign-content"><figure class="campaign-photo"><picture><source media="(max-width:560px)" srcset="./assets/recovery-hero-portrait.jpg"><img src="./assets/recovery-first-visit-plan.png" alt="トレーナーに支えてもらい、TRXで身体を伸ばす女性" width="958" height="737" loading="lazy" decoding="async"></picture><figcaption class="campaign-duration"><span>まずは体験！</span><strong>{offer['trial_minutes']}<small>分</small></strong></figcaption></figure><div class="campaign-experience"><h3>体験内容</h3><ol class="campaign-steps">{''.join(steps)}</ol>{description}</div></div><div class="campaign-action"><span class="campaign-web-note">{web_note}</span>{trial_cta(position, href)}</div></div></div></div>'''


def render_pricing():
    data = read_data('recovery-plans.json')
    groups = [
        (1, '平日デイタイムプラン', '平日10:00〜15:00', 0, 'daytime_price'),
        (2, 'レギュラープラン', '全営業時間（平日・土日祝）', data['other_hours_surcharge'], 'regular_price'),
    ]
    blocks = []
    for number, name, condition, surcharge, payg_field in groups:
        payg_price = data['pay_as_you_go'][payg_field]
        if type(payg_price) is not int or payg_price <= 0:
            raise ValueError(f'Invalid pay-as-you-go {payg_field}')
        rows = [f'''<tr data-payment="pay-as-you-go" data-per-session="{payg_price}"><th scope="row"><span>都度払い</span></th><td><span aria-label="月額料金なし">-</span></td><td><b>{payg_price:,}</b><span>円</span></td></tr>''']
        for plan in data['plans']:
            per_session = plan['per_session'] + surcharge
            monthly = plan['sessions'] * per_session
            rows.append(f'''<tr data-sessions="{plan['sessions']}" data-monthly="{monthly}" data-per-session="{per_session}"><th scope="row"><span>{escape(plan['name'])}</span></th><td><strong>{monthly:,}</strong><span>円</span></td><td><b>{per_session:,}</b><span>円</span></td></tr>''')
        blocks.append(f'''<article class="rate-plan rate-plan--{number}" data-rate-plan="{number}" aria-labelledby="rate-plan-{number}"><h3 id="rate-plan-{number}"><span class="rate-plan-label">{escape(name)}</span><span class="rate-plan-condition">{escape(condition)}</span></h3><div class="price-table-wrap"><table class="price-table"><caption class="visually-hidden">{escape(name)}：{escape(condition)}の月額・1回あたり（30分）の料金</caption><thead><tr><th scope="col">プラン</th><th scope="col">月額料金</th><th scope="col">1回あたり<span class="phrase-keep">（30分）</span></th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></article>''')
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
    return f'''<section class="section recovery-store-access" id="access" aria-labelledby="access-title"><div class="wrap"><div class="center-heading"><p class="section-eyebrow">ACCESS / {escape(store['en'])}</p><h2 id="access-title"><span>Dr.core {escape(store['name'])}</span><span>店舗情報・アクセス</span></h2></div><div class="recovery-access-grid"><figure class="recovery-access-photo"><img src="./{escape(store['photo'])}" alt="Dr.core{escape(store['name'])}の店内" width="{store['photo_width']}" height="{store['photo_height']}" loading="lazy" decoding="async"></figure><div class="recovery-access-content"><dl><div><dt>店舗名</dt><dd>Dr.core {escape(store['name'])}<small>自重ストレッチ／完全予約制</small></dd></div><div><dt>住所</dt><dd>{escape(store['address'])}<br>{escape(store['building'])}</dd></div><div><dt>アクセス</dt><dd>{escape(store['access'])}<small>{escape(store['access_sub'])}</small></dd></div></dl><a class="recovery-map-link" href="{escape(map_url)}" target="_blank" rel="noopener">Google マップで開く<span aria-hidden="true">↗</span></a><a class="recovery-page-top" href="#top">このページの先頭へ<span aria-hidden="true">↑</span></a></div></div></div></section>'''


def render_booking_content(markup, store=None):
    button_label = escape(read_data('recovery-offer.json')['button_label'])
    faq_booking = f'このページの「{button_label}」ボタンから、Web予約にお進みください。'
    return markup.replace('{{RESERVATION_FAQ}}', faq_booking)


def render_sections(source, store=None):
    destination = reservation_url(store)
    replacements = {
        '{{RESERVATION_URL}}': escape(destination),
        '{{CTA_INTRO}}': trial_banner('intro', destination),
        '{{CTA_PRICE}}': trial_banner('price', destination),
        '{{CTA_BOTTOM}}': trial_banner('bottom', destination),
        '{{CTA_STICKY}}': trial_banner('sticky', destination),
        '{{RATE_PLANS}}': render_pricing(),
        '{{TRAINER_CARDS}}': render_trainers(),
        '{{RECOVERY_FAQ}}': render_booking_content((ROOT / 'templates/partials/recovery-faq.html').read_text(encoding='utf-8'), store),
    }
    for marker, markup in replacements.items():
        source = source.replace(marker, markup)
    return source
