#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Recovery's homepage, two store LPs and shared sample voice articles."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
import json
import re
import ast
import argparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent / 'dist'
PAGE = ROOT / 'index.html'
HERO_PHOTO = ROOT / 'assets/recovery-hero-portrait.jpg'
HERO_LOGO = ROOT / 'assets/logo-transparent.svg'
STORE_IDS = ('tsukishima', 'motoyawata')
STORE_PROFILES = {
    'tsukishima': {
        'name': '月島店', 'address': '東京都中央区佃2-5-13',
        'building': 'スカイコートパレス月島102', 'station': '月島駅',
        'minutes': '3', 'photo': 'assets/studio-tsukishima.png',
    },
    'motoyawata': {
        'name': '本八幡店', 'address': '千葉県市川市八幡3丁目1-1',
        'building': 'プレジデントビル3F', 'station': '本八幡駅',
        'minutes': '2', 'photo': 'assets/studio-motoyawata.png',
    },
}
VOICE_IDS = ('a', 'd', 'c')
VOICE_PROFILES = {
    'a': ('Aさん', '50代女性', 'デスクワーク', '肩こり・疲労感'),
    'd': ('Dさん', '40代男性', '会社員・ゴルフ愛好家', 'ゴルフをもっと楽しめる身体へ'),
    'c': ('Cさん', '50代女性', '主婦', '姿勢・歩きやすさ'),
}
DAYTIME_VOICE_LABEL = '平日昼の利用イメージ（取材・写真確認待ち）'
VOICE_RESULTS_NOTE = '※個人の感想です。感じ方や変化には個人差があります。'
PAYG_OPTIONS = (
    ('daytime_price', '平日10:00〜15:00'),
    ('regular_price', 'その他の平日・土日祝'),
)
TRAINER_PROFILES = (
    ('takakura', '高倉トレーナー'),
    ('yoshioka', '吉岡トレーナー'),
    ('yoshinaga', '吉永トレーナー'),
    ('kuboki', '久保木トレーナー'),
)
SECTION_ORDER = (
    'top', 'concerns', 'daytime', 'message', 'method', 'session', 'first-visit', 'voices',
    'trainers', 'price', 'flow', 'faq', 'locations', 'trial',
)
HOME_COPY = {
    'top': (
        '自重ストレッチでしなやかに動ける身体へ',
        '器具に支えられながら、自分では届かないところまで。30分のマンツーマン自重ストレッチ',
        '完全予約制マンツーマン',
        '30分だから通いやすい',
        '平日10〜15時1回4,750円〜',
        '※平日デイタイムプラン・月8回の場合',
    ),
    'concerns': (
        '最近、このような体の変化はありませんか？',
        'その重さを、いつものことにしないために。',
        '疲労', 'しっかり寝たはずなのに、朝から身体がだるい',
        '肩・首', 'デスクワークが続くと、首や肩が重くなる',
        '腰', '立ち上がるたびに、腰の重さが気になる',
        '猫背', 'ふと鏡を見ると、背中が丸くなっている',
        '反り腰', 'まっすぐ立っているだけで、腰がつらい',
        '歩行', '以前より、長く歩くと疲れやすくなった',
        '座りっぱなしの仕事や、毎日の家事。'
        '気づかないうちに、身体に力が入っていませんか。'
        'Dr.coreでは、一人ひとりの身体の状態に合わせた自重ストレッチで、柔軟性や動きやすさの改善をサポートします。',
    ),
    'daytime': (
        '平日昼の30分を、自分のために。',
        '在宅ワークの昼休みに', '平日休みの日に', '家事の合間に30分',
        '平日10:00〜15:00なら、日常のすき間に通いやすいデイタイムプランをご利用いただけます。',
    ),
    'message': (
        'Dr.coreは',
        'カラダの緊張をほどき、軽やかに動けるように導きます',
    ),
    'method': (
        'Dr.core 自重ストレッチ3つの強み',
        'プロが導く、最適なストレッチ',
        '身体の状態や柔軟性に合わせて、専門トレーナーがマンツーマンでサポート。自分では伸ばしにくい部分まで、一人ひとりに合わせて丁寧にアプローチします。',
        '器具に身体を預けて、ラクに深く伸ばす',
        'TRXなどの器具に身体を支えてもらい、自分の体重を使ってゆっくり伸ばします。トレーナーが角度や体重のかけ方を調整し、無理なく心地よく伸ばせるようサポートします。',
        '伸ばすだけじゃない。動きやすい身体へ。',
        'ただ受けるだけではなく、自分自身のバランス機能も活用しながらストレッチ。柔軟性だけでなく身体の動かしやすさも高め、継続することで元の硬さに戻りにくい、軽やかに動ける身体を目指します。',
    ),
    'session': (
        '通常プラン・1回30分',
        '30分で、全身を心地よくDr.coreのアプローチ',
        '可動域を広げる',
        '器具に支えられて、伸ばす',
        'プロの手で、丁寧に伸ばす',
        '初回体験は、体組成・姿勢診断を含む60分です。',
    ),
    'first-visit': (
        'まずは一度、カラダの変化を感じてみませんか？',
        'あなたに合ったストレッチを、初回体験で。',
        '今のカラダを一緒にチェック',
        '気になる悩みを伺い、姿勢や動かしやすさを確認します。',
        'カラダに合わせて、無理なく伸ばす',
        'トレーナーのサポートで、一人ひとりに合ったストレッチを体験します。',
        '目標と生活に合う通い方をご案内',
        'どうなりたいか、どれくらい通えるかを伺い、続けやすいプランをご提案します。',
    ),
    'trainers': (
        'Dr.coreのトレーナー紹介',
        '経験豊富なトレーナーが、お客様の体をサポートします。',
    ),
    'price': (
        '平日昼なら、1回4,750円〜',
        '※平日10:00〜15:00・月8回の場合',
        '1回30分だから、気軽に通えて継続しやすい',
        '入会金0円',
        '平日デイタイムプラン平日10:00〜15:00',
        'レギュラープラン平日10:00〜15:00以外・土日祝',
    ),
}
VOID_TAGS = {
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
    'meta', 'param', 'source', 'track', 'wbr',
}


class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.assets = []
        self.controls = []
        self.h1 = 0
        self.text = []
        self.regions = {}
        self.stack = []
        self.elements = []
        self.anchors = []
        self.metadata = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        region = attrs.get('id')
        if region:
            self.ids.append(region)
            self.regions.setdefault(region, [])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if tag == 'meta' and attrs.get('name'):
            self.metadata[attrs['name'].lower()] = attrs.get('content', '')
        if tag == 'meta' and attrs.get('property'):
            self.metadata[attrs['property'].lower()] = attrs.get('content', '')
        if attrs.get('aria-controls'):
            self.controls.extend(attrs['aria-controls'].split())
        if tag in {'img', 'script', 'source'} and attrs.get('src'):
            self.assets.append(attrs['src'])
        if tag in {'img', 'source'} and attrs.get('srcset'):
            # A data URL is self-contained; its commas are not candidate separators.
            if not attrs['srcset'].strip().startswith('data:'):
                self.assets.extend(item.strip().split()[0]
                                   for item in attrs['srcset'].split(',') if item.strip())
        if tag == 'link' and attrs.get('href'):
            self.assets.append(attrs['href'])
        element = {'tag': tag, 'attrs': attrs, 'text': [], 'all_text': [],
                   'parent': self.stack[-1] if self.stack else None}
        self.elements.append(element)
        if tag == 'a':
            self.anchors.append(element)
        if tag not in VOID_TAGS:
            self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]['tag'] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for element in self.stack:
            element['all_text'].append(data)
        if any(element['tag'] in {'script', 'style'}
               or element['attrs'].get('aria-hidden') == 'true' for element in self.stack):
            return
        self.text.append(data)
        for element in self.stack:
            element['text'].append(data)
            region = element['attrs'].get('id')
            if region:
                self.regions[region].append(data)


def compact(parts):
    return re.sub(r'\s+', '', ''.join(parts))


