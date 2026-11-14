# -*- coding: utf-8 -*-
"""サイトの骨組みを作る（2026-11-14 新設）。

    python scripts/build_site.py            # 生成
    python scripts/build_benefits_pages.py  # そのあと必ず（sitemap.xml / sitemap2.xml をここで作り直す）

やること:
1. トップ index.html を作り直す（アプリ一覧・株主優待データベースとツールの入口・記事）
2. アプリごとの紹介ページ app-<slug>.html を作る（文は Play の掲載文から。**ストアに無いことは書かない**）
3. ほかの直下のページに共通ヘッダー・フッター・assets/site.css を差し込む（目印のコメントで囲むので何度流しても同じ）
4. tools.html / benefits.html に書いてある優待の銘柄数を benefits.json の実数にそろえる

画像は img/apps/<slug>/（icon / shot-N は webp、icon.png と og.jpg は共有カード用）。ストアの画像を幅480に縮めて置く。
通知バー・他アプリ・地名などが写った画像は載せない（2026-11-14: つぎコピ5枚目と音ナビ6枚目を外した）。
新しいアプリを足す時は APPS に1件足し、画像を同じ名前で置いて流す。
"""
import glob
import html
import json
import os
import re

from site_common import BASE_URL, SITE_NAME, CONTACT, css_link, header_html, footer_html, \
    HEADER_BEGIN, HEADER_END, FOOTER_BEGIN, FOOTER_END, CSS_MARK

try:
    from PIL import Image
except ImportError:  # 画像の縦横を width/height に書くためだけに使う
    Image = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAY = "https://play.google.com/store/apps/details?id="

