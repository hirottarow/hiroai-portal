# -*- coding: utf-8 -*-
"""全ページ共通のヘッダー・フッター（正本はこのファイル1つ）。

build_site.py（トップ・アプリ紹介・既存ページへの差し込み）と
build_benefits_pages.py（銘柄ページ）の両方がここを使う。
prefix はページから見たサイト直下への相対パス（直下のページは ""、benefits/ の中は "../"）。
"""

BASE_URL = "https://hirottarow.github.io/hiroai-portal/"
SITE_NAME = "ひろ@AI遊び場"
CONTACT = "hiro.ai.playground@gmail.com"

# (表示名, アイコン, リンク, 印を付けるキー)
NAV = [
    ("アプリ", "📱", "index.html#apps", "apps"),
    ("株主優待", "🎁", "benefits.html", "benefits"),
    ("ツール", "🧰", "tools.html", "tools"),
    ("記事", "📝", "index.html#articles", "articles"),
]

FOOTER = [
    ("ホーム", "index.html"),
    ("アプリ", "index.html#apps"),
    ("株主優待データベース", "benefits.html"),
    ("便利ツール", "tools.html"),
    ("AIキー取得ガイド", "ai-keys.html"),
    ("利用規約", "terms.html"),
    ("プライバシーポリシー", "privacy.html"),
    ("お問い合わせ", "mailto:" + CONTACT),
]

HEADER_BEGIN = "<!-- site:header -->"
HEADER_END = "<!-- /site:header -->"
FOOTER_BEGIN = "<!-- site:footer -->"
FOOTER_END = "<!-- /site:footer -->"
CSS_MARK = "<!-- site:css -->"


def css_link(prefix=""):
    return f'{CSS_MARK}<link rel="stylesheet" href="{prefix}assets/site.css">'


def header_html(prefix="", current=None):
    links = []
    for label, ico, href, key in NAV:
        cur = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{prefix}{href}"{cur}><span class="sh-ico" aria-hidden="true">{ico}</span>{label}</a>')
    return (
        f'{HEADER_BEGIN}\n'
        f'<div class="sh" role="banner"><div class="sh-in">'
        f'<a class="sh-brand" href="{prefix}index.html"><img src="{prefix}logo.jpg" alt="" width="32" height="32">'
        f'<span>{SITE_NAME}</span></a>'
        f'<div class="sh-nav" role="navigation" aria-label="サイト内">{"".join(links)}</div>'
        f'</div></div>\n{HEADER_END}'
    )


def footer_html(prefix=""):
    links = "".join(
        f'<a href="{href if href.startswith("mailto:") else prefix + href}">{label}</a>' for label, href in FOOTER
    )
    return (
        f'{FOOTER_BEGIN}\n'
        f'<div class="sf" role="contentinfo"><div class="sf-links">{links}</div>'
        f'<div class="sf-copy">&copy; 2026 Hiro @ AI Playground. All Rights Reserved.</div></div>\n'
        f'{FOOTER_END}'
    )