def local_path(reference, referring_file):
    parsed = urlparse(reference)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    destination = ((ROOT / path.lstrip('/')) if path.startswith('/')
                   else referring_file.parent / path) if path else referring_file
    destination = destination.resolve()
    assert destination.is_relative_to(ROOT), f'Reference leaves dist: {reference}'
    if destination.is_dir():
        destination /= 'index.html'
    return destination


def check_asset(reference, referring_file, visited):
    destination = local_path(reference, referring_file)
    if destination is None:
        return
    assert destination.is_file(), f'Missing asset in {referring_file.name}: {reference}'
    if destination.suffix.lower() != '.css' or destination in visited:
        return
    visited.add(destination)
    css = destination.read_text(encoding='utf-8')
    references = re.findall(r'url\(\s*[\'"]?([^\'"\)]+)[\'"]?\s*\)', css)
    references += re.findall(r'@import\s+[\'"]([^\'"]+)[\'"]', css)
    for nested in references:
        check_asset(nested.strip(), destination, visited)


def has_amount(text, amount):
    digits = f'{amount:,}'
    return bool(re.search(rf'(?<![\d,])(?:{re.escape(digits)}|{amount})(?![\d,])', text))


def has_class(element, name):
    return name in element['attrs'].get('class', '').split()


def is_within(element, ancestor):
    while element is not None:
        if element is ancestor:
            return True
        element = element['parent']
    return False


def load_stores():
    source = ROOT.parent / 'data/recovery-stores.json'
    assert source.is_file(), 'Missing shared Recovery store data.'
    stores = json.loads(source.read_text(encoding='utf-8'))
    assert isinstance(stores, list) and tuple(store['slug'] for store in stores) == STORE_IDS, \
        'Recovery store data must contain the corresponding Tsukishima and Motoyawata stores.'
    legacy_source = ast.parse((ROOT.parent / 'build.py').read_text(encoding='utf-8'))
    legacy_assignment = next(node for node in legacy_source.body if isinstance(node, ast.Assign)
                             and any(isinstance(target, ast.Name) and target.id == 'STORES'
                                     for target in node.targets))
    legacy_stores = ast.literal_eval(legacy_assignment.value)
    for store in stores:
        slug = store['slug']
        for field, expected in STORE_PROFILES[slug].items():
            assert compact([str(store[field])]) == compact([expected]), \
                f'Recovery store {slug} has the wrong {field}.'
        assert store['reserve'] == legacy_stores[slug]['reserve'], \
            f'Recovery store {slug} must use the existing adult reservation URL authorized by the user.'
        parsed = urlparse(store['reserve'])
        assert parsed.scheme == 'https' and parsed.netloc == 'reserve.quick-reserve.com', \
            f'Recovery store {slug} needs its approved HTTPS reservation URL.'
    return stores


def check_page(page):
    assert page.is_file(), f'Build {page.relative_to(ROOT)} before verification.'
    scan = Scan()
    scan.feed(page.read_text(encoding='utf-8'))
    assert scan.h1 == 1, f'{page.name}: expected one h1; found {scan.h1}.'
    duplicates = [name for name, count in Counter(scan.ids).items() if count > 1]
    assert not duplicates, f'Duplicate IDs: {duplicates}'
    assert set(scan.controls).issubset(scan.ids), 'An aria-controls target is missing.'
    bodies = [element for element in scan.elements if element['tag'] == 'body']
    assert len(bodies) == 1 and bodies[0]['attrs'].get('data-program') == 'Recovery', \
        f'{page.relative_to(ROOT)} must be a Recovery page.'

    visited_css = set()
    for reference in scan.assets:
        check_asset(reference, page, visited_css)

    approved_reservations = {store['reserve'] for store in load_stores()}
    for anchor in scan.anchors:
        reference = anchor['attrs'].get('href', '')
        assert reference.strip(), 'An anchor has an empty href.'
        parsed = urlparse(reference)
        if 'quick-reserve' in parsed.netloc.lower():
            assert reference in approved_reservations, f'Unapproved reservation URL: {reference}'
            assert anchor['attrs'].get('target') == '_blank' \
                and 'noopener' in anchor['attrs'].get('rel', '').split(), \
                'External reservation links must open with target="_blank" and rel="noopener".'
        destination = local_path(reference, page)
        if destination is None:
            continue
        assert destination.is_file(), f'Missing local link target: {reference}'
        if parsed.fragment:
            target = scan
            if destination != page:
                target = Scan()
                target.feed(destination.read_text(encoding='utf-8'))
            assert unquote(parsed.fragment) in target.ids, f'Missing anchor target: {reference}'

    assert not re.search(r'先着5名|永続割引|ペア割|U18|綺麗に痩せて|PRE.?OPEN|プレオープン|先行登録',
                         compact(scan.text), re.I), 'Inherited adult campaign copy remains.'
    naming_text = ''.join(scan.text) + ''.join(scan.metadata.values()) + ''.join(
        element['attrs'].get(field, '') for element in scan.elements for field in ('alt', 'aria-label', 'title')
    )
    assert not re.search(r'リカバリーストレッチ|ストレッチ専門プラン|パーソナルストレッチ', naming_text), \
        'Use the unified Japanese service name 自重ストレッチ.'
    assert not re.search(r'\{\{[A-Z_]+\}\}', page.read_text(encoding='utf-8')), \
        f'Unexpanded template marker in {page.relative_to(ROOT)}.'
    return scan