# status: "ok"＝ストアで公開中（Play へのボタンを出す） / "wip"＝公開前（ボタンを出さない）
# 文はすべて Play の掲載文（ja-JP）から短くしたもの。掲載文に無い機能・数字を足さないこと。
APPS = [
    {
        "slug": "diy-wood", "name": "DIY Wood Calculator", "sub": "木取り計算",
        "pkg": "com.hiroai.diywoodcalculator", "privacy": "privacy_diy_wood.html",
        "status": "ok", "badge": "Google Play で配信中", "category": "UtilitiesApplication",
        "lead": "パーツの長さと本数を入れるだけ。木材をいちばん無駄なく切る木取り図を自動で計算します。",
        "feats": [
            ("🪵", "木取り図を自動計算", "端材（余り）が最小になる切り出し方を瞬時に出します。"),
            ("⚖️", "歩留まり優先／カット数優先", "目的に合わせて計算の方針を選べます。"),
            ("🪚", "電動工具と手ノコ", "同じ長さを重ねて切る／1本ずつ切るも選べます。"),
            ("📏", "刃の幅とトリム幅", "のこぎりの削れ幅と両端の余白を指定して、実寸で計算します。"),
            ("🎬", "切る順番を再生", "のこぎりのアニメーションで手順を確かめられます。"),
            ("💾", "計算の履歴", "過去の計算を保存して、いつでも再利用できます。"),
        ],
        "steps": ["木材の長さを選ぶ", "パーツの長さと本数を入れる", "木取り図のとおりに切る"],
        "facts": [("💾", "入力したデータは端末内に保存されます。"), ("📢", "広告を表示します。")],
    },
    {
        "slug": "launchlog", "name": "LaunchLog", "sub": "アプリ台帳と起動管理",
        "pkg": "com.hiroai.launchlog", "privacy": "privacy_launchlog.html",
        "status": "ok", "badge": "Google Play で配信中", "category": "UtilitiesApplication",
        "lead": "増えたアプリを台帳で整理。連続起動（ストリーク）と、定期的に開くタイミングをまとめて管理します。",
        "feats": [
            ("🚀", "台帳からすぐ起動", "検索やタブ分けで、目的のアプリをすぐ開けます。"),
            ("🔥", "連続起動を数える", "ログインボーナスや習慣化に。長く開いていない「幽霊アプリ」も抽出します。"),
            ("⏱️", "次の回収までカウントダウン", "「毎日○時」「毎月1日」「○時間ごと」などの周期を表示します。"),
            ("📝", "メモ・URL・関連アプリ", "攻略コードやログインURLを保存。長押しで関連アプリも続けて起動。"),
            ("🧩", "ウィジェットと通知", "フォルダごとの起動ウィジェット。途切れそうな時は通知します。"),
            ("➡️", "「次へ▶」で順番に", "画面の端のボタンで、登録したアプリを順に開けます。"),
        ],
        "steps": ["台帳に入れるアプリを選ぶ", "周期やメモを付ける", "ウィジェットや「次へ▶」から開く"],
        "facts": [
            ("🔒", "登録したデータはスマホの中だけに保存し、開発者のサーバーへは送りません。"),
            ("📢", "広告表示（Google AdMob）のためにインターネットを使います。"),
            ("🔑", "使う許可: 全アプリの一覧・他のアプリの上に表示・アンインストールの依頼。"),
        ],
    },
    {
        "slug": "benefittracker", "name": "株主優待管理", "sub": "BenefitTracker",
        "pkg": "com.hiro.benefittracker", "privacy": "privacy_benefittracker.html",
        "status": "ok", "badge": "Google Play で配信中（日本）", "category": "FinanceApplication",
        "lead": "優待券・優待カード・優待ポイントの残高と期限を1つの画面で。期限が近づいたら通知でお知らせします。",
        "feats": [
            ("🎫", "残高と期限", "円・枚・点で管理。1枚使うごとにワンタップで減らせます。"),
            ("🚦", "期限を3色で", "緊急・注意・安全で一目で分かり、近づくと通知します。"),
            ("📖", "優待辞書から登録", "主要銘柄の内容から選ぶだけ。辞書は自動で最新になります。"),
            ("📷", "バーコード・OCR", "カメラで読み取り。端末内で処理し、画像は保存しません。"),
            ("🧩", "ホーム画面ウィジェット", "期限が近い順の一覧と件数を、開かずに確認できます。"),
            ("💾", "バックアップ", "JSON で書き出し・読み込み。機種変更に備えられます。"),
        ],
        "steps": ["辞書から銘柄を選ぶ", "残高と期限を入れる", "使ったら「1枚使う」"],
        "facts": [
            ("🔒", "登録した優待の情報は端末内に保存し、外部へ送信しません。"),
            ("📢", "広告表示（Google AdMob）のためにインターネットを使います。"),
            ("⚠️", "優待情報は参考です。正確な内容は各企業の公式サイトでご確認ください。"),
        ],
        "extra": ("🎁", "株主優待データベースを見る", "benefits.html"),
    },
    {
        "slug": "designforge", "name": "DesignForge", "sub": "DESIGN.md をつくる",
        "pkg": "com.hiroai.designforge", "privacy": "privacy_designforge.html",
        "status": "ok", "badge": "Google Play で配信中", "category": "DesignApplication",
        "lead": "色・書体・余白の「正解」を DESIGN.md 1枚に。AI にも人にも、同じデザインを渡せます。",
        "feats": [
            ("🎛️", "8項目から自動で導く", "14色・7段階の書体・角丸・余白・部品スタイルまで。"),
            ("👀", "ライブプレビュー", "見出し・ボタン・カード・入力欄に、その場で反映されます。"),
            ("🧰", "12の道具で試着", "TODO リストやタイマーなど、普段使う画面で配色を確かめられます。"),
            ("✅", "コントラスト判定", "WCAG AA の基準を、書き出す前に端末で判定します。"),
            ("📄", "DESIGN.md 形式", "公開されている仕様に準拠。コピー・共有・保存できます。"),
            ("🗂️", "保存して呼び出す", "名前を付けて保存し、あとから読み込めます。"),
        ],
        "steps": ["下敷き（ジャンル別のプリセット）を選ぶ", "主色・書体・余白などを調整", "プレビューで確かめる", "DESIGN.md を書き出す"],
        "facts": [
            ("🔒", "入力したデータはすべて端末内に保存されます。アカウント登録は不要です。"),
            ("📢", "無料で使えます。運営のため広告を表示します。"),
        ],
    },
    {
        "slug": "tsugicopi", "name": "つぎコピ", "sub": "定型文を順番にコピー",
        "pkg": "com.hiroai.tsugicopi", "privacy": "privacy_tsugicopi.html",
        "status": "ok", "badge": "Google Play で配信中", "category": "UtilitiesApplication",
        "lead": "用意した文を上から順に1タップでコピー。最前面の小窓から送るので、配信やチャットの画面を離れずに次の一言を出せます。",
        "feats": [
            ("🔢", "順番・ランダム・重複なし", "出す順番を先に決めておき、当日は送るだけ。"),
            ("🎛️", "6つのスロット", "枠ごとにグループを割り当て。使い切ると次のグループへ。"),
            ("⏱️", "自動送りとゆらぎ", "秒数・件数・待ち時間を決めて自動で。±秒のゆらぎも。"),
            ("✍️", "選んだ文字をそのまま登録", "他のアプリの選択メニュー・共有メニューから追加できます。"),
            ("⏳", "カウントダウン", "決めた秒数のあいだ次のコピーを止め、連投を急ぎすぎない目安に。"),
            ("💾", "バックアップ", "グループ・本文・小窓の設定をまとめて1つのファイルに。"),
        ],
        "steps": ["文をグループにまとめる", "小窓（フローター）を起動", "押してコピー → 貼り付け"],
        "facts": [
            ("🔒", "入力した文は端末の中だけに保存し、どこにも送信しません。他のアプリでコピーされた内容も読みません。"),
            ("📢", "広告はアプリ画面の一番下だけ。小窓には出しません。"),
            ("🌐", "日本語と英語に対応しています。"),
        ],
    },
    {
        "slug": "otonavi", "name": "音ナビ", "sub": "配信・録音の音量バランス",
        "pkg": "com.hiroai.otonavi", "privacy": "privacy_otonavi.html",
        "status": "ok", "badge": "Google Play で配信中", "category": "MultimediaApplication",
        "lead": "声・BGM・効果音を1つずつ測って音量バランスを合わせるメーター。次からは目標線に合わせるだけです。",
        "feats": [
            ("🔊", "出る音を直接測る", "端末が再生している音を測るので、音量つまみやミュートに左右されません。"),
            ("🎤", "入る音も測れる", "マイクやミキサー・オーディオインターフェース経由の音にも対応。"),
            ("🧭", "ステップ案内", "声 → BGM → 効果音 → 全体の順に、何を鳴らすかを案内します。"),
            ("🎯", "目標線とプリセット", "良い音量を目標に登録。映像編集・配信・Web会議などを収録。"),
            ("🪟", "小窓で見続ける", "他のアプリを操作しながら、最前面の小窓でメーターを見られます。"),
            ("📊", "6種類のメーター", "バー・履歴・スペクトラム・低中高・波形・LED/VU。"),
        ],
        "steps": ["測る音（出る音／入る音）を選ぶ", "声・BGM・効果音を1つずつ鳴らす", "良い音量を目標として登録"],
        "facts": [
            ("🔒", "音声は端末の中だけで処理し、送信も録音ファイルの保存もしません。"),
            ("🪟", "小窓は広告を1本見ると24時間使えます。本体のメーターはいつでも制限なく使えます。"),
            ("⚠️", "通話の音声は測れません（Android の仕様）。"),
        ],
    },
    {
        "slug": "numdeck", "name": "NumDeck", "sub": "テンキー＆ボタン盤",
        "pkg": "com.hiroai.bluetoothnumpad", "privacy": "privacy_bluetoothnumpad.html",
        "status": "wip", "badge": "公開準備中", "category": "UtilitiesApplication",
        "lead": "スマホを Bluetooth キーボードに。テンキーの無いノートパソコンへ、半角の数字をそのまま打ち込めます。",
        "feats": [
            ("🔢", "全角にならない数字", "日本語入力がオンのままでも、半角の数字が入ります。"),
            ("💡", "NumLock を実測", "パソコンのランプ情報を読み取り、キーの表示も自動で切り替えます。"),
            ("🧮", "電卓", "その場で計算して、答えだけをパソコンへ送れます。"),
            ("🖱️", "トラックパッド", "クリック・縦横スクロール・端末を傾けるエアマウス。"),
            ("🎛️", "自分の盤面", "キーを並べた盤面を最大5枚まで作れます。"),
            ("🔁", "自動でつなぎ直す", "一度つないだ相手を覚えて、開くとつなぎ直します。"),
        ],
        "steps": ["パソコンと Bluetooth でつなぐ（パソコン側にアプリは不要）", "テンキー・電卓・トラックパッドから選ぶ", "そのまま打つ"],
        "facts": [
            ("🔑", "使う権限は Bluetooth と通知だけ。位置情報・連絡先・写真・マイク・カメラには触れません。"),
            ("🔒", "入力した内容は開発者に送られません。設定と計算履歴は端末内にだけ保存します。"),
            ("📢", "無料で提供するため、画面上部に広告を表示します。"),
            ("📱", "Android 10 以降。接続先は Bluetooth キーボード／マウスを受け付ける機器です。"),
        ],
    },
    {
        "slug": "connectshelf", "name": "ConnectShelf", "sub": "いつもの機器を見守る相棒",
        "pkg": "com.hiroai.btdeviceshelf", "privacy": "privacy_connectshelf.html",
        "status": "wip", "badge": "クローズドテスト中", "category": "UtilitiesApplication",
        "lead": "イヤホンや車がどこで切れたかを覚えておく相棒アプリ。置き忘れても、最後の場所を地図で開けます。",
        "feats": [
            ("📍", "切れた場所を記録", "接続が切れた瞬間の場所を1回だけ記録。地図アプリで開けます（初期はオフ）。"),
            ("🔋", "バッテリー残量", "接続中の機器の残量を表示し、下回ったら通知します。"),
            ("🕒", "接続・切断の履歴", "いつつながり、いつ切れ、そのとき何%だったかを残します。"),
            ("🗂️", "つないだらアプリ棚", "イヤホンなら音楽、車なら地図。機器ごとのアプリ棚が出ます。"),
        ],
        "steps": ["見守る機器を選ぶ", "棚にアプリを並べる", "つないだら棚から開く"],
        "facts": [
            ("📍", "位置は切断の瞬間に1回だけ取ります。記録は端末の中だけに保存し、広告にも使いません。"),
            ("⚠️", "充電ケースの残量は表示できません（Android の仕様）。"),
            ("📢", "無料で提供するため、画面に広告を表示します。"),
        ],
    },
    {
        "slug": "flowclicker", "name": "フロークリッカー", "sub": "見えるオートクリッカー",
        "pkg": "com.hiroai.flowclicker", "privacy": "privacy_flowclicker.html",
        "status": "wip", "badge": "クローズドテスト中", "category": "UtilitiesApplication",
        "lead": "次に押す所と残り秒数が見えるオートクリッカー。毎日の決まった画面操作を手順にしてまかせられます。",
        "feats": [
            ("👁️", "次に押す所が見える", "押す位置の印と、あと何秒で押すかのカウントダウン。"),
            ("🧱", "ブロックで手順を組む", "タップ・長押し・スワイプ・なぞり・待ち・アプリの起動を並べます。"),
            ("⏺️", "操作を記録", "実際に画面を操作して、そのまま手順にできます。"),
            ("📐", "画面の比率で覚える", "画面の大きさが違う端末でも同じ所を押します。"),
            ("🛑", "確実に止まる", "音量キーの長押しで、いつでもすぐに止まります。"),
            ("⏸️", "割り込みで一時停止", "通知や別のアプリが前に出たら止まります（強さは4段階）。"),
        ],
        "steps": ["ブロックを並べて手順を作る", "押す位置を決める", "再生してまかせる"],
        "facts": [
            ("🚫", "インターネットの権限を持たず、広告もありません。手順は端末の中だけに保存します。"),
            ("♿", "ユーザー補助機能は、あなたが設定でオンにした時だけ動きます。画面の文字や入力内容は読み取りません。"),
            ("⚠️", "自動操作の前に、操作する相手のアプリやサービスの利用規約をご確認ください。"),
        ],
    },
]

