"""Build the Recovery home, store LPs and shared customer voice articles."""
from pathlib import Path
import hashlib
import html
import json
import re
from recovery_sections import load_stores, render_sections, render_store_access, render_store_cards

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'


def load_voices():
    """Keep supplied manuscript paragraphs as text, without shortening them."""
    voices = json.loads((ROOT / 'data/voices.json').read_text(encoding='utf-8'))
    slugs = set()
    for voice in voices:
        slug = voice['slug']
        if not slug or any(character not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for character in slug):
            raise ValueError(f'Invalid voice URL slug: {slug!r}')
        if slug in slugs:
            raise ValueError(f'Duplicate voice URL slug: {slug}')
        slugs.add(slug)
        for field in ['name', 'age', 'attribute', 'theme', 'main_concerns']:
            if not isinstance(voice[field], str):
                raise ValueError(f'{slug}: {field} must be text')
        for field in ['card_title', 'card_intro', 'article_title', 'editorial_label']:
            if voice.get(field) is not None and not isinstance(voice[field], str):
                raise ValueError(f'{slug}: {field} must be text or null')
        paragraphs = voice.get('paragraphs')
        if paragraphs is not None and (not isinstance(paragraphs, list) or any(not isinstance(paragraph, str) for paragraph in paragraphs)):
            raise ValueError(f'{slug}: paragraphs must be an array of text or null')
        validate_voice_photo(voice)
    return voices


def escape(value):
    return html.escape(str(value), quote=True)


def voice_identity(voice):
    return '｜'.join([voice['name'], voice['age'], voice['attribute']])


def validate_voice_photo(voice):
    """Accept only existing local raster assets and simple crop coordinates."""
    slug = voice['slug']
    photo = voice.get('photo')
    if photo is not None:
        if not isinstance(photo, str) or not re.fullmatch(r'assets/[A-Za-z0-9_./-]+', photo):
            raise ValueError(f'{slug}: photo must be a local assets path or null')
        path = Path(photo)
        if '..' in path.parts or path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.avif'}:
            raise ValueError(f'{slug}: photo must be a local raster image')
        resolved = (DIST / path).resolve()
        if not resolved.is_relative_to((DIST / 'assets').resolve()) or not resolved.is_file():
            raise ValueError(f'{slug}: photo asset is missing or outside assets: {photo}')
    alt = voice.get('photo_alt')
    if alt is not None and not isinstance(alt, str):
        raise ValueError(f'{slug}: photo_alt must be text or null')
    position = voice.get('photo_object_position', '50% 50%')
    coordinate = r'(?:left|center|right|top|bottom|(?:100|[0-9]{1,2})(?:\.\d+)?%)'
    if not isinstance(position, str) or not re.fullmatch(coordinate + r'(?:\s+' + coordinate + r')?', position):
        raise ValueError(f'{slug}: photo_object_position must use keywords or percentage coordinates')


def photo_placeholder(voice):
    # A neutral graphic must never imply that it depicts the customer.
    return f'''<div class="voice-photo-placeholder" role="img" aria-label="{escape(voice['name'])}の写真掲載予定位置。写真は未提供です。"><svg viewBox="0 0 64 64" fill="none" aria-hidden="true"><rect x="8" y="12" width="48" height="40" rx="5"/><circle cx="24" cy="25" r="5"/><path d="m12 45 13-13 10 10 8-8 9 11"/></svg><span>お客様写真 掲載予定</span><small>写真確認待ち</small></div>'''


def render_voice_photo(voice, asset_prefix='./'):
    validate_voice_photo(voice)
    photo = voice.get('photo')
    if not photo:
        return photo_placeholder(voice)
    alt = voice.get('photo_alt') or f"{voice['name']}の写真"
    position = voice.get('photo_object_position', '50% 50%')
    return f'''<figure class="voice-photo"><img src="{escape(asset_prefix + photo)}" alt="{escape(alt)}" loading="lazy" decoding="async" style="object-position:{escape(position)}"></figure>'''