def check_home(scan, page=PAGE, store=None):
    section_order = list(SECTION_ORDER)
    if store:
        section_order.insert(section_order.index('locations'), 'access')
    required_ids = set(section_order)
    assert required_ids.issubset(scan.ids), f'Missing sections: {required_ids - set(scan.ids)}'
    assert [scan.ids.index(region) for region in section_order] == sorted(
        scan.ids.index(region) for region in section_order
    ), 'The homepage sections are not in the supplied reading order.'
    assert 'purposes' not in scan.ids and not any(has_class(element, 'purpose-card')
                                                for element in scan.elements), \
        'Remove the customer-purpose section as requested.'
    text = compact(scan.text)
    assert 'Recovery' in text and 'TRX' in text, 'Recovery / TRX identity is missing.'
    for region, phrases in HOME_COPY.items():
        section_text = compact(scan.regions[region])
        for phrase in phrases:
            assert compact([phrase]) in section_text, f'Missing supplied copy in #{region}: {phrase}'
    heading = next(element for element in scan.elements if element['tag'] == 'h1')
    assert compact(heading['text']) == compact([HOME_COPY['top'][0]]), 'The main headline differs from supplied copy.'
    hero_lines = [element for element in scan.elements
                  if element['tag'] == 'span' and has_class(element, 'hero-title-line')
                  and is_within(element, heading)]
    assert [compact(element['text']) for element in hero_lines] == [
        '自重ストレッチで', 'しなやかに動ける', '身体へ'
    ], 'The main headline must preserve its three explicit, punctuation-free lines.'
    point_lists = [element for element in scan.elements
                   if has_class(element, 'hero-points')]
    assert len(point_lists) == 1, 'Expected one hero feature list.'
    points = [element for element in scan.elements if element['tag'] == 'li'
              and element['parent'] is point_lists[0]]
    assert len(points) == 3, 'Expected three hero features.'
    for element, phrase in zip(points, HOME_COPY['top'][2:5]):
        assert compact([phrase]) in compact(element['text']), f'Missing hero feature: {phrase}'
    assert HOME_COPY['top'][5] in compact(points[2]['text']), \
        'The monthly-eight-session condition must stay with the third hero price feature.'
    hero = next(element for element in scan.elements if element['attrs'].get('id') == 'top')
    visuals = [element for element in scan.elements
               if has_class(element, 'hero-visual') and is_within(element, hero)]
    details = [element for element in scan.elements
               if has_class(element, 'hero-details') and is_within(element, hero)]
    assert len(visuals) == len(details) == 1 \
        and visuals[0]['parent'] is hero and details[0]['parent'] is hero, \
        'The hero must separate its first-screen visual from its following detail block.'
    copies = [element for element in scan.elements if has_class(element, 'hero-copy')]
    photos = [element for element in scan.elements if has_class(element, 'hero-photo')]
    assert len(copies) == len(photos) == 1 and is_within(copies[0], visuals[0]) \
        and is_within(photos[0], visuals[0]) and is_within(heading, copies[0]), \
        'The hero visual must retain its headline copy and one photo.'
    leads = [element for element in scan.elements if has_class(element, 'hero-lead')]
    assert len(leads) == 1 and is_within(leads[0], copies[0]) \
        and compact(leads[0]['text']) == HOME_COPY['top'][1], \
        'Keep the existing service explanation with the headline inside the hero visual.'
    images = [element for element in scan.elements
              if element['tag'] == 'img' and is_within(element, photos[0])]
    assert len(images) == 1 \
        and local_path(images[0]['attrs'].get('src', ''), page) == HERO_PHOTO \
        and images[0]['attrs'].get('width') == '1080' and images[0]['attrs'].get('height') == '1920', \
        'Every LP hero must use the supplied 1080×1920 portrait asset.'
    brands = [element for element in scan.elements if has_class(element, 'hero-brand')]
    assert len(brands) == 1 and brands[0]['tag'] == 'div' and brands[0]['parent'] is visuals[0], \
        'Show one unlinked brand directly inside the initial hero visual.'
    brand_images = [element for element in scan.elements
                    if element['tag'] == 'img' and element['parent'] is brands[0]]
    assert len(brand_images) == 1 and brand_images[0]['attrs'].get('alt') == 'Dr.core' \
        and local_path(brand_images[0]['attrs'].get('src', ''), page) == HERO_LOGO \
        and brand_images[0]['attrs'].get('width') == '1691' and brand_images[0]['attrs'].get('height') == '393', \
        'The initial hero logo must retain the local white Dr.core SVG and its intrinsic dimensions.'
    assert not any(is_within(anchor, visuals[0]) for anchor in scan.anchors) \
        and is_within(point_lists[0], details[0]) and not is_within(point_lists[0], visuals[0]), \
        'Keep the hero visual focused on its photo and copy, with all three features below it.'
    assert not any(is_within(anchor, details[0]) for anchor in scan.anchors), \
        'Remove the service-detail link below the three hero features.'
    hero_ctas = [anchor for anchor in scan.anchors
                 if has_class(anchor, 'cta-fixed') and anchor['attrs'].get('data-position') == 'hero']
    assert len(hero_ctas) == 1 and is_within(hero_ctas[0], hero) \
        and not is_within(hero_ctas[0], visuals[0]) \
        and scan.elements.index(visuals[0]) < scan.elements.index(details[0]) < scan.elements.index(hero_ctas[0]), \
        'Keep the existing hero trial banner after the visual and detail blocks.'
    concern_lists = [element for element in scan.elements if has_class(element, 'concern-grid')]
    assert len(concern_lists) == 1, 'Expected one concern list.'
    concerns = [element for element in scan.elements if element['tag'] == 'li'
                and element['parent'] is concern_lists[0]]
    assert len(concerns) == 6, 'Expected six supplied concern cards.'
    concern_titles = [element for element in scan.elements
                      if element['tag'] == 'h2' and has_class(element, 'concern-title')]
    assert len(concern_titles) == 1, 'Expected one concern heading.'
    title_lines = [element for element in scan.elements if element['parent'] is concern_titles[0]]
    assert [compact(element['text']) for element in title_lines] == [
        '最近、このような', '体の変化はありませんか？'
    ], 'The concern heading must explicitly group the two supplied mobile lines.'
    concern_closings = [element for element in scan.elements if has_class(element, 'concern-closing')]
    assert len(concern_closings) == 1, 'Expected one concern-closing block.'
    closing_headings = [element for element in scan.elements
                        if element['tag'] == 'h3' and is_within(element, concern_closings[0])]
    assert len(closing_headings) == 1, 'Expected one concern-closing heading.'
    closing_lines = [element for element in scan.elements
                     if element['parent'] is closing_headings[0]]
    assert all(element['tag'] == 'span' and has_class(element, 'heading-line') for element in closing_lines) \
        and [compact(element['text']) for element in closing_lines] == [
            'その重さを、', 'いつものことにしないために。'
        ] and compact(closing_headings[0]['text']) == HOME_COPY['concerns'][1], \
        'The concern-closing heading must preserve its two explicit supplied lines.'
    daytime_scenes = [element for element in scan.elements if has_class(element, 'daytime-scenes')]
    assert len(daytime_scenes) == 1, 'Expected one weekday-daytime scene section.'
    daytime = daytime_scenes[0]
    main = next(element for element in scan.elements if element['attrs'].get('id') == 'main')
    concern_section = next(element for element in scan.elements if element['attrs'].get('id') == 'concerns')
    assert daytime['tag'] == 'section' and has_class(daytime, 'section') \
        and daytime['attrs'].get('id') == 'daytime' and daytime['parent'] is main \
        and daytime['attrs'].get('aria-labelledby') == 'daytime-title' \
        and not is_within(daytime, concern_section), \
        'The weekday-daytime section must stand directly within main, outside the gray concern section.'
    daytime_contents = [element for element in scan.elements
                        if has_class(element, 'daytime-content') and element['parent'] is daytime]
    assert len(daytime_contents) == 1 and daytime_contents[0]['tag'] == 'div' \
        and has_class(daytime_contents[0], 'wrap'), 'Wrap the independent daytime section content consistently.'
    daytime_headings = [element for element in scan.elements
                        if element['tag'] == 'h2' and is_within(element, daytime_contents[0])]
    assert len(daytime_headings) == 1 and daytime_headings[0]['attrs'].get('id') == 'daytime-title' \
        and compact(daytime_headings[0]['text']) == HOME_COPY['daytime'][0], \
        'The independent daytime section must retain its supplied, labelled h2 heading.'
    daytime_buttons = [anchor for anchor in scan.anchors if is_within(anchor, daytime_scenes[0])]
    assert len(daytime_buttons) == 1 and has_class(daytime_buttons[0], 'daytime-plan-button') \
        and not has_class(daytime_buttons[0], 'text-link') \
        and daytime_buttons[0]['attrs'].get('href') == '#price' \
        and compact(daytime_buttons[0]['text']) == '平日デイタイムプランを見る', \
        'The weekday-daytime block needs its dedicated button and existing pricing route.'
    for index, concern in enumerate(concerns):
        for phrase in HOME_COPY['concerns'][2 + index * 2:4 + index * 2]:
            assert compact([phrase]) in compact(concern['text']), \
                f'Concern card {index + 1} differs from supplied copy: {phrase}'
        images = [element for element in scan.elements
                  if element['tag'] == 'img' and is_within(element, concern)]
        assert not images, f'Concern card {index + 1} must omit its illustration as requested.'
    strengths = [element for element in scan.elements if has_class(element, 'feature')]
    assert len(strengths) == 3, 'Expected three supplied strength cards.'
    for index, strength in enumerate(strengths):
        for phrase in HOME_COPY['method'][1 + index * 2:3 + index * 2]:
            assert compact([phrase]) in compact(strength['text']), \
                f'Strength card {index + 1} differs from supplied copy: {phrase}'
    method = next(element for element in scan.elements if element['attrs'].get('id') == 'method')
    method_headings = [element for element in scan.elements
                       if element['tag'] == 'h2' and is_within(element, method)]
    assert len(method_headings) == 1 and compact(method_headings[0]['text']) == compact([HOME_COPY['method'][0]]), \
        'The strength heading must remove the separator and keep the supplied wording.'
    assert not any(has_class(element, 'next-step') and is_within(element, method)
                   for element in scan.elements), 'Remove the training upsell from the strength section.'
    for region in section_order:
        if region != 'faq':
            assert 'トレーニング' not in compact(scan.regions[region]), \
                f'Training-plan guidance must remain only in the FAQ, not #{region}.'

    campaign_ctas = [anchor for anchor in scan.anchors if has_class(anchor, 'cta-fixed')]
    cta_positions = ('hero', 'intro', 'price', 'bottom', 'sticky')
    assert Counter(anchor['attrs'].get('data-position') for anchor in campaign_ctas) == Counter(cta_positions), \
        'Expected one shared gold CTA in each hero, introduction, pricing, bottom and floating position.'
    for anchor in campaign_ctas:
        position = anchor['attrs']['data-position']
        expected_route = store['reserve'] if store else '#locations'
        assert anchor['attrs'].get('href') == expected_route \
            and compact(anchor['text']).endswith('初回体験予約'), \
            f'Campaign CTA {position} must preserve its route and supplied reservation label.'
        main_labels = [element for element in scan.elements
                       if is_within(element, anchor) and has_class(element, 'cta-fixed__main')]
        assert len(main_labels) == 1 and compact(main_labels[0]['text']) == '初回体験予約', \
            f'Campaign CTA {position} has the wrong main label.'
        top_labels = [element for element in scan.elements
                      if is_within(element, anchor) and has_class(element, 'cta-fixed__top')]
        assert len(top_labels) == 1 and '初回60分' in compact(top_labels[0]['text']) \
            and '10/31まで' in compact(top_labels[0]['text']) \
            and has_amount(compact(top_labels[0]['text']), 1000), \
            f'Campaign CTA {position} must show the trial duration, deadline and price in its top frame.'
        top_deadlines = [element for element in scan.elements
                         if element['tag'] == 'time' and is_within(element, top_labels[0])]
        assert len(top_deadlines) == 1, f'Campaign CTA {position} needs one deadline in its top frame.'
        banner = anchor['parent']
        while banner is not None and not has_class(banner, 'campaign-banner'):
            banner = banner['parent']
        assert banner is not None, 'Each trial button must belong to its shared banner.'
        descriptions = [element for element in scan.elements
                        if is_within(element, banner) and has_class(element, 'campaign-banner-description')]
        assert len(descriptions) == 1 and compact(descriptions[0]['text']) == '体組成・姿勢診断付き' \
            and not is_within(descriptions[0], anchor), \
            f'Campaign CTA {position} must retain the diagnosis description beside its button.'
    deadlines = [element for element in scan.elements if element['tag'] == 'time']
    assert len(deadlines) == len(cta_positions) and all(
        element['attrs'].get('datetime') == '2026-10-31'
        and compact(element['text']) == '10/31まで' for element in deadlines
    ), 'Campaign deadline must remain fixed at October 31, 2026.'

    price = compact(scan.regions['price'])
    check_session(scan)
    check_intro(scan)
    check_pricing(scan)
    check_trainers(scan, page)
    check_flow_and_faq(scan)
    check_store_identity(scan, page, store)
    check_store_navigation(scan, page)
    assert has_amount(text, 1000), 'Missing first-trial price: 1,000.'
    assert re.search(r'(?:[¥￥]0(?!\d)|(?<![\d,])0円)', price), \
        'Missing the free enrollment fee: 0 yen.'
    assert not has_amount(price, 33000) and '体験当日のご入会' not in price, \
        'Do not retain the previous enrollment fee or same-day-only restriction.'
    assert '30分' in text and '月額' in price, '30-minute / monthly service terms are missing.'