TOOLS = [
    ("⏱️", "ストップウォッチ", "tool-stopwatch.html"),
    ("🍅", "ポモドーロ", "tool-pomodoro.html"),
    ("🧮", "割り勘", "tool-warikan.html"),
    ("📝", "文字数", "tool-mojisu.html"),
    ("🗾", "日本地図 制覇", "tool-japan-map.html"),
    ("🔩", "ねじ下穴径", "tool-tapdrill-metric.html"),
]

POSTS = [
    ("blog-antigravity-agent-rules.html", "2026-08-14", "AI / 開発環境", "AIエージェントに運用ルールを読ませる話",
     "同じフォルダで複数のAIコーディングエージェントを動かしたら、片方が運用ルールを一度も読んでいなかった。置き場と読み込みの単位を実測した記録。"),
    ("blog-android-app-volume.html", "2026-08-09", "Android / オーディオ", "Androidでアプリごとの音量を変えられない理由を、実測で確かめた",
     "「配信アプリの音だけ下げたい」から始めた調査。出力全体の増幅が効くアプリと効かないアプリの違いを追いました。"),
]

# 差し込まないページ（OBS 表示専用・Search Console の確認用）と、ここで作るページ
SKIP_INJECT = {"tool-japan-map-display.html", "index.html"}
CURRENT = {"benefits.html": "benefits", "tools.html": "tools"}

