#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""benefits.json の構造検証。push 前に必ず実行すること:

    python scripts/validate_benefits.py

`build_benefits_pages.py` はページを生成するだけでデータの妥当性は見ない（別の仕事なので混ぜない）。
このスクリプトは「壊れたデータが push されて、アプリが無言で古いキャッシュへ落ちる」事故を
push 前に止めるためのもの。標準ライブラリのみ使用。

検出する不正:
  - JSON構文エラー
  - 必須項目の欠落（company/title/category/ticker/usableStores/description/
    balanceUnit/quantityUnit/exchange/auditedAt/auditScope が空文字、
    balance/unitPrice/rating のキー欠落）
  - 型違い（文字列であるべき項目が数値、等）
  - ticker の重複（templates + siteOnly を通して）
  - tiers / quo.tiers の minShares が昇順でない
  - dataVersion の形式違反（YYYY-MM-DD.連番）
  - auditedAt の形式違反（YYYY-MM-DD。quo.auditedAt も対象）

エラーがあれば終了コードを 0 以外にする。正常なら何も出さず 0 で終わる。
"""
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "benefittracker", "benefits.json")

DATA_VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.\d+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# 現行データで全件に存在する文字列項目（空文字は不可）
REQUIRED_STR_FIELDS = (
    "company", "title", "category", "ticker", "usableStores",
    "description", "balanceUnit", "quantityUnit", "exchange",
    "auditedAt", "auditScope",
)
# 現行データで全件に存在する数値項目（キー自体の欠落のみ検出。値は0でもよい）
REQUIRED_INT_FIELDS = ("balance", "unitPrice", "rating")

# 型が決まっている任意項目（あれば型だけ見る）
OPTIONAL_STR_FIELDS = ("usageNotes", "shipMonths", "tiersNote", "siteGroup")

TIER_INT_FIELDS = ("minShares", "minHoldMonths", "amount")
QUO_TIER_INT_FIELDS = ("minShares", "minHoldMonths", "amountYen")
QUO_STR_FIELDS = ("rightsMonths", "note", "auditedAt", "auditScope")


class Errors:
    def __init__(self):
        self.items = []

    def add(self, line, label, message):
        self.items.append((line, label, message))

    def __bool__(self):
        return bool(self.items)


def line_of(text, char_offset):
    return text.count("\n", 0, char_offset) + 1


def scan_top_level_objects(text, array_open_idx):
    """array_open_idx は配列の '[' の直後の位置。直下の {...} の (start, end) を順番に返す。"""
    objects = []
    i = array_open_idx
    n = len(text)
    depth = 0
    in_string = False
    escape = False
    obj_start = None
    while i < n:
        c = text[i]
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == "{":
                if depth == 0:
                    obj_start = i
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0 and obj_start is not None:
                    objects.append((obj_start, i + 1))
                    obj_start = None
            elif c == "]" and depth == 0:
                break
        i += 1
    return objects


def find_array_open(text, key):
    m = re.search(r'"%s"\s*:\s*\[' % re.escape(key), text)
    return m.end() if m else None


def item_label(item, index):
    ticker = item.get("ticker") if isinstance(item, dict) else None
    company = item.get("company") if isinstance(item, dict) else None
    parts = []
    if ticker:
        parts.append("ticker=%s" % ticker)
    if company:
        parts.append("company=%s" % company)
    return " ".join(parts) if parts else "(index %d)" % index


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def is_str(v):
    return isinstance(v, str)


def validate_tiers(tiers, line, label, errors, int_fields, where):
    """minShares の昇順は「同じ minHoldMonths（継続保有条件）どうし」でのみ成り立つ。
    実データは 100株(条件なし)→500株(条件なし)→…→100株(12ヶ月継続)→500株(12ヶ月継続)…
    のように継続保有ボーナスの段が挟まり、その段の minShares は基本段より小さく戻ってよい
    （ビックカメラ・コジマ等で実在するパターン）。minHoldMonths が同じ段どうしの中でだけ判定する。"""
    if not isinstance(tiers, list):
        errors.add(line, label, "%s が配列ではありません" % where)
        return
    prev_by_hold = {}
    for i, tier in enumerate(tiers):
        if not isinstance(tier, dict):
            errors.add(line, label, "%s[%d] がオブジェクトではありません" % (where, i))
            continue
        for f in int_fields:
            if f in tier and not is_int(tier[f]):
                errors.add(line, label, "%s[%d].%s が数値ではありません（値: %r）" % (where, i, f, tier[f]))
        if "timesPerYear" in tier and tier["timesPerYear"] is not None and not is_int(tier["timesPerYear"]):
            errors.add(line, label, "%s[%d].timesPerYear が数値ではありません（値: %r）" % (where, i, tier["timesPerYear"]))
        min_shares = tier.get("minShares")
        hold = tier.get("minHoldMonths")
        if is_int(min_shares) and is_int(hold):
            prev = prev_by_hold.get(hold)
            if prev is not None and min_shares <= prev:
                errors.add(
                    line, label,
                    "%s の minShares が昇順ではありません（%d件目: minHoldMonths=%d の中で %d は直前の %d 以下）"
                    % (where, i + 1, hold, min_shares, prev),
                )
            prev_by_hold[hold] = min_shares


def validate_item(item, line, index, errors, is_site_only):
    label = item_label(item, index)
    if not isinstance(item, dict):
        errors.add(line, "(index %d)" % index, "銘柄がオブジェクトではありません")
        return

    for f in REQUIRED_STR_FIELDS:
        if f not in item:
            errors.add(line, label, "必須項目 '%s' が欠落" % f)
        elif not is_str(item[f]):
            errors.add(line, label, "'%s' が文字列ではありません（値: %r）" % (f, item[f]))
        elif item[f].strip() == "":
            errors.add(line, label, "'%s' が空文字です" % f)

    for f in REQUIRED_INT_FIELDS:
        if f not in item:
            errors.add(line, label, "必須項目 '%s' が欠落" % f)
        elif not is_int(item[f]):
            errors.add(line, label, "'%s' が数値ではありません（値: %r）" % (f, item[f]))

    for f in OPTIONAL_STR_FIELDS:
        if f in item and not is_str(item[f]):
            errors.add(line, label, "'%s' が文字列ではありません（値: %r）" % (f, item[f]))

    auditedAt = item.get("auditedAt")
    if is_str(auditedAt) and auditedAt and not DATE_RE.match(auditedAt):
        errors.add(line, label, "auditedAt の形式が不正です（YYYY-MM-DD ではない: %r）" % auditedAt)

    if "tiers" in item:
        validate_tiers(item["tiers"], line, label, errors, TIER_INT_FIELDS, "tiers")

    quo = item.get("quo")
    if quo is not None:
        if not isinstance(quo, dict):
            errors.add(line, label, "quo がオブジェクトではありません")
        else:
            for f in QUO_STR_FIELDS:
                if f in quo and not is_str(quo[f]):
                    errors.add(line, label, "quo.%s が文字列ではありません（値: %r）" % (f, quo[f]))
            quo_audited = quo.get("auditedAt")
            if is_str(quo_audited) and quo_audited and not DATE_RE.match(quo_audited):
                errors.add(line, label, "quo.auditedAt の形式が不正です（YYYY-MM-DD ではない: %r）" % quo_audited)
            if "tiers" in quo:
                validate_tiers(quo["tiers"], line, label, errors, QUO_TIER_INT_FIELDS, "quo.tiers")


def validate(text):
    errors = Errors()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        errors.add(e.lineno, "-", "JSON構文エラー: %s（%d行目 %d列目）" % (e.msg, e.lineno, e.colno))
        return errors

    if not isinstance(data, dict):
        errors.add(1, "-", "トップレベルがオブジェクトではありません")
        return errors

    # トップレベルの必須項目
    if "schemaVersion" not in data or not is_int(data.get("schemaVersion")):
        errors.add(1, "-", "schemaVersion が欠落、または数値ではありません")

    data_version = data.get("dataVersion")
    if not is_str(data_version) or not data_version:
        errors.add(1, "-", "dataVersion が欠落しています")
    elif not DATA_VERSION_RE.match(data_version):
        errors.add(1, "-", "dataVersion の形式が不正です（YYYY-MM-DD.連番 ではない: %r）" % data_version)

    updated_at = data.get("updatedAt")
    if is_str(updated_at) and updated_at and not DATE_RE.match(updated_at):
        errors.add(1, "-", "updatedAt の形式が不正です（YYYY-MM-DD ではない: %r）" % updated_at)

    templates = data.get("templates")
    if not isinstance(templates, list) or len(templates) == 0:
        errors.add(1, "-", "templates が空、または配列ではありません")
        templates = templates if isinstance(templates, list) else []

    site_only = data.get("siteOnly", [])
    if not isinstance(site_only, list):
        errors.add(1, "-", "siteOnly が配列ではありません")
        site_only = []

    # 行番号を突き合わせるため、生テキスト側も同じ順序で走査する
    templates_open = find_array_open(text, "templates")
    site_only_open = find_array_open(text, "siteOnly")
    template_spans = scan_top_level_objects(text, templates_open) if templates_open is not None else []
    site_only_spans = scan_top_level_objects(text, site_only_open) if site_only_open is not None else []

    all_items = []
    for i, item in enumerate(templates):
        span = template_spans[i] if i < len(template_spans) else None
        line = line_of(text, span[0]) if span else 1
        validate_item(item, line, i, errors, is_site_only=False)
        all_items.append((item, line))

    for i, item in enumerate(site_only):
        span = site_only_spans[i] if i < len(site_only_spans) else None
        line = line_of(text, span[0]) if span else 1
        validate_item(item, line, i, errors, is_site_only=True)
        all_items.append((item, line))

    # ticker の重複（空は対象外）
    seen = {}
    for item, line in all_items:
        if not isinstance(item, dict):
            continue
        ticker = item.get("ticker")
        if not ticker:
            continue
        if ticker in seen:
            first_line, first_label = seen[ticker]
            errors.add(
                line, item_label(item, -1),
                "ticker '%s' が重複しています（%d行目の %s と重複）" % (ticker, first_line, first_label),
            )
        else:
            seen[ticker] = (line, item_label(item, -1))

    return errors


def main():
    if not os.path.exists(DATA_PATH):
        print("ERROR: %s が見つかりません" % DATA_PATH, file=sys.stderr)
        return 1

    with open(DATA_PATH, encoding="utf-8") as f:
        text = f.read()

    errors = validate(text)
    if not errors:
        print("OK: %s は正常です" % os.path.relpath(DATA_PATH, ROOT))
        return 0

    for line, label, message in errors.items:
        print("[%d行目] %s: %s" % (line, label, message))
    print("--- %d件のエラー ---" % len(errors.items), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