def check_session(scan):
    session = next(element for element in scan.elements if element['attrs'].get('id') == 'session')
    headings = [element for element in scan.elements
                if element['tag'] == 'h2' and is_within(element, session)]
    assert len(headings) == 1, 'Expected one regular-session heading.'
    heading_lines = [element for element in scan.elements if element['parent'] is headings[0]]
    assert all(element['tag'] == 'span' and has_class(element, 'heading-line') for element in heading_lines) \
        and [compact(element['text']) for element in heading_lines] == [
            '30分で、全身を心地よく', 'Dr.coreのアプローチ'
        ] and compact(headings[0]['text']) == HOME_COPY['session'][1], \
        'The regular-session heading must preserve its two explicit supplied lines.'
    cards = [element for element in scan.elements if has_class(element, 'session-card')
             and is_within(element, session)]
    assert len(cards) == 3, 'Explain the three approaches in the regular 30-minute session.'
    for card, title, keywords in zip(cards, HOME_COPY['session'][2:5],
                                      (('モビリティ',), ('TRX', '器具'), ('ペアストレッチ', 'トレーナー'))):
        headings = [element for element in scan.elements
                    if element['tag'] == 'h3' and is_within(element, card)]
        paragraphs = [element for element in scan.elements
                      if element['tag'] == 'p' and is_within(element, card)]
        assert len(headings) == 1 and compact(headings[0]['text']) == title, \
            'The regular session must preserve the corresponding approach title.'
        assert len(paragraphs) == 1 and all(keyword in compact(paragraphs[0]['text']) for keyword in keywords), \
            'Each session approach needs its explanatory body text.'


def check_intro(scan):
    intro_cards = [element for element in scan.elements if has_class(element, 'first-visit-card')]
    assert len(intro_cards) == 3, 'Expected three concise first-visit introduction cards.'
    for index, card in enumerate(intro_cards, 1):
        phrase, description = HOME_COPY['first-visit'][2 * index:2 * index + 2]
        headings = [element for element in scan.elements
                    if element['tag'] == 'h3' and is_within(element, card)]
        numbers = [element for element in scan.elements if has_class(element, 'intro-step') and is_within(element, card)]
        images = [element for element in scan.elements if element['tag'] == 'img' and is_within(element, card)]
        assert len(headings) == 1 and compact(headings[0]['text']) == compact([phrase]), \
            f'First-visit card {index} does not preserve the supplied title.'
        descriptions = [element for element in scan.elements
                        if element['tag'] == 'p' and element['parent'] is card]
        assert len(descriptions) == 1 and compact(descriptions[0]['text']) == compact([description]), \
            f'First-visit card {index} does not preserve the supplied explanation.'
        assert len(numbers) == 1 and compact(numbers[0]['text']) == f'{index:02}' \
            and len(images) == 1, f'First-visit card {index} needs its sequence number and visual.'


def check_pricing(scan):
    data = json.loads((ROOT.parent / 'data/recovery-plans.json').read_text(encoding='utf-8'))
    expected_plans = ((1, 6000), (2, 5250), (4, 5000), (8, 4750))
    assert data['session_minutes'] == 30 and data['enrollment_fee'] == 0, \
        'The supplied session duration or enrollment fee changed.'
    assert data['other_hours_surcharge'] == 1000, 'Other-hours surcharge must be 1,000 yen per session.'
    assert tuple((plan['sessions'], plan['per_session']) for plan in data['plans']) == expected_plans, \
        'The existing plan counts or base per-session rates changed.'
    groups = [element for element in scan.elements
              if element['tag'] == 'article' and element['attrs'].get('data-rate-plan')]
    assert [element['attrs']['data-rate-plan'] for element in groups] == ['1', '2'], \
        'Display exactly two rate plans, with the weekday plan first.'
    for number, group in enumerate(groups, 1):
        labels = [element for element in scan.elements
                  if has_class(element, 'rate-plan-label') and is_within(element, group)]
        conditions = [element for element in scan.elements
                      if has_class(element, 'rate-plan-condition') and is_within(element, group)]
        name, condition = (
            ('平日デイタイムプラン', '平日10:00〜15:00') if number == 1 else
            ('レギュラープラン', '平日10:00〜15:00以外・土日祝')
        )
        assert len(labels) == 1 and compact(labels[0]['text']) == name \
            and len(conditions) == 1 and compact(conditions[0]['text']) == condition, \
            f'Rate plan {number} must show its corresponding name and time condition.'
        tables = [element for element in scan.elements
                  if element['tag'] == 'table' and is_within(element, group)]
        assert len(tables) == 1, f'Rate plan {number} must have one comparison table.'
        rows = [element for element in scan.elements
                if element['tag'] == 'tr' and is_within(element, tables[0])
                and element['parent']['tag'] == 'tbody']
        assert len(rows) == 4, f'Rate plan {number} must show all four monthly plans.'
        surcharge = 1000 if number == 2 else 0
        for row, plan in zip(rows, data['plans']):
            sessions = plan['sessions']
            per_session = plan['per_session'] + surcharge
            monthly = sessions * per_session
            for field, expected in (('sessions', sessions), ('monthly', monthly), ('per-session', per_session)):
                assert row['attrs'].get(f'data-{field}') == str(expected), \
                    f'Rate plan {number}, {sessions} sessions: incorrect {field}; expected {expected}.'
            cells = [element for element in scan.elements if element['parent'] is row
                     and element['tag'] in {'th', 'td'}]
            assert len(cells) == 3 and cells[0]['tag'] == 'th' \
                and cells[0]['attrs'].get('scope') == 'row', \
                f'Rate plan {number}, {sessions} sessions: expected an accessible row heading and two prices.'
            assert compact([plan['name']]) in compact(cells[0]['text']) \
                and f'月{sessions}回' in compact(cells[0]['text']), \
                f'Rate plan {number}, {sessions} sessions: wrong plan name or session count.'
            for cell, amount, label in ((cells[1], monthly, 'monthly'), (cells[2], per_session, 'per-session')):
                assert compact(cell['text']).replace(',', '') == f'{amount}円', \
                    f'Rate plan {number}, {sessions} sessions: displayed {label} price must be {amount:,} yen.'
            assert not re.search(r'[〜～]', compact(row['text'])), \
                f'Rate plan {number}, {sessions} sessions: remove starting-price marks only from table prices.'
    price = next(element for element in scan.elements if element['attrs'].get('id') == 'price')
    enrollments = [element for element in scan.elements
                   if element['tag'] == 'article' and has_class(element, 'enrollment-plan')
                   and is_within(element, price)]
    assert len(enrollments) == 1, 'Show the enrollment fee in one separate plan card.'
    assert not any(has_class(element, 'enrollment-base') and is_within(element, price)
                   for element in scan.elements), 'Remove the enrollment fee from the pricing introduction.'
    assert has_class(enrollments[0], 'enrollment-plan--free'), \
        'The enrollment card must show the free self-weight stretch terms.'
    fees = [element for element in scan.elements
            if has_class(element, 'enrollment-free-price') and is_within(element, enrollments[0])]
    assert len(fees) == 1 and compact(fees[0]['text']) == '入会金0円', \
        'Display the confirmed free enrollment fee.'
    assert 'すべての自重ストレッチプランが対象です。' in compact(enrollments[0]['text']), \
        'The free enrollment terms must clearly apply to self-weight stretch plans.'
    check_pay_as_you_go(scan, price, checked_payg_prices(data))