e = html.escape


def img_size(rel):
    if Image is None:
        return None
    with Image.open(os.path.join(ROOT, rel)) as im:
        return im.size


def img_tag(rel, alt, cls="", lazy=True, prefix=""):
    size = img_size(rel)
    wh = f' width="{size[0]}" height="{size[1]}"' if size else ""
    c = f' class="{cls}"' if cls else ""
    ld = ' loading="lazy" decoding="async"' if lazy else ""
    return f'<img src="{prefix}{rel}" alt="{e(alt)}"{wh}{c}{ld}>'


def shots_of(slug):
    files = sorted(glob.glob(os.path.join(ROOT, "img", "apps", slug, "shot-*.webp")),
                   key=lambda p: int(re.search(r"shot-(\d+)", p).group(1)))
    return [os.path.relpath(p, ROOT).replace(os.sep, "/") for p in files]


def benefit_count():
    with open(os.path.join(ROOT, "data", "benefittracker", "benefits.json"), encoding="utf-8") as f:
        d = json.load(f)
    tickers = {t.get("ticker") for t in d.get("templates", []) + d.get("siteOnly", []) if t.get("ticker")}
    return len(tickers)


def head(title, desc, canonical, image, card="summary_large_image", og_type="website", jsonld=None):
    ld = ""
    if jsonld:
        ld = '\n<script type="application/ld+json">\n' + json.dumps(jsonld, ensure_ascii=False, indent=1) + "\n</script>"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{image}">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="{card}">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{image}">