def render_voice_cards(voices, site_prefix='./'):
    cards = []
    for voice in voices:
        title = voice.get('card_title') or '紹介タイトル：原稿確認待ち'
        title_html = ''.join(f'<span>{escape(line)}</span>' for line in title.splitlines())
        intro = voice.get('card_intro') or '紹介文：原稿確認待ち'
        card_identity = '｜'.join([voice['name'], voice['age']])
        editorial = f'<p class="voice-editorial-label">{escape(voice["editorial_label"])}</p>' if voice.get('editorial_label') else ''
        cards.append(f'''<article class="voice-card" data-voice-id="{escape(voice['slug'])}"><a class="voice-read-more voice-card-link" href="{escape(site_prefix)}voices/{escape(voice['slug'])}/" aria-label="{escape(voice['name'])}のお客様の声を詳しく読む">{render_voice_photo(voice)}<div class="voice-card-content">{editorial}<p class="voice-identity">{escape(card_identity)}<span class="voice-card-arrow" aria-hidden="true">→</span></p><h3 class="voice-card-title">{title_html}</h3><p class="voice-card-intro">{escape(intro)}</p></div></a></article>''')
    return '''<div class="voice-carousel"><div class="voice-carousel-toolbar"><p>横にスクロール <span aria-hidden="true">→</span></p><div class="voice-carousel-controls" hidden><button class="voice-prev" type="button" aria-label="前のお客様の声を表示" aria-controls="voice-track"><span aria-hidden="true">←</span></button><button class="voice-next" type="button" aria-label="次のお客様の声を表示" aria-controls="voice-track"><span aria-hidden="true">→</span></button></div></div><div class="voice-grid" id="voice-track" tabindex="0" role="region" aria-label="お客様の声。左右にスクロールしてご覧ください">''' + '\n'.join(cards) + '</div></div>'


def revision_assets(source):
    for name in ['recovery.css', 'recovery-stores.css', 'recovery.js', 'voices.css', 'logo-transparent.svg', 'logo-dark.svg']:
        revision = hashlib.sha256((DIST / 'assets' / name).read_bytes()).hexdigest()[:12]
        source = source.replace(f'assets/{name}"', f'assets/{name}?v={revision}"')
    return source


def build_voice_pages(voices, origin=''):
    template = (ROOT / 'templates/recovery-voice.html').read_text(encoding='utf-8')
    for voice in voices:
        title = voice.get('article_title') or f"{voice['name']}のお客様の声"
        paragraphs = voice.get('paragraphs')
        if paragraphs:
            body = '\n'.join(
                ('<p class="voice-quote">' if paragraph.startswith('「') and paragraph.endswith('」') else '<p>')
                + escape(paragraph).replace('\n', '<br>') + '</p>'
                for paragraph in paragraphs
            )
        else:
            body = '<div class="voice-manuscript-pending"><h2>記事本文：原稿確認待ち</h2><p>お客様の声原稿は未提供のため、本文は掲載していません。</p></div>'
        if paragraphs:
            sample_description = 'この文章は確認用のサンプルです。実際のお客様への取材内容ではありません。'
            if not voice.get('photo'):
                sample_description += '写真は確認待ちです。'
        else:
            sample_description = ('原稿の確認待ちです。' if voice.get('photo') else '原稿・写真の確認待ちです。') + '掲載位置と画面構成を確認するためのサンプルです。'
        sample_notice = f'<aside class="voice-sample-notice" aria-label="サンプル原稿について"><strong>掲載イメージ（サンプル）</strong><p>{sample_description}</p></aside>' if voice.get('is_sample', True) else ''
        metadata = ''
        if origin:
            url = escape(origin.rstrip('/') + f"/voices/{voice['slug']}/")
            metadata = f'<link rel="canonical" href="{url}"><meta property="og:url" content="{url}">'
        replacements = {
            '{{VOICE_ID}}': escape(voice['slug']),
            '{{VOICE_TITLE}}': escape(title),
            '{{VOICE_IDENTITY}}': escape(voice_identity(voice)),
            '{{VOICE_THEME}}': escape(voice['theme']),
            '{{VOICE_CONCERNS}}': escape(voice['main_concerns']),
            '{{VOICE_PHOTO}}': render_voice_photo(voice, '../../'),
            '{{VOICE_BODY}}': body,
            '{{VOICE_SAMPLE_NOTICE}}': sample_notice,
            '{{ORIGIN_META}}': metadata,
        }
        source = template
        for placeholder, replacement in replacements.items():
            source = source.replace(placeholder, replacement)
        destination = DIST / 'voices' / voice['slug']
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'index.html').write_text(revision_assets(source), encoding='utf-8')