def checked_payg_prices(data):
    prices = data.get('pay_as_you_go')
    assert isinstance(prices, dict) and all(field in prices for field, _ in PAYG_OPTIONS), \
        'Both pay-as-you-go time bands must exist in the shared price data.'
    for field, _ in PAYG_OPTIONS:
        value = prices[field]
        assert value is None or (type(value) is int and value > 0), \
            f'Pay-as-you-go {field} must be a confirmed positive integer or null while pending.'
    assert prices.get('unconfirmed_price_display') in {None, 'contact_store'}, \
        'Unconfirmed pay-as-you-go prices require the explicit contact_store display mode or remain pending.'
    return prices


def check_pay_as_you_go(scan, price_region, prices):
    plans = [element for element in scan.elements
             if has_class(element, 'payg-plan') and is_within(element, price_region)]
    assert len(plans) == 1 and '都度払い' in compact(plans[0]['text']) \
        and '1回30分' in compact(plans[0]['text']), 'Show one separate 30-minute pay-as-you-go plan.'
    options = [element for element in scan.elements
               if has_class(element, 'payg-options') and is_within(element, plans[0])]
    assert len(options) == 1, 'Pay-as-you-go must have one time-band comparison.'
    cards = [element for element in scan.elements if element['parent'] is options[0]]
    assert len(cards) == 2, 'Show both pay-as-you-go time bands.'
    for card, (field, label) in zip(cards, PAYG_OPTIONS):
        headings = [element for element in scan.elements
                    if element['tag'] == 'h4' and is_within(element, card)]
        figures = [element for element in scan.elements
                   if has_class(element, 'payg-price') and is_within(element, card)]
        pending = [element for element in scan.elements
                   if 'data-pending-content' in element['attrs'] and is_within(element, card)]
        inquiries = [element for element in scan.elements
                     if 'data-price-inquiry' in element['attrs'] and is_within(element, card)]
        assert len(headings) == 1 and compact(headings[0]['text']) == label, \
            f'Pay-as-you-go {field} must show its corresponding time band.'
        assert len(figures) == 1, f'Pay-as-you-go {field} needs exactly one price, inquiry or pending figure.'
        if prices[field] is None:
            if prices.get('unconfirmed_price_display') == 'contact_store':
                assert not pending and len(inquiries) == 1 and inquiries[0] is figures[0] \
                    and figures[0]['tag'] == 'p' and has_class(figures[0], 'payg-price--inquiry') \
                    and not has_class(figures[0], 'payg-price--pending') \
                    and figures[0]['attrs'].get('data-price-inquiry') == field \
                    and compact(figures[0]['all_text']) == '料金は店舗へお問い合わせください', \
                    f'Unconfirmed pay-as-you-go {field} must show its corresponding public store-inquiry message.'
            else:
                assert not inquiries and len(pending) == 1 and pending[0] is figures[0] \
                    and has_class(figures[0], 'payg-price--pending') \
                    and not has_class(figures[0], 'payg-price--inquiry') \
                    and compact(figures[0]['text']) == '料金確認中', \
                    f'Unconfirmed pay-as-you-go {field} must retain its explicit pending marker.'
        else:
            assert type(prices[field]) is int and prices[field] > 0, f'Invalid confirmed price: {field}.'
            assert not pending and not inquiries and not has_class(figures[0], 'payg-price--pending') \
                and not has_class(figures[0], 'payg-price--inquiry') \
                and compact(figures[0]['text']).replace(',', '') == f'{prices[field]}円／回', \
                f'Confirmed pay-as-you-go {field} must display exactly {prices[field]:,} yen per visit.'


def check_trainers(scan, page=PAGE):
    trainers = json.loads((ROOT.parent / 'data/trainers.json').read_text(encoding='utf-8'))
    assert tuple((trainer['id'], trainer['label']) for trainer in trainers) == TRAINER_PROFILES, \
        'Trainer identities or their source-confirmed order changed.'
    cards = [element for element in scan.elements if has_class(element, 'trainer-card')]
    assert tuple(card['attrs'].get('data-trainer-id') for card in cards) == tuple(
        profile[0] for profile in TRAINER_PROFILES
    ), 'Expected the four corresponding trainer cards.'
    for trainer, card in zip(trainers, cards):
        headings = [element for element in scan.elements
                    if element['tag'] == 'h3' and is_within(element, card)]
        images = [element for element in scan.elements
                  if element['tag'] == 'img' and is_within(element, card)]
        assert len(headings) == 1 and compact(headings[0]['text']) == trainer['label'], \
            f'Trainer {trainer["id"]} has the wrong name label.'
        assert len(images) == 1 and local_path(images[0]['attrs'].get('src', ''), page) == ROOT / trainer['photo'], \
            f'Trainer {trainer["id"]} uses the wrong portrait or a remote image.'
        assert images[0]['attrs'].get('alt') == trainer['label'], \
            f'Trainer {trainer["id"]} portrait has the wrong accessible name.'


