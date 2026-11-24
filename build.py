#!/usr/bin/env python3
"""Batch builder, validator, and GitHub Pages (/docs) sync for Scratch 3.0 (.sb3).

Usage:
    python3 -X utf8 build.py
"""

from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

from builder.validator import validate_sb3
from tasks import ALL_TASKS


ROOT_DIR = Path(__file__).resolve().parent
TASKS_CSV_PATH = ROOT_DIR / "data" / "tasks.csv"
DIST_DIR = ROOT_DIR / "dist"
DIST_TEMPLATES_DIR = DIST_DIR / "templates"
DIST_SAMPLES_DIR = DIST_DIR / "samples"

# Fixed 6-character random directory name under docs/ to avoid guessable URLs
PUBLISH_SLUG = "r86pu8"
DOCS_DIR = ROOT_DIR / "docs"
DOCS_PUBLISH_DIR = DOCS_DIR / PUBLISH_SLUG
DOCS_TEMPLATES_DIR = DOCS_PUBLISH_DIR / "templates"
DOCS_SAMPLES_DIR = DOCS_PUBLISH_DIR / "samples"


def load_csv_file_ids(csv_path: Path) -> dict[int, str]:
    """Read data/tasks.csv (skip lines 1-2 memo rows, line 3 is header) -> {No.: ファイルID}."""
    if not csv_path.exists():
        raise FileNotFoundError(f"tasks.csv が見つかりません: {csv_path}")

    mapping: dict[int, str] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        # 1〜2行目はメモ行のためスキップ
        next(f, None)
        next(f, None)
        reader = csv.DictReader(f)
        if not reader.fieldnames or "No." not in reader.fieldnames or "ファイルID" not in reader.fieldnames:
            raise ValueError(
                f"tasks.csv の3行目ヘッダーに 'No.' または 'ファイルID' がありません: {reader.fieldnames}"
            )
        for row in reader:
            no_raw = (row.get("No.") or "").strip()
            file_id = (row.get("ファイルID") or "").strip()
            if not no_raw or not file_id:
                continue
            mapping[int(no_raw)] = file_id
    return mapping


def _resolve_file_id(task_mod: object, csv_ids: dict[int, str]) -> str:
    task_id = getattr(task_mod, "TASK_ID", "")
    prefix = task_id.split("_", 1)[0]
    if not prefix.isdigit():
        raise ValueError(f"TASK_ID {task_id!r} の先頭から課題番号を取得できません")
    task_no = int(prefix)
    if task_no not in csv_ids:
        raise KeyError(f"課題 No.{task_no} が data/tasks.csv に存在しません")
    expected_id = csv_ids[task_no]
    if task_id != expected_id:
        raise ValueError(
            f"TASK_ID 不一致 (No.{task_no}): code={task_id!r} != csv={expected_id!r}"
        )
    return expected_id


def _clean_sb3_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for old_file in directory.glob("*.sb3"):
        old_file.unlink()


def sync_to_docs() -> None:
    """Sync dist/samples and dist/templates into docs/<PUBLISH_SLUG>/ and write Pages guard files."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS_DIR / "robots.txt").write_text(
        "User-agent: *\nDisallow: /\n",
        encoding="utf-8",
    )

    _clean_sb3_dir(DOCS_TEMPLATES_DIR)
    _clean_sb3_dir(DOCS_SAMPLES_DIR)

    for src in sorted(DIST_TEMPLATES_DIR.glob("*.sb3")):
        shutil.copy2(src, DOCS_TEMPLATES_DIR / src.name)
    for src in sorted(DIST_SAMPLES_DIR.glob("*.sb3")):
        shutil.copy2(src, DOCS_SAMPLES_DIR / src.name)


def main() -> int:
    csv_ids = load_csv_file_ids(TASKS_CSV_PATH)
    _clean_sb3_dir(DIST_TEMPLATES_DIR)
    _clean_sb3_dir(DIST_SAMPLES_DIR)

    generated_paths: list[Path] = []

    print(f"=== Scratch 3.0 (.sb3) ビルド開始（全 {len(ALL_TASKS)} 課題 / CSV照合済）===")
    for task_mod in ALL_TASKS:
        file_id = _resolve_file_id(task_mod, csv_ids)
        task_title = getattr(task_mod, "TASK_TITLE", file_id)

        template_proj = task_mod.build_template()
        template_path = DIST_TEMPLATES_DIR / f"{file_id}_template.sb3"
        template_proj.save(template_path)
        generated_paths.append(template_path)

        sample_proj = task_mod.build_sample()
        sample_path = DIST_SAMPLES_DIR / f"{file_id}_sample.sb3"
        sample_proj.save(sample_path)
        generated_paths.append(sample_path)

        print(f"  [BUILD] {file_id} ({task_title})")
        print(f"          template -> {template_path.relative_to(ROOT_DIR)}")
        print(f"          sample   -> {sample_path.relative_to(ROOT_DIR)}")

    print("\n=== 自動バリデーション実行 (builder/validator.py) ===")
    all_ok = True
    total_warnings = 0
    for sb3_path in generated_paths:
        res = validate_sb3(sb3_path)
        rel = sb3_path.relative_to(ROOT_DIR)
        st = res.stats
        status = "PASS" if res.ok else "FAIL"
        ext_str = ",".join(st.get("extensions", [])) or "none"
        print(
            f"  [{status}] {rel} "
            f"(targets={st['targets']}, blocks={st['blocks']}, "
            f"top={st['top_level_blocks']}, costumes={st['costumes']}, "
            f"sounds={st['sounds']}, comments={st['comments']}, ext={ext_str})"
        )
        for warn in res.warnings:
            total_warnings += 1
            print(f"         [WARN] {warn}")
        for err in res.errors:
            print(f"         [ERR]  {err}")
        if not res.ok:
            all_ok = False

    if not all_ok:
        print("\nバリデーションエラーが検出されたため docs/ への同期を中止しました。", file=sys.stderr)
        return 1

    sync_to_docs()
    docs_count = len(list(DOCS_SAMPLES_DIR.glob("*.sb3"))) + len(
        list(DOCS_TEMPLATES_DIR.glob("*.sb3"))
    )
    print(f"\n=== GitHub Pages 同期完了 ===")
    print(f"  公開ディレクトリ : {DOCS_PUBLISH_DIR.relative_to(ROOT_DIR)}/ ({docs_count} files)")
    print(f"  ガードファイル   : docs/.nojekyll, docs/robots.txt")
    print(
        f"\n全 {len(generated_paths)} ファイル（{len(ALL_TASKS)} 課題ペア）の"
        f"ビルド・バリデーション・docs同期に成功しました！（警告={total_warnings}件）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