<meta name="theme-color" content="#FAF7F2">
<link rel="icon" href="logo.png">
{css_link()}{ld}
</head>"""


def play_button(a, cls="btn primary"):
    return (f'<a class="{cls}" href="{PLAY}{a["pkg"]}" target="_blank" rel="noopener">'
            f'<span aria-hidden="true">▶</span>Google Play で入手</a>')


def badge(a):
    cls = "ok" if a["status"] == "ok" else "wip"
    dot = "●" if a["status"] == "ok" else "◐"
    return f'<span class="badge {cls}"><span aria-hidden="true">{dot}</span>{e(a["badge"])}</span>'


def app_card(a):
    icon = img_tag(f'img/apps/{a["slug"]}/icon.webp', "", lazy=True)
    return (f'<a class="app" href="app-{a["slug"]}.html">{icon}<div>'
            f'<div class="app-n">{e(a["name"])}</div><div class="app-d">{e(a["lead"])}</div>{badge(a)}</div></a>')


def build_index():
    n_benefit = benefit_count()
    live = [a for a in APPS if a["status"] == "ok"]
    soon = [a for a in APPS if a["status"] != "ok"]
    desc = (f"{SITE_NAME}の Android アプリ（" + "・".join(a["name"] for a in APPS[:6]) +
            f"ほか）と、株主優待{n_benefit}銘柄のデータベース、ブラウザで使える便利ツールをまとめています。")
    jsonld = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": BASE_URL + "index.html",
         "inLanguage": "ja"},
        {"@context": "https://schema.org", "@type": "Organization", "name": SITE_NAME, "url": BASE_URL + "index.html",
         "logo": BASE_URL + "logo.png", "email": CONTACT},
    ]

    posts = "".join(
        f'<a class="post" href="{href}"><div class="post-m">{d} ・ {e(tag)}</div>'
        f'<div class="post-t">{e(t)}</div><div class="post-d">{e(s)}</div></a>'
        for href, d, tag, t, s in POSTS)
    body = f"""
<body class="site">
{header_html(current=None)}
<main class="wrap">
<section class="hero">
<img class="hero-logo" src="logo.jpg" alt="{SITE_NAME} のロゴ" width="288" height="288">
<div>
<h1>{SITE_NAME}</h1>
<p>毎日のちょっとした手間を減らす Android アプリと、ブラウザで使える道具を作っています。</p>
</div>
</section>