def check_flow_and_faq(scan):
    flow = next(element for element in scan.elements if element['attrs'].get('id') == 'flow')
    steps = [element for element in scan.elements
             if element['tag'] == 'li' and has_class(element, 'recovery-flow-step') and is_within(element, flow)]
    assert len(steps) == 5, 'Expected five sequential experience steps.'
    assert steps[0]['parent']['tag'] == 'ol' \
        and all(step['parent'] is steps[0]['parent'] for step in steps), \
        'Experience steps must belong to one ordered list.'
    for index, step in enumerate(steps, 1):
        children = [element for element in scan.elements if element['parent'] is step]
        assert len(children) == 3 and has_class(children[0], 'recovery-flow-number') \
            and children[1]['tag'] == 'figure' and has_class(children[1], 'recovery-flow-image') \
            and has_class(children[2], 'recovery-flow-copy'), \
            f'Step {index} must read number, image, then title and explanation in DOM order.'
        assert compact(children[0]['text']) == f'STEP{index:02}', f'Incorrect step number: {index}.'
        images = [element for element in scan.elements
                  if element['tag'] == 'img' and is_within(element, children[1])]
        assert len(images) == 1 and images[0]['attrs'].get('alt', '').strip(), \
            f'Step {index} needs one image describing its content.'
        copy_children = [element for element in scan.elements if element['parent'] is children[2]]
        assert len(copy_children) >= 2 and copy_children[0]['tag'] == 'h3' \
            and copy_children[1]['tag'] == 'p' and compact(copy_children[1]['text']), \
            f'Step {index} must show a title before its explanation.'

    faq = next(element for element in scan.elements if element['attrs'].get('id') == 'faq')
    questions = [element for element in scan.elements if element['tag'] == 'details' and is_within(element, faq)]
    assert len(questions) == 9, 'Expected nine stretch-specific FAQ disclosures.'
    for index, question in enumerate(questions, 1):
        children = [element for element in scan.elements if element['parent'] is question]
        assert children and children[0]['tag'] == 'summary' and compact(children[0]['text']), \
            f'FAQ {index} must start with a native summary for keyboard and screen-reader operation.'
        assert len([element for element in children if element['tag'] == 'summary']) == 1 \
            and any(has_class(element, 'answer') and compact(element['text']) for element in children[1:]), \
            f'FAQ {index} must have one question and a nonempty answer.'
    summaries = [compact(element['text']) for element in scan.elements
                 if element['tag'] == 'summary' and is_within(element, faq)]
    assert any('服装' in question for question in summaries) \
        and any('着替' in question and 'シャワー' in question for question in summaries), \
        'The FAQ must include clothing and changing/shower questions without inferring unconfirmed answers.'
    store_inquiries = [element for element in scan.elements if 'data-store-inquiry' in element['attrs']]
    assert Counter(element['attrs']['data-store-inquiry'] for element in store_inquiries) == \
        Counter(('clothing', 'facilities')), 'Show exactly one public inquiry answer for each unconfirmed facility topic.'
    for field, question_text, answer_text in (
        ('clothing', '服装は？',
         '普段着でのご利用やレンタルウェアについては、ご予約前にご利用店舗へお問い合わせください。'),
        ('facilities', '着替えやシャワーはありますか？',
         '着替えスペース・シャワーのご利用については、ご予約前にご利用店舗へお問い合わせください。'),
    ):
        answer = next(element for element in store_inquiries if element['attrs']['data-store-inquiry'] == field)
        question = answer['parent']
        question_summaries = [element for element in scan.elements
                              if element['tag'] == 'summary' and element['parent'] is question]
        question_answers = [element for element in scan.elements
                            if element['parent'] is question and element['tag'] != 'summary']
        assert has_class(answer, 'answer') and question['tag'] == 'details' and is_within(answer, faq) \
            and len(question_summaries) == 1 and compact(question_summaries[0]['text']) == question_text \
            and len(question_answers) == 1 and question_answers[0] is answer \
            and compact(answer['all_text']) == answer_text \
            and compact(question['text']) == question_text + answer_text \
            and not any('data-pending-content' in element['attrs'] and is_within(element, answer)
                        for element in scan.elements), \
            f'The {field} FAQ must retain its corresponding public store-inquiry copy without facility claims or draft markers.'
    training_questions = [question for question in questions if 'トレーニング' in compact(question['text'])]
    assert len(training_questions) == 1 and all(phrase in compact(training_questions[0]['text']) for phrase in
        ('自重ストレッチだけ', 'ご希望の方に限り', '別のトレーニングプラン')), \
        'Explain the separate training service only for customers who request it in the FAQ.'


def check_store_identity(scan, page, store=None):
    body = next(element for element in scan.elements if element['tag'] == 'body')
    expected_slug = store['slug'] if store else 'all'
    assert body['attrs'].get('data-store') == expected_slug, \
        f'{page.relative_to(ROOT)} has the wrong store identity.'
    assert '準備中' not in compact(body['text']), \
        f'{page.relative_to(ROOT)} still describes its authorized reservation route as unavailable.'
    hero = next(element for element in scan.elements if element['attrs'].get('id') == 'top')
    hero_labels = [element for element in scan.elements
                   if has_class(element, 'hero-label') and is_within(element, hero)]
    if not store:
        assert not hero_labels and 'Dr.coreの自重ストレッチ' not in compact(hero['text']), \
            'Remove the entire top-page hero label while retaining store labels.'
        assert 'access' not in scan.ids, 'The top page must not present one store as its sole access location.'
        return
    assert len(hero_labels) == 1 and hero_labels[0]['tag'] == 'p', \
        f'{store["slug"]} must retain its hero-label paragraph.'
    visual = next(element for element in scan.elements if has_class(element, 'hero-visual'))
    assert is_within(hero_labels[0], visual), \
        f'{store["slug"]} must retain its store label within the first-screen visual.'
    hero_names = [element for element in scan.elements if has_class(element, 'hero-store-name')]
    hero_stations = [element for element in scan.elements if has_class(element, 'hero-store-station')]
    assert len(hero_names) == 1 and is_within(hero_names[0], hero_labels[0]) \
        and store['name'] in compact(hero_names[0]['text']), \
        f'{store["slug"]} must identify the corresponding store in its hero.'
    assert len(hero_stations) == 1 and is_within(hero_stations[0], hero_labels[0]) \
        and store['station'] in compact(hero_stations[0]['text']) \
        and f'徒歩{store["minutes"]}分' in compact(hero_stations[0]['text']), \
        f'{store["slug"]} hero must retain its correct station and walking time.'
    title = next(element for element in scan.elements if element['tag'] == 'title')
    assert store['name'] in compact(title['text']) and 'Recovery' in compact(title['text']) \
        and store['station'] in compact(title['text']) \
        and f'徒歩{store["minutes"]}分' in compact(title['text']), \
        f'{store["slug"]} page title must identify the Recovery store.'
    for field in ('description', 'og:title', 'og:description'):
        metadata_text = compact([scan.metadata.get(field, '')])
        assert store['name'] in metadata_text and store['station'] in metadata_text \
            and f'徒歩{store["minutes"]}分' in metadata_text, \
            f'{store["slug"]} {field} must identify its corresponding store, station and walking time.'
    access = next(element for element in scan.elements if element['attrs'].get('id') == 'access')
    access_text = compact(access['text'])
    for field in ('name', 'address', 'building', 'station'):
        assert compact([store[field]]) in access_text, \
            f'{store["slug"]} access information has the wrong {field}.'
    assert f'徒歩{store["minutes"]}分' in access_text, \
        f'{store["slug"]} access information has the wrong walking time.'
    images = [element for element in scan.elements
              if element['tag'] == 'img' and is_within(element, access)]
    assert len(images) == 1 and local_path(images[0]['attrs'].get('src', ''), page) == ROOT / store['photo'], \
        f'{store["slug"]} access section must use its corresponding local store photo.'
    assert any(local_path(anchor['attrs'].get('href', ''), page) == PAGE for anchor in scan.anchors), \
        f'{store["slug"]} must link back to the Recovery top page.'


def check_store_navigation(scan, page):
    locations = next(element for element in scan.elements if element['attrs'].get('id') == 'locations')
    cards = [element for element in scan.elements if has_class(element, 'studio')
             and is_within(element, locations)]
    assert len(cards) == 2, 'Each Recovery LP must retain both store-selection cards.'
    for store, card in zip(load_stores(), cards):
        card_text = compact(card['text'])
        for field in ('name', 'address', 'building', 'station'):
            assert compact([store[field]]) in card_text, \
                f'Store-selection card {store["slug"]} has the wrong {field}.'
        assert f'徒歩{store["minutes"]}分' in card_text, \
            f'Store-selection card {store["slug"]} has the wrong walking time.'
        images = [element for element in scan.elements
                  if element['tag'] == 'img' and is_within(element, card)]
        assert len(images) == 1 and local_path(images[0]['attrs'].get('src', ''), page) == ROOT / store['photo'], \
            f'Store-selection card {store["slug"]} must use the corresponding local photo.'
        destination = ROOT / 'gyms' / store['slug'] / 'index.html'
        assert any(is_within(anchor, card) and local_path(anchor['attrs'].get('href', ''), page) == destination
                   for anchor in scan.anchors), \
            f'Store-selection card {store["slug"]} must link to its Recovery LP.'


