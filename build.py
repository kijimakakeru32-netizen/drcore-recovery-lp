#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import html, json, re
import hashlib
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
ORIGIN = ''
STORES = {
    'tsukishima': {'name': '月島店', 'en': 'TSUKISHIMA', 'area': 'TOKYO / 東京', 'address': '東京都中央区佃2-5-13', 'building': 'スカイコートパレス月島102', 'access': '東京メトロ有楽町線・都営大江戸線「月島駅」徒歩3分', 'access_sub': '6番出口からお越しいただくとスムーズです。', 'hours': '10:00〜22:00', 'closed': '年中無休', 'phone': '03-3520-8337', 'minutes': '3', 'reserve': 'https://reserve.quick-reserve.com/core?view=eyJ2ZXJzaW9uIjoyLCJzdG9yZXMiOlt7ImlkIjoyMzEsImNvdXJzZUlkcyI6WzIyMjddfV19&eid=UWGwJBTX39DN4vJmVsCbpB9fNa1CMhDO&_gl=1*1etmk5i*_ga*MTk4NjExMTc0My4xNzg2NDEyMTcy*_ga_GQJRGS8KQR*czE3ODk0MDI0MDYkbzkkZzEkdDE3ODk0MDI0MzEkajM1JGwwJGgw'},
    'motoyawata': {'name': '本八幡店', 'en': 'MOTOYAWATA', 'area': 'CHIBA / 千葉', 'address': '千葉県市川市八幡3丁目1-1', 'building': 'プレジデントビル 3F', 'access': 'JR総武線・都営新宿線「本八幡駅」徒歩2分', 'access_sub': '京成本線「京成八幡駅」からも徒歩2分。', 'hours': '10:00〜21:00', 'closed': 'なし', 'phone': '', 'minutes': '2', 'reserve': 'https://reserve.quick-reserve.com/core?view=eyJzdG9yZXMiOlt7ImlkIjozNDEsImNvdXJzZUlkcyI6WzMxNjNdfV0sInZlcnNpb24iOjJ9&eid=OXeJGjCXlLEqwwfGwW2y2nlVXKg2B59T&_gl=1*1etmk5i*_ga*MTk4NjExMTc0My4xNzg2NDEyMTcy*_ga_GQJRGS8KQR*czE3ODk0MDI0MDYkbzkkZzEkdDE3ODk0MDI0MzEkajM1JGwwJGgw'}
}

def cta(store, position, extra=''):
    text = f'{store["name"]}の体験を予約する' if store else '店舗を選んで体験を予約する'
    href = html.escape(store['reserve']) if store else '#shoplist'
    attrs = 'target="_blank" rel="noopener" data-reservation' if store else ''
    return f'<a class="btn btn--primary {extra}" href="{href}" {attrs} data-position="{position}">{text}<span class="btn__arrow" aria-hidden="true">→</span></a>'

def store_cta_template(name, store):
    return (ROOT/'templates'/name).read_text().replace('{{RESERVE_URL}}', html.escape(store['reserve']))

def shops(base):
    cards = ''
    for slug,s in STORES.items():
        dimensions = 'width="1800" height="1304"' if slug == 'tsukishima' else 'width="2200" height="1650"'
        station = '月島駅' if slug == 'tsukishima' else '本八幡駅'
        cards += f'''<a class="shop-card shop-card--{slug}" href="{base}gyms/{slug}/" data-store-link="{s['name']}">
          <div class="shop-card__visual">
            <img src="{base}assets/studio-{slug}.png" alt="Dr.core {s['name']}の店内。人工芝のフロアとトレーニング設備" {dimensions} loading="lazy" decoding="async">
            <span class="shop-card__area">{s['area']}</span>
            <span class="shop-card__en" lang="en">{s['en']}</span>
          </div>
          <div class="shop-card__body">
            <div class="shop-card__title"><div><p class="shop-card__brand">Dr.core PERSONAL TRAINING</p><h3>{s['name']}</h3></div><span class="shop-card__arrow" aria-hidden="true">↗</span></div>
            <p class="shop-card__station"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="3" width="14" height="15" rx="3"/><path d="M5 10h14M9 18l-3 4m9-4 3 4M9 21h6"/><circle cx="8.5" cy="14.5" r=".8" fill="currentColor"/><circle cx="15.5" cy="14.5" r=".8" fill="currentColor"/></svg>{station}から徒歩<strong>{s['minutes']}<span>分</span></strong></p>
            <p class="shop-card__address">{s['address']}<br>{s['building']}</p>
            <dl class="shop-card__hours"><div><dt>営業時間</dt><dd>{s['hours']}</dd></div><div><dt>定休日</dt><dd>{s['closed']}</dd></div></dl>
            <span class="shop-card__link">店舗の詳細・体験予約<span aria-hidden="true">→</span></span>
          </div>
        </a>'''
    return f'<section class="sec shoplist" id="shoplist"><div class="wrap"><div class="shoplist__header"><div><p class="eyebrow">Shop list</p><h2 class="h2">あなたの街の、Dr.core。</h2></div><p class="shoplist__lead">月島・本八幡の2店舗。<br>通いやすい店舗をお選びください。</p></div><div class="shop-grid">{cards}</div></div></section>'