def build_landing_page(voices, stores, origin='', store=None):
    """Use the approved template for the general LP and both full store LPs."""
    prefix = '../../' if store else './'
    title = f"Dr.core Recovery {store['name']}｜{store['station']}徒歩{store['minutes']}分・自重ストレッチ" if store else 'Dr.core Recovery｜自重ストレッチ・身体のメンテナンス'
    description = (
        f"Dr.core Recovery {store['name']}のマンツーマン自重ストレッチ。{store['access']}。"
        if store else '月島店・本八幡店で、自重ストレッチによる身体のメンテナンス。'
    ) + '通常プランは1回30分。初回体験は体組成・姿勢診断付きの60分・1,000円。料金プランとWeb予約をご案内。'
    hero_label = f'''<span class="hero-store-name">Dr.core Recovery {escape(store['name'])}</span><span class="hero-store-station">{escape(store['station'])} 徒歩{escape(store['minutes'])}分</span>''' if store else 'Dr.coreの自重ストレッチ'
    footer_links = f'<a href="{prefix}#top">トップページ</a>' + ''.join(f'<a href="{prefix}gyms/{escape(item["slug"])}/">{escape(item["name"])}</a>' for item in stores)
    metadata = ''
    if origin:
        url = origin.rstrip('/') + (f"/gyms/{store['slug']}/" if store else '/')
        metadata = f'<link rel="canonical" href="{escape(url)}"><meta property="og:url" content="{escape(url)}"><meta property="og:image" content="{escape(origin.rstrip("/"))}/assets/fv_main.jpg">'
    replacements = {
        '{{PAGE_TITLE}}': escape(title),
        '{{PAGE_DESCRIPTION}}': escape(description),
        '{{STORE_SLUG}}': escape(store['slug'] if store else 'all'),
        '{{TOP_HREF}}': prefix + '#top' if store else '#top',
        '{{LOCATION_NAV_HREF}}': '#access' if store else '#locations',
        '{{LOCATION_NAV_LABEL}}': '店舗情報' if store else '店舗一覧',
        '{{HERO_LABEL}}': hero_label,
        '{{VOICE_CARDS}}': render_voice_cards(voices, prefix),
        '{{STORE_ACCESS}}': render_store_access(store),
        '{{STORE_CARDS}}': render_store_cards(stores, prefix, store),
        '{{FOOTER_PAGE_LINKS}}': footer_links,
        '{{TRIAL_STATUS}}': 'ご予約はWebより受け付けています。' if store else 'ご希望の店舗をお選びいただき、初回体験をご予約ください。',
        '{{ORIGIN_META}}': metadata,
    }
    source = render_sections((ROOT / 'templates/recovery-home.html').read_text(encoding='utf-8'), store)
    for marker, markup in replacements.items():
        source = source.replace(marker, markup)
    # Shared section assets remain template-relative; each generated page uses
    # its own relative prefix so direct access and subfolder hosting both work.
    source = revision_assets(source.replace('./assets/', prefix + 'assets/'))
    source = re.sub(r'[ \t]+\n', '\n', source)
    if re.search(r'\{\{[A-Z_]+\}\}', source):
        raise ValueError(f'Unresolved template marker in {store["slug"] if store else "home"}')
    destination = DIST / 'gyms' / store['slug'] if store else DIST
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'index.html').write_text(source, encoding='utf-8')


def build_home(origin=''):
    """Preserve the build entry point while generating all Recovery pages."""
    origin = origin.rstrip('/')
    voices = load_voices()
    stores = load_stores()
    build_landing_page(voices, stores, origin)
    for store in stores:
        build_landing_page(voices, stores, origin, store)
    build_voice_pages(voices, origin)
    urls = [origin + '/'] + [origin + f"/gyms/{store['slug']}/" for store in stores] if origin else []
    sitemap = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{escape(url)}</loc></url>' for url in urls) + '</urlset>'
    (DIST / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
    (DIST / 'robots.txt').write_text('User-agent: *\nAllow: /\n' + (f'Sitemap: {origin}/sitemap.xml\n' if origin else ''), encoding='utf-8')
    print('Generated Dr.core Recovery home page, 2 full store LPs and 3 sample voice pages.')