def check_voice_photo(scan, container, voice, page):
    slots = [element for element in scan.elements if is_within(element, container)
             and (has_class(element, 'voice-photo-placeholder') or has_class(element, 'voice-photo'))]
    slug = voice['slug']
    assert len(slots) == 1, f'Voice {slug} needs exactly one replaceable photo frame.'
    images = [element for element in scan.elements
              if element['tag'] == 'img' and is_within(element, slots[0])]
    photo = voice.get('photo')
    if photo:
        assert has_class(slots[0], 'voice-photo') and len(images) == 1, \
            f'Voice {slug} must show its supplied photo in the photo frame.'
        assert local_path(images[0]['attrs'].get('src', ''), page) == (ROOT / photo).resolve(), \
            f'Voice {slug} must use the corresponding local photo asset.'
        assert images[0]['attrs'].get('alt', '').strip(), f'Voice {slug} photo needs an accessible description.'
        if voice.get('photo_alt'):
            assert images[0]['attrs']['alt'] == voice['photo_alt'], \
                f'Voice {slug} photo must preserve its supplied description.'
    else:
        assert has_class(slots[0], 'voice-photo-placeholder') and not images \
            and slots[0]['attrs'].get('role') == 'img' \
            and voice['name'] in slots[0]['attrs'].get('aria-label', ''), \
            f'Voice {slug} must retain a neutral, named placeholder until a photo is supplied.'
    return slots[0]


def check_voice_results_note(scan, container):
    notes = [element for element in scan.elements
             if has_class(element, 'voice-results-note') and is_within(element, container)]
    assert len(notes) == 1 and compact(notes[0]['text']) == VOICE_RESULTS_NOTE, \
        'Customer voices must carry the personal-impressions and individual-differences note.'


def check_voices(home, page=PAGE, verify_articles=True, report_prefix=''):
    source = ROOT.parent / 'data/voices.json'
    assert source.is_file(), 'Missing shared voice data.'
    voices = json.loads(source.read_text(encoding='utf-8'))
    assert isinstance(voices, list), 'Voice data must be an array.'
    assert tuple(voice['slug'] for voice in voices) == VOICE_IDS, 'Voice cards must remain ordered A, D, C.'
    assert all(voice.get('is_sample') is True for voice in voices), \
        'These authored manuscripts must remain samples until actual interviews are confirmed.'
    voice_section = next(element for element in home.elements if element['attrs'].get('id') == 'voices')
    check_voice_results_note(home, voice_section)
    cards = [element for element in home.elements if has_class(element, 'voice-card')]
    assert tuple(card['attrs'].get('data-voice-id') for card in cards) == VOICE_IDS, \
        'The homepage must contain the corresponding A / D / C cards.'
    tracks = [element for element in home.elements if element['attrs'].get('id') == 'voice-track']
    assert len(tracks) == 1 and tracks[0]['attrs'].get('tabindex') == '0' \
        and all(is_within(card, tracks[0]) for card in cards), \
        'All voice cards must be in one keyboard-accessible scroll region.'
    for class_name in ('voice-prev', 'voice-next'):
        buttons = [element for element in home.elements
                   if element['tag'] == 'button' and has_class(element, class_name)]
        assert len(buttons) == 1 and buttons[0]['attrs'].get('aria-controls') == 'voice-track' \
            and buttons[0]['attrs'].get('aria-label') and buttons[0]['attrs'].get('type') == 'button', \
            'Voice navigation must have named buttons controlling the scroll region.'

    for voice, card in zip(voices, cards):
        slug = voice['slug']
        profile = VOICE_PROFILES[slug]
        assert tuple(voice[field] for field in ('name', 'age', 'attribute', 'theme')) == profile, \
            f'Voice {slug} profile differs from supplied information.'
        card_text = compact(card['text'])
        editorial_labels = [element for element in home.elements
                            if has_class(element, 'voice-editorial-label') and is_within(element, card)]
        if slug == 'a':
            assert voice.get('editorial_label') == DAYTIME_VOICE_LABEL \
                and '昼' in voice.get('card_title', ''), \
                'The A sample must identify its weekday-daytime use scenario as an editorial image.'
            assert len(editorial_labels) == 1 and compact(editorial_labels[0]['text']) == DAYTIME_VOICE_LABEL, \
                'The A card must display the pending interview/photo label from its sample data.'
        else:
            assert not editorial_labels, 'Do not attach the A daytime-image label to other customer cards.'
        for phrase in profile[:2]:
            assert compact([phrase]) in card_text, f'Wrong identity/theme on voice card {slug}: {phrase}'
        identity = [element for element in home.elements
                    if is_within(element, card) and has_class(element, 'voice-identity')]
        assert len(identity) == 1 and compact(identity[0]['text']) == f'{profile[0]}｜{profile[1]}', \
            f'Voice card {slug} must show only the supplied name and age.'
        assert '掲載イメージ（サンプル）' not in card_text \
            and not any(is_within(element, card) and any(has_class(element, name) for name in
                        ('voice-theme', 'voice-concerns')) for element in home.elements), \
            f'Voice card {slug} must omit the removed presentation elements.'
        for field, class_name in (('card_title', 'voice-card-title'), ('card_intro', 'voice-card-intro')):
            if voice.get(field):
                elements = [element for element in home.elements
                            if is_within(element, card) and has_class(element, class_name)]
                assert len(elements) == 1 and compact(elements[0]['text']) == compact([voice[field]]), \
                    f'Card {slug} does not preserve the supplied {field}.'
                if field == 'card_title':
                    lines = [element for element in home.elements
                             if element['tag'] == 'span' and element['parent'] is elements[0]]
                    assert len(lines) == 2 and [compact(line['text']) for line in lines] == \
                        [compact([line]) for line in voice[field].splitlines()], \
                        f'Card {slug} must preserve both complete title lines.'
        links = [anchor for anchor in home.anchors if is_within(anchor, card)
                 and has_class(anchor, 'voice-read-more')]
        assert len(links) == 1, f'Expected one article link on voice card {slug}.'
        photo_slot = check_voice_photo(home, card, voice, page)
        assert has_class(links[0], 'voice-card-link') and is_within(photo_slot, links[0]) \
            and is_within(identity[0], links[0]) \
            and all(is_within(element, links[0]) for element in home.elements
                    if is_within(element, card) and any(has_class(element, name) for name in
                        ('voice-card-title', 'voice-card-intro'))), \
            f'Voice card {slug} must link its photo and all presentation content to the article.'
        article_path = ROOT / 'voices' / slug / 'index.html'
        assert local_path(links[0]['attrs']['href'], page) == article_path, \
            f'Voice {slug} URL does not resolve to its article.'
        if not verify_articles:
            continue
        article = check_page(article_path)
        bodies = [element for element in article.elements if element['tag'] == 'body']
        assert len(bodies) == 1 and bodies[0]['attrs'].get('data-voice-id') == slug, \
            f'Wrong voice identity on article {slug}.'
        article_text = compact(bodies[0]['text'])
        article_cards = [element for element in article.elements
                         if element['tag'] == 'article' and has_class(element, 'voice-article')]
        assert len(article_cards) == 1, f'Expected one main voice article: {slug}.'
        check_voice_photo(article, article_cards[0], voice, article_path)
        check_voice_results_note(article, article_cards[0])
        for phrase in profile:
            assert compact([phrase]) in article_text, f'Wrong identity/theme on article {slug}: {phrase}'
        heading = next(element for element in article.elements if element['tag'] == 'h1')
        if voice.get('article_title'):
            assert compact(heading['text']) == compact([voice['article_title']]), \
                f'Article {slug} does not preserve the supplied title.'
        else:
            assert voice['name'] in compact(heading['text']), f'Wrong article title identity: {slug}.'
        if voice.get('is_sample', True):
            notices = [element for element in article.elements if has_class(element, 'voice-sample-notice')]
            assert len(notices) == 1 and '掲載イメージ（サンプル）' in compact(notices[0]['text']), \
                f'Missing explicit sample notice on article {slug}.'
            assert 'noindex' in {token.strip().lower() for token in article.metadata.get('robots', '').split(',')}, \
                f'Sample article {slug} must remain noindex.'
        pending = [element for element in article.elements if has_class(element, 'voice-manuscript-pending')]
        supplied_paragraphs = voice.get('paragraphs')
        if supplied_paragraphs:
            assert not pending, f'Article {slug} still shows a pending block despite supplied manuscript.'
            article_bodies = [element for element in article.elements if has_class(element, 'voice-article-body')]
            assert len(article_bodies) == 1, f'Expected one manuscript body on article {slug}.'
            paragraphs = [element for element in article.elements
                          if element['tag'] == 'p' and is_within(element, article_bodies[0])]
            assert [compact(element['text']) for element in paragraphs] == \
                [compact([paragraph]) for paragraph in supplied_paragraphs], \
                f'Article {slug} changed, omitted, truncated, or reordered supplied paragraphs.'
        else:
            assert len(pending) == 1 and '原稿' in compact(pending[0]['text']) \
                and '未提供' in compact(pending[0]['text']), f'Missing manuscript-pending disclosure: {slug}.'
        assert '../../#voices' in article.links, f'Missing return link on article {slug}.'
        ctas = [anchor for anchor in article.anchors if anchor['attrs'].get('href') == '../../#trial']
        assert ctas and all(compact(anchor['text']) == '初回体験予約' for anchor in ctas), \
            f'Wrong reservation CTA on article {slug}.'
        print(f'{report_prefix}voices/{slug}/index.html: OK — corresponding identity, manuscript state, assets and links.')


