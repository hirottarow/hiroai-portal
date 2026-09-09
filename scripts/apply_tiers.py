#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""benefits.json の指定銘柄に tiers（株数段階）をまとめて入れる。

## 何のためのツールか

142銘柄のうち tiers を持つのは一部だけで、無い銘柄ではアプリの条件選択ダイアログが出ない。
残りを何本かに分けて埋めていく作業用（2026-09-10 の外食20銘柄が1本目）。
**巨大な JSON を手で編集して壊す事故を防ぐ**のが目的で、調べる仕事そのものは肩代わりしない。

    python scripts/apply_tiers.py <patch.json>

patch.json の形:

    {
      "auditedAt": "2026-09-10",
      "dataVersion": "2026-09-10.1",          # 省略可。最後のバッチにだけ書けばよい
      "items": {
        "7550": {
          "auditScope": "券種・金額・使える店・使い方の注意・株数区分",
          "tiers": [ {"minShares": 100, "minHoldMonths": 0, "amount": 1000, "timesPerYear": 2} ],
          "tiersNote": "継続保有条件なし。3月末・9月末基準の年2回で、金額は1回ぶん",
          "balance": 1000                      # 省略可。tiers の最小段と食い違う時だけ書く
        }
      }
    }

**キーは `amount`（`amountYen` ではない）。** `amountYen` は `quo.tiers` 側のキーで別物。
書式と各フィールドの意味の正本は `data/benefittracker/README.md`。

## 使い方の約束

- **20銘柄を一度に書き換えず、数銘柄ずつのパッチに分けて流す。** 途中で止めてもそこまでが残る。
- 流したら毎回 `python scripts/validate_benefits.py` を通す（exit 0 を確認する）。
- 全部終わってから `python scripts/build_benefits_pages.py` を1回流す。
- **推測で埋めない。** 公式で確認できなかった銘柄は tiers を入れずに残すのが正解。
  外れる段階を出すくらいなら黙る（入れなければアプリは今までどおりで実害が無い）。
  公式ページの探し方と、株数区分の表を落とさずに読む方法は `tools/links.py` と `tools/fetch.py`
  の先頭コメントに書いてある（**WebFetch の要約は表の行を落とすので使わない**）。

## 壊さないための作り

読み込み → 書き戻しが**バイト単位で一致する**ことを確認してある（`indent=1` / `ensure_ascii=False` /
末尾改行1つ）。指定した銘柄のフィールド以外は触らないので、**他セッションが同じファイルへ
足したエントリも保たれる**（2026-09-10 に実際に MIRARTH 8897 の追加と同時進行になった）。
ただし同時書き込みそのものは防げないので、並行して触っている相手がいる時は先に声を掛けること。
"""
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "benefittracker", "benefits.json")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    patch = json.load(open(sys.argv[1], encoding="utf-8"))
    audited = patch["auditedAt"]
    items = patch["items"]

    d = json.load(open(DATA_PATH, encoding="utf-8"))
    by = {t.get("ticker"): t for t in d["templates"]}

    for ticker, spec in items.items():
        t = by.get(ticker)
        if t is None:
            print("!! ticker %s が見つかりません（中止。何も書いていません）" % ticker)
            return 1
        t["tiers"] = spec["tiers"]
        t["tiersNote"] = spec["tiersNote"]
        t["auditedAt"] = audited
        t["auditScope"] = spec["auditScope"]
        if "balance" in spec:
            print("   balance %s: %s -> %s" % (ticker, t["balance"], spec["balance"]))
            t["balance"] = spec["balance"]
        print("OK %s %s tiers=%d" % (ticker, t["company"], len(t["tiers"])))

    if "dataVersion" in patch:
        d["dataVersion"] = patch["dataVersion"]
        d["updatedAt"] = audited
        print("dataVersion -> %s" % d["dataVersion"])

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("書き込み完了 -> %s" % DATA_PATH)
    print("次に: python scripts/validate_benefits.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
