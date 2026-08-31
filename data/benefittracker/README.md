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
3. commit → push（GitHub Pages に反映されるまで数分）

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
| unitPrice | int | 1単位の金額 | 0 |
| balanceUnit | string | 残高の単位（円分/円/冊 等） | 円 |
| quantityUnit | string | 数量の単位（枚/冊/回 等） | 枚 |
| exchange | string | 上場市場 | 東証 |

## 同梱スナップショットの同期（任意）

アプリのリリースビルドを焼く時は、初回オフライン用の同梱データも最新化しておく:

```
cp data/benefittracker/benefits.json ../BenefitTracker/app/src/main/assets/benefits.json
```

（同期を忘れても、オンラインになれば最新が取得されるので実害は小さい）

技術的経緯の正本は SecondBrain `research/benefittracker.md`。