def check_publication(pages, expected_origin=''):
    canonical_urls = {}
    for page, scan in pages.items():
        canonicals = [element['attrs'].get('href', '') for element in scan.elements
                      if element['tag'] == 'link'
                      and 'canonical' in element['attrs'].get('rel', '').split()]
        assert len(canonicals) <= 1, f'{page.relative_to(ROOT)} has duplicate canonicals.'
        canonical_urls[page] = canonicals[0] if canonicals else ''
    origin = expected_origin.rstrip('/')
    if not origin and canonical_urls[PAGE]:
        parsed = urlparse(canonical_urls[PAGE])
        assert parsed.scheme in {'https', 'http'} and parsed.netloc \
            and parsed.path == '/' and not parsed.query and not parsed.fragment, \
            'The top canonical must identify the Recovery publication origin.'
        origin = canonical_urls[PAGE].rstrip('/')
    expected_urls = []
    for page, scan in pages.items():
        relative = page.relative_to(ROOT).parent.as_posix()
        path = '/' if relative == '.' else f'/{relative}/'
        expected_url = origin + path if origin else ''
        assert canonical_urls[page] == expected_url, \
            f'{page.relative_to(ROOT)} has the wrong canonical; expected {expected_url or "none"}.'
        if origin:
            expected_urls.append(expected_url)
            assert scan.metadata.get('og:url') == expected_url, \
                f'{page.relative_to(ROOT)} has the wrong Open Graph URL.'
            image = scan.metadata.get('og:image', '')
            hero_photos = [element for element in scan.elements if has_class(element, 'hero-photo')]
            hero_images = [element for element in scan.elements if element['tag'] == 'img'
                           and len(hero_photos) == 1 and is_within(element, hero_photos[0])]
            assert len(hero_images) == 1, 'Each published LP must retain its approved hero photo.'
            hero_path = local_path(hero_images[0]['attrs'].get('src', ''), page)
            assert hero_path is not None and hero_path.is_file(), 'The hero photo must be a local Recovery asset.'
            assert image == origin + '/' + hero_path.relative_to(ROOT).as_posix(), \
                f'{page.relative_to(ROOT)} Open Graph image must match its approved hero photo.'
        assert 'noindex' not in scan.metadata.get('robots', '').lower(), \
            f'The public Recovery LP must remain indexable: {page.relative_to(ROOT)}'
    sitemap = ROOT / 'sitemap.xml'
    assert sitemap.is_file(), 'Missing Recovery sitemap.'
    sitemap_tree = ET.parse(sitemap)
    assert sitemap_tree.getroot().tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}urlset', \
        'The sitemap must use the standard sitemap namespace.'
    sitemap_urls = [element.text or '' for element in
                    sitemap_tree.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/'
                                         '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    assert Counter(sitemap_urls) == Counter(expected_urls), \
        'The sitemap must contain exactly the top and two store LPs when an origin is supplied.'
    assert not any('/voices/' in url for url in sitemap_urls), 'Sample articles must stay out of the sitemap.'
    robots = (ROOT / 'robots.txt').read_text(encoding='utf-8')
    assert re.search(r'^User-agent:\s*\*\s*$', robots, re.M) \
        and re.search(r'^Allow:\s*/\s*$', robots, re.M), 'Allow crawling of the Recovery LPs.'
    disallows = re.findall(r'^Disallow:\s*(\S*)\s*$', robots, re.M)
    assert not any(rule in {'/', '/gyms', '/gyms/', '/gyms/*'} for rule in disallows), \
        'Do not block the public Recovery store pages in robots.txt.'
    sitemap_lines = re.findall(r'^Sitemap:\s*(\S+)\s*$', robots, re.M)
    assert sitemap_lines == ([origin + '/sitemap.xml'] if origin else []), \
        'robots.txt must point to the corresponding publication sitemap.'


def check_pending_content(allow_pending_content=False):
    data = json.loads((ROOT.parent / 'data/recovery-plans.json').read_text(encoding='utf-8'))
    prices = checked_payg_prices(data)
    pending_prices = [field for field, _ in PAYG_OPTIONS
                      if prices[field] is None and prices.get('unconfirmed_price_display') != 'contact_store']
    pending_markers = []
    for page in sorted(ROOT.rglob('*.html')):
        scan = Scan()
        scan.feed(page.read_text(encoding='utf-8'))
        pending_markers.extend(page for element in scan.elements
                               if 'data-pending-content' in element['attrs'])
    description = (f'{len(pending_markers)} data-pending-content elements; '
                   f'null pay_as_you_go prices: {", ".join(pending_prices) or "none"}')
    assert allow_pending_content or not (pending_markers or pending_prices), (
        f'Publication blocked by pending content ({description}). '
        'Use --allow-pending-content only for local DRAFT verification.'
    )
    if allow_pending_content:
        print(f'DRAFT — pending content allowed for local checks only: {description}.')
    return len(pending_markers), len(pending_prices)


def main(expected_origin='', allow_pending_content=False):
    pending_markers, pending_prices = check_pending_content(allow_pending_content)
    report_prefix = 'DRAFT — ' if allow_pending_content else ''
    stores = load_stores()
    pages = {PAGE: check_page(PAGE)}
    check_home(pages[PAGE], PAGE)
    check_voices(pages[PAGE], PAGE, report_prefix=report_prefix)
    for store in stores:
        page = ROOT / 'gyms' / store['slug'] / 'index.html'
        scan = check_page(page)
        pages[page] = scan
        check_home(scan, page, store)
        check_voices(scan, page, verify_articles=False)
    check_publication(pages, expected_origin)
    for page, scan in pages.items():
        print(f'{report_prefix}{page.relative_to(ROOT)}: OK — {len(scan.links)} links, {len(scan.assets)} assets, '
              f'{len(scan.ids)} unique IDs; corresponding Recovery copy, reservation route and prices passed.')
    if allow_pending_content:
        print(f'DRAFT checks passed with {pending_markers} pending content elements and {pending_prices} pending prices; '
              'local verification only, not publication approval.')
    else:
        print('Verified three Recovery LPs, the shared sample articles, reservation destinations and publication metadata.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', default='', help='Optional expected publication origin for canonical and sitemap checks.')
    parser.add_argument('--allow-pending-content', action='store_true',
                        help='Allow unconfirmed content only for local DRAFT checks; never use for publication.')
    args = parser.parse_args()
    main(args.origin, args.allow_pending_content)