def page(slug=None, full=False):
    s = STORES.get(slug)
    base = '../../' if s else './'
    brand = 'Dr.core ' + s['name'] if s else 'Dr.core'
    title = f'{brand}｜綺麗に痩せて、動けるカラダへ。パーソナルトレーニング'
    desc = f'{brand}の大人向けパーソナルトレーニング。完全マンツーマンで、姿勢・体幹・身体の使い方から理想の身体づくりをサポート。' + (s['access']+'。' if s else '月島店・本八幡店の店舗情報と料金をご案内。')
    storelabel = s['name'] if s else 'PERSONAL TRAINING'
    location = s['access'] if s else '月島・本八幡のパーソナルトレーニング'
    hero = f'''<section class="adult-hero" id="top"><div class="adult-hero__photo"><img src="{base}assets/fv_main.jpg" alt="トレーナーとマンツーマンで身体の動かし方を練習する女性" width="1800" height="1055" fetchpriority="high"></div><div class="wrap adult-hero__inner"><div class="adult-hero__copy"><p class="adult-hero__eyebrow">TRAIN WITH PURPOSE</p><p class="adult-hero__brand">{brand} / パーソナルトレーニング</p><h1>綺麗に痩せて、<br>動けるカラダへ。</h1><p class="adult-hero__lead">見た目も、動きも、心地よく。<br>あなたに合った身体の使い方から、<br class="sp-only">理想の自分をつくる。</p><p class="adult-hero__location">{location}</p><div class="hero-cta">{cta(s,'hero')}<p>初回体験 60分 <strong>1,000円</strong>（税込）<span>先着5名様限定</span></p></div></div></div><div class="hero-bottom"><div class="wrap"><span>完全マンツーマン</span><span>オーダーメイドプログラム</span><span>手ぶらで通える</span></div></div></section>'''
    body = hero + shops(base)
    if full:
        body = hero + content(s,base) + shops(base)
    links = ''.join(f'<a href="#{i}">{label}</a>' for i,label in [('method','特徴'),('reason','選ばれる理由'),('price','料金'),('flow','体験の流れ')]) if full else ''
    favicon = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"%3E%3Crect width="64" height="64" rx="12" fill="%230e1113"/%3E%3Ctext x="10" y="45" font-family="Arial" font-weight="700" font-size="42" fill="white"%3ED%3C/text%3E%3Ccircle cx="51" cy="44" r="5" fill="%232dd97a"/%3E%3C/svg%3E'
    floating = store_cta_template('store-floating.html', s) if s else f'''<div class="booking-bar" hidden><div class="wrap"><div class="booking-bar__text"><span>{brand}</span><b>初回体験 60分 1,000円</b></div>{cta(s,"sticky")}</div></div>'''
    doc = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="format-detection" content="telephone=no"><title>{title}</title><meta name="description" content="{desc}"><meta name="theme-color" content="#0e1113"><meta property="og:type" content="website"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href='{favicon}'><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700;900&display=swap" rel="stylesheet"><link rel="stylesheet" href="{base}assets/base.css"><link rel="stylesheet" href="{base}assets/site.css"><script src="{base}assets/site.js" defer></script></head><body data-store="{'Dr.core '+s['name'] if s else 'Dr.core 全店舗'}"><a class="skip-link" href="#main">本文へスキップ</a><header class="site-header"><div class="wrap site-header__inner"><a class="site-logo" href="{base}" aria-label="Dr.core トップページ"><img src="{base}assets/logo-transparent.svg" width="1691" height="393" alt="Dr.core"><span>{storelabel}</span></a><nav class="desktop-nav" aria-label="メインメニュー">{links}</nav><a class="shop-nav" href="#shoplist">SHOP LIST <span aria-hidden="true">↗</span></a><button class="menu-button" aria-label="メニューを開く" aria-expanded="false" aria-controls="mobile-nav"><span></span><span></span></button></div><nav id="mobile-nav" class="mobile-nav" aria-label="モバイルメニュー" hidden>{links}<a href="#shoplist">店舗一覧</a>{cta(s,'menu')}</nav></header><main id="main">{body}</main>{floating}<footer class="site-footer"><div class="wrap"><div class="footer-top"><a href="{base}"><img src="{base}assets/logo-transparent.svg" width="1691" height="393" alt="Dr.core トップページ"></a><p>綺麗に痩せて、動けるカラダへ。</p></div><div class="footer-links"><a href="{base}">トップページ</a><a href="{base}gyms/tsukishima/">月島店</a><a href="{base}gyms/motoyawata/">本八幡店</a><a href="https://drcore.jp/privacy-policy">プライバシーポリシー</a><a href="https://drcore.jp/terms-of-service">利用規約</a><a href="https://drcore.jp/company">運営会社</a></div><p class="copyright">© 2026 Dr.core All Rights Reserved.</p></div></footer></body></html>'''
    tracking=(ROOT/'templates/tracking.html').read_text()
    doc=doc.replace('</head>',tracking+'</head>')
    if s:
        revision = hashlib.sha256((DIST/'assets/store-cta.css').read_bytes()).hexdigest()[:12]
        doc = doc.replace('</head>', f'<link rel="stylesheet" href="{base}assets/store-cta.css?v={revision}"></head>')
    for asset in ['base.css', 'site.css', 'site.js', 'logo-transparent.svg']:
        revision = hashlib.sha256((DIST/'assets'/asset).read_bytes()).hexdigest()[:12]
        doc = doc.replace(f'{base}assets/{asset}"', f'{base}assets/{asset}?v={revision}"')
    doc=doc.replace('<body data-store=', '<body data-store=')
    if ORIGIN:
        url=ORIGIN+('/gyms/'+slug+'/' if slug else '/')
        doc=doc.replace('</head>',f'<link rel="canonical" href="{url}"><meta property="og:url" content="{url}"><meta property="og:image" content="{ORIGIN}/assets/ogp.jpg"></head>')
    out = DIST / ('gyms/'+slug if slug else '')
    out.mkdir(parents=True,exist_ok=True)
    (out/'index.html').write_text(doc)