<nav class="doors" aria-label="入口">
<a class="door main" href="benefits.html"><span class="door-ico" aria-hidden="true">🎁</span>
<span class="door-t">株主優待データベース</span>
<span class="door-d">使えるお店・期限・長期保有の条件を銘柄ごとに</span>
<span class="door-n">{n_benefit}銘柄を検索 →</span></a>
<a class="door" href="tools.html"><span class="door-ico" aria-hidden="true">🧰</span>
<span class="door-t">便利ツール</span>
<span class="door-d">インストール不要・ブラウザだけで動く</span>
<span class="door-n">{len(TOOLS)}つのツール →</span></a>
<a class="door" href="ai-keys.html"><span class="door-ico" aria-hidden="true">🔑</span>
<span class="door-t">AIキー取得ガイド</span>
<span class="door-d">各社の AI の API キーの取り方</span>
<span class="door-n">ガイドを読む →</span></a>
</nav>

<section class="sec" id="apps">
<div class="sec-h"><h2>アプリ</h2></div>
<div class="apps">{"".join(app_card(a) for a in live)}</div>
<div class="app-group">テスト中・公開準備中</div>
<div class="apps">{"".join(app_card(a) for a in soon)}</div>
</section>

<section class="sec" id="articles">
<div class="sec-h"><h2>記事</h2></div>
<p class="sec-sub">作る前に調べたこと、実機で確かめたことの記録です。</p>
<div class="posts">{posts}</div>
</section>
</main>
{footer_html()}
</body>
</html>
"""
    page = head(f"{SITE_NAME} | Android アプリ・株主優待データベース・便利ツール", desc,
                BASE_URL + "index.html", BASE_URL + "logo.png", card="summary", jsonld=jsonld) + body
    write("index.html", page)


def build_app(a):
    slug = a["slug"]
    url = f"{BASE_URL}app-{slug}.html"
    title = f'{a["name"]}（{a["sub"]}）| {SITE_NAME}'
    desc = a["lead"]
    shots = shots_of(slug)
    jsonld = {
        "@context": "https://schema.org", "@type": "SoftwareApplication",
        "name": a["name"], "alternateName": a["sub"], "description": desc,
        "operatingSystem": "ANDROID", "applicationCategory": a["category"],
        "url": url, "image": BASE_URL + f"img/apps/{slug}/icon.png",
        "screenshot": [BASE_URL + s for s in shots],
        "author": {"@type": "Organization", "name": SITE_NAME, "url": BASE_URL + "index.html"},
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "JPY"},
    }
    if a["status"] == "ok":
        jsonld["installUrl"] = PLAY + a["pkg"]
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ホーム", "item": BASE_URL + "index.html"},
        {"@type": "ListItem", "position": 2, "name": "アプリ", "item": BASE_URL + "index.html#apps"},
        {"@type": "ListItem", "position": 3, "name": a["name"], "item": url},
    ]}

    if a["status"] == "ok":
        primary = play_button(a)
        note = ""
    else:
        primary = ""
        note = f'<p class="ap-note">{"いまはクローズドテスト中で、ストアの公開ページはまだありません。" if "テスト" in a["badge"] else "Google Play での公開に向けて準備中です。"}</p>'
    extra = ""
    if a.get("extra"):
        ico, label, href = a["extra"]
        extra = f'<a class="btn" href="{href}"><span aria-hidden="true">{ico}</span>{e(label)}</a>'
    privacy = f'<a class="btn" href="{a["privacy"]}"><span aria-hidden="true">🔒</span>プライバシーポリシー</a>'

    shot_html = "".join(img_tag(s, f'{a["name"]} の画面 {i}', lazy=i > 2) for i, s in enumerate(shots, 1))
    feats = "".join(
        f'<div class="feat"><div class="feat-i" aria-hidden="true">{ico}</div><div class="feat-t">{e(t)}</div>'
        f'<div class="feat-d">{e(d)}</div></div>' for ico, t, d in a["feats"])
    feats_cls = " even" if len(a["feats"]) % 3 and len(a["feats"]) % 2 == 0 else ""
    steps = "".join(f"<li>{e(s)}</li>" for s in a["steps"])
    facts = "".join(f'<li><span aria-hidden="true">{ico}</span><span>{e(t)}</span></li>' for ico, t in a["facts"])
    others = "".join(
        f'<a href="app-{o["slug"]}.html">{img_tag(f"img/apps/{o['slug']}/icon.webp", "")}{e(o["name"])}</a>'
        for o in APPS if o is not a)
    icon = img_tag(f"img/apps/{slug}/icon.webp", f'{a["name"]} のアイコン', lazy=False)
    cta_icon = img_tag(f"img/apps/{slug}/icon.webp", "")

    body = f"""
