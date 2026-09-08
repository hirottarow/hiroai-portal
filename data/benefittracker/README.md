# BenefitTracker 優待カタログ（正本）

`benefits.json` が **株主優待テンプレートデータの正本**。ここを編集して push するだけで、
以下の2箇所へ自動反映される（アプリの再ビルド・Play 審査は不要）。

1. **ポータルの一覧ページ** `../../benefits.html` … このJSONをfetchして描画
2. **BenefitTracker アプリ**（優待辞書画面）… 起動時に
   `https://hirottarow.github.io/hiroai-portal/data/benefittracker/benefits.json`
   を取得してキャッシュ（オフライン時はキャッシュ→同梱スナップショットの順でフォールバック）

## 更新手順

1. `benefits.json` の `templates` 配列を編集（追加・修正・削除）
2. `dataVersion` を更新（`YYYY-MM-DD.連番`）、`updatedAt` を当日に
3. **push 前に `python scripts/build_benefits_pages.py` を流す**（銘柄ごとの静的ページ `benefits/<ticker>.html`・
   `benefits.html` の静的一覧・`sitemap.xml` を再生成する。2026-09-09 新設。標準ライブラリのみ、冪等）
4. commit → push（GitHub Pages に反映されるまで数分）

## スキーマの約束

- `schemaVersion: 1` を維持する。**既存フィールドの削除・型変更は禁止**
  （旧バージョンのアプリが読めなくなる）。フィールドの**追加は自由**
  （アプリは `ignoreUnknownKeys` で未知フィールドを無視する）。
- `templates` を空にしない・`company` を空文字にしない
  （アプリ側が不正データとして**取得を破棄**し、更新されない）。
- 破壊的変更が必要になったら `benefits.v2.json` を新設し、旧ファイルは残す。

## テンプレート1件のフィールド

| キー | 型 | 意味 | 省略時 |
|---|---|---|---|
| company | string | 企業名（**必須・アプリ側の照合キー**） | — |
| title | string | 優待の名称 | "" |
| balance | int | 初期残高の目安 | 0 |
| category | string | 外食/小売/交通/レジャー/カタログ/自社商品/その他 | その他 |
| ticker | string | 証券コード | "" |
| usableStores | string | 使える店舗 | "" |
| description | string | 説明（\n 区切りの複数段落） | "" |
| rating | int | おすすめ度 1〜5 | 3 |
| unitPrice | int | 1単位の金額。**規約: 金券・枚数系=券面額 / 物品セット・カタログ系=balanceと同値（1セットで使い切り） / ポイント・チャージ系=0（個数と「1回使う」を表示しない）**。1のまま残すとアプリで「1個=1円」になる（2026-08-31 の不具合） | 0 |
| balanceUnit | string | 残高の単位（円分/円/冊 等） | 円 |
| quantityUnit | string | 数量の単位（枚/冊/回 等） | 枚 |
| exchange | string | 上場市場 | 東証 |
| usageNotes | string | 使い方（券面額・お釣りの可否・併用制限・有効期限など**残高の減り方に効く事実**）。アプリのカード詳細に「💳」で出る。裏取りできた内容だけ書く | "" |
| shipMonths | string | 発送目安月（カンマ区切り。例 `"5,11"`）。「そろそろ届くはず」の判定にだけ使う | "" |
| auditedAt | string | **その銘柄の内容を最後に各社の公表資料で確かめた日**（`YYYY-MM-DD`）。古い順に並べれば次に見るべき銘柄が出る | "" |

### `usageNotes` を足したら数値も読み直す（2026-09-07 追加）

`usageNotes` に「1円単位で使える」「ポイント制」と書いたのに `unitPrice` を券面額のまま残す事故を
**同じ日に4件**やった（エディオン・西松屋・バロー・オートバックス）。本文だけを直して数値を
置き去りにするのも同じで、マツキヨは「商品券→ポイント制へ変更」と本文に書いた状態で
title が「商品券」のまま数日残った。**注記と数値は同じレコードにある。片方を触ったら必ずもう片方を見る。**

規約の対応:
- 券・枚数系 … `unitPrice` = 券面額
- 物品セット・カタログ系 … `unitPrice` = `balance`
- **ポイント・チャージ・電子チケット・1円単位のカード … `unitPrice` = 0**
- 割引券・割引カード … `unitPrice` = 1 / `balanceUnit` = `枚` / `balance` = 枚数（金券ではないので円で持たない）

`balance` は**1回に届く額**で持つ（年2回の銘柄で年間合計を入れない）。

## `siteOnly` … サイトで紹介するだけの銘柄（2026-09-06 新設）

`templates` と同じ形の配列だが、**アプリの優待辞書には出さず、`benefits.html` でだけ紹介する**。
`siteGroup`（例 `"QUOカード"`）でひとまとめにして、ページ下部に別セクションで出す。

現在入っているのは **QUOカードそのものが優待品の銘柄**（稲畑産業・たけびし・フタバ産業・スターシーズ）。
QUOカードは**有効期限が無く、発行元と関係のないコンビニ・書店で使える**ので、
残高と期限を管理する対象にならない。加えて、券面スキャンの銘柄同定は `usableStores` を
ブランド名として照合するため、**「コンビニ」「書店」のような一般名詞を持つ銘柄が並ぶと
同点で誤爆する**（QUOカード銘柄は全部これだった）。

アプリ側は未知のトップレベルキーを無視する（`TemplateCatalog` が `ignoreUnknownKeys`）ので、
`siteOnly` を足しても旧バージョンのアプリは壊れない。**`templates` から外した銘柄は
アプリの辞書から消える**（登録済みのカードは消えない）ので、移す前に管理する価値があるかを確かめること。

## 同梱スナップショットの同期（任意）

アプリのリリースビルドを焼く時は、初回オフライン用の同梱データも最新化しておく:

```
cp data/benefittracker/benefits.json ../BenefitTracker/app/src/main/assets/benefits.json
```

（同期を忘れても、オンラインになれば最新が取得されるので実害は小さい）

技術的経緯の正本は SecondBrain `research/benefittracker.md`。