def content(s,base):
    sections = []
    for name in ['check','method','reason','program','session','price','flow']:
        text = (ROOT/'templates'/f'{name}.html').read_text()
        text = text.replace('./images/',base+'assets/').replace('{{CTA_PRICE}}',cta(s,'price'))
        sections.append(text)
    if s:
        address = s['address']+' '+s['building']
        query = quote(address)
        phone = f'<div><dt>電話</dt><dd><a href="tel:{s["phone"].replace("-", "")}">{s["phone"]}</a></dd></div>' if s['phone'] else ''
        sections.append(f'''<section class="sec store-access" id="access"><div class="wrap"><p class="eyebrow">Access / {s['en']}</p><h2 class="h2">Dr.core {s['name']}の<br>店舗情報・アクセス</h2><div class="access"><div><div class="access__map"><iframe title="Dr.core {s['name']}の地図" src="https://www.google.com/maps?q={query}&amp;output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div><a class="map-link" href="https://www.google.com/maps/search/?api=1&amp;query={query}" target="_blank" rel="noopener">Google マップで開く ↗</a></div><div><dl class="dl"><div><dt>店舗名</dt><dd>Dr.core {s['name']}<span class="sub">パーソナルトレーニング／完全予約制</span></dd></div><div><dt>住所</dt><dd>{s['address']}<span class="sub">{s['building']}</span></dd></div><div><dt>アクセス</dt><dd>{s['access']}<span class="sub">{s['access_sub']}</span></dd></div><div><dt>営業時間</dt><dd>{s['hours']}<span class="sub">定休日：{s['closed']}</span></dd></div>{phone}<div><dt>駐車場</dt><dd>専用駐車場なし<span class="sub">近隣のコインパーキングをご利用ください。</span></dd></div></dl><div class="access-cta">{cta(s,'access')}<p class="note">Webから24時間ご予約いただけます。</p></div></div></div></div></section>''')
    sections.append((ROOT/'templates/faq.html').read_text())
    if s:
        sections.append(store_cta_template('store-trial.html', s))
    else:
        sections.append(f'''<section class="sec final-cta" id="trial"><div class="wrap"><p class="eyebrow">Start your training</p><h2 class="h2">これからの身体に、<br>今日からできること。</h2><p>まずは体験トレーニングで、<br>自分の身体と向き合ってみませんか。</p><div class="cta-block">{cta(s,'bottom')}<p class="micro">初回体験60分・先着5名様 1,000円（税込）</p></div></div></section>''')
    return '\n'.join(sections)

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--full',action='store_true')
    parser.add_argument('--origin',default='')
    args=parser.parse_args()
    ORIGIN=args.origin.rstrip('/')
    page(full=args.full)
    if args.full:
        for slug in STORES: page(slug,True)
    if ORIGIN:
        urls = [ORIGIN+'/'] + [ORIGIN+'/gyms/'+slug+'/' for slug in STORES]
        sitemap = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>'+url+'</loc></url>' for url in urls) + '</urlset>'
        (DIST/'sitemap.xml').write_text(sitemap)
        (DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+ORIGIN+'/sitemap.xml\n')
    print('Generated LP pages.')