<body class="site">
{header_html(current="apps")}
<main class="wrap">
<nav class="crumb" aria-label="パンくず"><a href="index.html">ホーム</a> › <a href="index.html#apps">アプリ</a> › {e(a["name"])}</nav>

<section class="ap-hero">
{icon}
<div>
<h1>{e(a["name"])}</h1>
<div class="ap-sub">{e(a["sub"])}</div>
{badge(a)}
<p class="ap-lead">{e(a["lead"])}</p>
<div class="btns">{primary}{extra}{privacy}</div>
{note}
</div>
</section>

<section class="sec" aria-label="画面">
<div class="shots">{shot_html}</div>
</section>

<section class="sec">
<div class="sec-h"><h2>できること</h2></div>
<div class="feats{feats_cls}">{feats}</div>
</section>

<section class="sec">
<div class="sec-h"><h2>使い方</h2></div>
<ol class="steps">{steps}</ol>
</section>

<section class="sec">
<div class="sec-h"><h2>データと注意</h2></div>
<ul class="facts">{facts}</ul>
</section>

<div class="cta">
<div class="cta-t">{cta_icon}<span>{e(a["name"])}</span></div>
<div class="btns">{primary or badge(a)}{privacy}</div>
</div>

<section class="sec">
<div class="sec-h"><h2>ほかのアプリ</h2><a href="index.html#apps">一覧 →</a></div>
<div class="more">{others}</div>
</section>
</main>
{footer_html()}
</body>
</html>
"""
    page = head(title, desc, url, BASE_URL + f"img/apps/{slug}/og.jpg", jsonld=[jsonld, crumbs]) + body
    write(f"app-{slug}.html", page)


def write(name, text):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def inject(path):
    """既存ページに共通の CSS・ヘッダー・フッターを差し込む（目印で囲むので何度流しても同じ）。"""
    name = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        s = f.read()
    orig = s
    current = CURRENT.get(name) or ("tools" if name.startswith("tool-") else "articles" if name.startswith("blog-") else None)
    hdr, ftr = header_html(current=current), footer_html()

    if CSS_MARK not in s:
        s = s.replace("</head>", css_link() + "\n</head>", 1)

    if HEADER_BEGIN in s:
        s = re.sub(re.escape(HEADER_BEGIN) + ".*?" + re.escape(HEADER_END), lambda m: hdr, s, count=1, flags=re.S)
    elif re.search(r"<header\b.*?</header>", s, re.S):
        s = re.sub(r"<header\b.*?</header>", lambda m: hdr, s, count=1, flags=re.S)
    else:
        s = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + hdr, s, count=1)

    if FOOTER_BEGIN in s:
        s = re.sub(re.escape(FOOTER_BEGIN) + ".*?" + re.escape(FOOTER_END), lambda m: ftr, s, count=1, flags=re.S)
    else:
        pat = r'<div class="footer-links">.*?</div>\s*<div class="copyright">.*?</div>'
        if re.search(pat, s, re.S):
            s = re.sub(pat, lambda m: ftr, s, count=1, flags=re.S)
        else:
            s = s.replace("</body>", ftr + "\n</body>", 1)

    if s != orig:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(s)
        return True
    return False


def update_counts():
    n = benefit_count()
    changed = []
    for name in ("tools.html", "benefits.html"):
        p = os.path.join(ROOT, name)
        with open(p, encoding="utf-8") as f:
            s = f.read()
        t = re.sub(r"人気の株主優待\s?\d+\s?銘柄", f"人気の株主優待{n}銘柄", s)
        if t != s:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(t)
            changed.append(name)
    return n, changed


def main():
    build_index()
    for a in APPS:
        build_app(a)
    targets = [p for p in sorted(glob.glob(os.path.join(ROOT, "*.html")))
               if os.path.basename(p) not in SKIP_INJECT
               and not os.path.basename(p).startswith("app-")
               and not re.match(r"google[0-9a-f]+\.html$", os.path.basename(p))]
    injected = [os.path.basename(p) for p in targets if inject(p)]
    n, changed = update_counts()
    print(f"index.html + app pages: {len(APPS)}")
    print(f"injected header/footer: {len(injected)} / {len(targets)}")
    print(f"benefit count: {n}  updated: {changed}")


if __name__ == "__main__":
    main()
