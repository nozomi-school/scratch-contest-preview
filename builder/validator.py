"""Automated Scratch 3.0 (.sb3) archive and structural integrity validator."""

from __future__ import annotations

import hashlib
import io
import json
import re
import wave
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Union


MD5_RE = re.compile(r"^[0-9a-f]{32}$")


@dataclass
class ValidationResult:
    path: Path
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


def _iter_input_block_refs(inputs: dict) -> List[Tuple[str, str]]:
    """Return list of (input_name, referenced_block_id) from a Scratch block's inputs."""
    refs: List[Tuple[str, str]] = []
    for input_name, raw_val in inputs.items():
        if not isinstance(raw_val, list) or len(raw_val) < 2:
            continue
        for elem in raw_val[1:]:
            if isinstance(elem, str):
                refs.append((input_name, elem))
    return refs


def _iter_input_var_refs(inputs: dict) -> List[Tuple[str, str]]:
    """Return list of (var_name, var_id) from inline variable reporters in inputs."""
    refs: List[Tuple[str, str]] = []
    for raw_val in inputs.values():
        if not isinstance(raw_val, list):
            continue
        for elem in raw_val[1:]:
            if isinstance(elem, list) and len(elem) >= 3 and elem[0] == 12:
                refs.append((str(elem[1]), str(elem[2])))
    return refs


def _iter_input_broadcast_refs(inputs: dict) -> List[Tuple[str, str]]:
    """Return list of (broadcast_name, broadcast_id) from inline broadcast inputs."""
    refs: List[Tuple[str, str]] = []
    for raw_val in inputs.values():
        if not isinstance(raw_val, list):
            continue
        for elem in raw_val[1:]:
            if isinstance(elem, list) and len(elem) >= 3 and elem[0] == 11:
                refs.append((str(elem[1]), str(elem[2])))
    return refs


def validate_sb3(path: Union[str, Path]) -> ValidationResult:
    """Run full Scratch 3.0 structural, asset MD5, block graph, and layout checks."""
    sb3_path = Path(path)
    errors: List[str] = []
    warnings: List[str] = []
    stats: Dict[str, Any] = {
        "targets": 0,
        "blocks": 0,
        "top_level_blocks": 0,
        "costumes": 0,
        "sounds": 0,
        "comments": 0,
        "extensions": [],
    }

    if not sb3_path.exists():
        return ValidationResult(sb3_path, False, [f"File not found: {sb3_path}"], [], stats)

    # 1. ZIP integrity and project.json parsing
    try:
        zf = zipfile.ZipFile(sb3_path, "r")
    except zipfile.BadZipFile as exc:
        return ValidationResult(sb3_path, False, [f"Invalid ZIP archive: {exc}"], [], stats)

    with zf:
        bad_file = zf.testzip()
        if bad_file is not None:
            errors.append(f"Corrupt ZIP entry detected: {bad_file}")

        zip_names = set(zf.namelist())
        if "project.json" not in zip_names:
            errors.append("Missing project.json in archive root")
            return ValidationResult(sb3_path, False, errors, warnings, stats)

        try:
            raw_json = zf.read("project.json").decode("utf-8")
            project = json.loads(raw_json)
        except Exception as exc:
            errors.append(f"Failed to parse project.json as UTF-8 JSON: {exc}")
            return ValidationResult(sb3_path, False, errors, warnings, stats)

        if not isinstance(project, dict):
            errors.append("project.json root must be a JSON object")
            return ValidationResult(sb3_path, False, errors, warnings, stats)

        targets = project.get("targets")
        extensions = project.get("extensions", [])
        stats["extensions"] = list(extensions)

        if not isinstance(targets, list) or not targets:
            errors.append("project.json 'targets' must be a non-empty list")
            return ValidationResult(sb3_path, False, errors, warnings, stats)

        stats["targets"] = len(targets)
        if not targets[0].get("isStage") or targets[0].get("name") != "Stage":
            errors.append("First target must be Stage (isStage: true, name: 'Stage')")

        stage_var_ids: Set[str] = set(targets[0].get("variables", {}).keys())
        stage_list_ids: Set[str] = set(targets[0].get("lists", {}).keys())
        stage_broadcast_ids: Set[str] = set(targets[0].get("broadcasts", {}).keys())
        sprite_names: Set[str] = {
            t.get("name", "") for t in targets if not t.get("isStage")
        }

        referenced_assets: Set[str] = set()
        used_extensions: Set[str] = set()
        seen_layer_orders: Set[int] = set()

        # 2. Validate each target (assets, blocks, comments, layout)
        for t_idx, target in enumerate(targets):
            t_name = target.get("name", f"target[{t_idx}]")
            layer_order = target.get("layerOrder")
            if layer_order in seen_layer_orders:
                errors.append(f"[{t_name}] Duplicate layerOrder: {layer_order}")
            seen_layer_orders.add(layer_order)

            # 2a. Costumes
            costumes = target.get("costumes", [])
            if not costumes:
                errors.append(f"[{t_name}] Target must have at least one costume")
            costume_names: Set[str] = set()
            for c in costumes:
                stats["costumes"] += 1
                costume_names.add(c.get("name", ""))
                _validate_asset(
                    zf, zip_names, referenced_assets, errors, t_name, c, kind="costume"
                )

            # 2b. Sounds
            sounds = target.get("sounds", [])
            sound_names: Set[str] = set()
            for s in sounds:
                stats["sounds"] += 1
                sound_names.add(s.get("name", ""))
                _validate_asset(
                    zf, zip_names, referenced_assets, errors, t_name, s, kind="sound"
                )

            # 2c. Blocks graph integrity
            blocks = target.get("blocks", {})
            if not isinstance(blocks, dict):
                errors.append(f"[{t_name}] 'blocks' must be a dict")
                continue

            stats["blocks"] += len(blocks)
            target_var_ids = stage_var_ids | set(target.get("variables", {}).keys())
            target_list_ids = stage_list_ids | set(target.get("lists", {}).keys())

            children_map: Dict[str, Set[str]] = {bid: set() for bid in blocks}
            top_level_coords: List[Tuple[str, float, float]] = []

            for bid, blk in blocks.items():
                if not isinstance(blk, dict):
                    errors.append(f"[{t_name}] Block {bid!r} must be a dict")
                    continue

                opcode = blk.get("opcode", "")
                if opcode.startswith("pen_"):
                    used_extensions.add("pen")

                parent_id = blk.get("parent")
                next_id = blk.get("next")
                top_level = bool(blk.get("topLevel", False))
                shadow = bool(blk.get("shadow", False))
                inputs = blk.get("inputs", {})
                fields = blk.get("fields", {})

                if shadow and top_level:
                    errors.append(f"[{t_name}] Shadow block {bid!r} cannot be topLevel")
                if shadow and parent_id is None:
                    errors.append(f"[{t_name}] Shadow block {bid!r} must have a parent")

                if top_level:
                    stats["top_level_blocks"] += 1
                    if parent_id is not None:
                        errors.append(
                            f"[{t_name}] topLevel block {bid!r} must have parent=null, got {parent_id!r}"
                        )
                    bx = blk.get("x")
                    by = blk.get("y")
                    if not isinstance(bx, (int, float)) or not isinstance(by, (int, float)):
                        errors.append(
                            f"[{t_name}] topLevel block {bid!r} missing numeric x/y coordinates"
                        )
                    else:
                        if not (-2000 <= bx <= 2000 and -2000 <= by <= 2000):
                            errors.append(
                                f"[{t_name}] topLevel block {bid!r} out of canvas bounds: ({bx}, {by})"
                            )
                        top_level_coords.append((bid, float(bx), float(by)))
                else:
                    if parent_id is None:
                        errors.append(
                            f"[{t_name}] Non-topLevel block {bid!r} has parent=null (orphan)"
                        )
                    elif parent_id not in blocks:
                        errors.append(
                            f"[{t_name}] Block {bid!r} references missing parent {parent_id!r}"
                        )

                if next_id is not None:
                    if next_id not in blocks:
                        errors.append(
                            f"[{t_name}] Block {bid!r} references missing next {next_id!r}"
                        )
                    else:
                        children_map[bid].add(next_id)
                        if blocks[next_id].get("parent") != bid:
                            errors.append(
                                f"[{t_name}] Next link mismatch: {bid!r}.next={next_id!r}, "
                                f"but {next_id!r}.parent={blocks[next_id].get('parent')!r}"
                            )

                for input_name, ref_id in _iter_input_block_refs(inputs):
                    if ref_id not in blocks:
                        errors.append(
                            f"[{t_name}] Block {bid!r} input {input_name!r} references missing block {ref_id!r}"
                        )
                    else:
                        children_map[bid].add(ref_id)
                        if blocks[ref_id].get("parent") != bid:
                            errors.append(
                                f"[{t_name}] Input link mismatch: {bid!r}.{input_name}={ref_id!r}, "
                                f"but {ref_id!r}.parent={blocks[ref_id].get('parent')!r}"
                            )

                # Validate sound / costume / variable / list / broadcast / sprite references
                if opcode == "sound_sounds_menu":
                    snd = fields.get("SOUND_MENU", [None])[0]
                    if snd not in sound_names:
                        errors.append(
                            f"[{t_name}] Sound menu {bid!r} references unknown sound {snd!r}"
                        )
                if opcode == "looks_costume":
                    cst = fields.get("COSTUME", [None])[0]
                    if cst not in costume_names:
                        errors.append(
                            f"[{t_name}] Costume menu {bid!r} references unknown costume {cst!r}"
                        )
                if opcode in (
                    "data_setvariableto",
                    "data_changevariableby",
                    "data_showvariable",
                    "data_hidevariable",
                ):
                    var_field = fields.get("VARIABLE")
                    if (
                        not isinstance(var_field, list)
                        or len(var_field) < 2
                        or var_field[1] not in target_var_ids
                    ):
                        errors.append(
                            f"[{t_name}] Block {bid!r} references unknown variable {var_field!r}"
                        )
                if opcode in (
                    "data_addtolist",
                    "data_deleteoflist",
                    "data_deletealloflist",
                    "data_itemoflist",
                    "data_lengthoflist",
                    "data_listcontainsitem",
                ):
                    lst_field = fields.get("LIST")
                    if (
                        not isinstance(lst_field, list)
                        or len(lst_field) < 2
                        or lst_field[1] not in target_list_ids
                    ):
                        errors.append(
                            f"[{t_name}] Block {bid!r} references unknown list {lst_field!r}"
                        )
                if opcode == "event_whenbroadcastreceived":
                    bc_field = fields.get("BROADCAST_OPTION")
                    if (
                        not isinstance(bc_field, list)
                        or len(bc_field) < 2
                        or bc_field[1] not in stage_broadcast_ids
                    ):
                        errors.append(
                            f"[{t_name}] Block {bid!r} references unknown broadcast {bc_field!r}"
                        )
                if opcode == "sensing_distancetomenu":
                    tgt = fields.get("DISTANCETOMENU", [None])[0]
                    if tgt != "_mouse_" and tgt not in sprite_names:
                        errors.append(
                            f"[{t_name}] Distance menu {bid!r} references unknown target {tgt!r}"
                        )
                if opcode == "sensing_touchingobjectmenu":
                    tgt = fields.get("TOUCHINGOBJECTMENU", [None])[0]
                    if tgt not in ("_mouse_", "_edge_") and tgt not in sprite_names:
                        errors.append(
                            f"[{t_name}] Touching menu {bid!r} references unknown target {tgt!r}"
                        )
                if opcode == "control_create_clone_of_menu":
                    tgt = fields.get("CLONE_OPTION", [None])[0]
                    if tgt != "_myself_" and tgt not in sprite_names:
                        errors.append(
                            f"[{t_name}] Clone menu {bid!r} references unknown target {tgt!r}"
                        )
                for var_name, var_id in _iter_input_var_refs(inputs):
                    if var_id not in target_var_ids:
                        errors.append(
                            f"[{t_name}] Block {bid!r} inline variable {var_name!r} ({var_id!r}) not defined"
                        )
                for bc_name, bc_id in _iter_input_broadcast_refs(inputs):
                    if bc_id not in stage_broadcast_ids:
                        errors.append(
                            f"[{t_name}] Block {bid!r} broadcast {bc_name!r} ({bc_id!r}) not defined on Stage"
                        )

            # Verify bidirectional parent <-> child membership
            for bid, blk in blocks.items():
                parent_id = blk.get("parent")
                if parent_id is not None and parent_id in blocks:
                    if bid not in children_map[parent_id]:
                        errors.append(
                            f"[{t_name}] Orphaned child link: {bid!r} claims parent {parent_id!r}, "
                            f"but parent does not reference {bid!r} in next/inputs"
                        )

            # Cycle detection via parent walk & reachability from topLevel roots
            for bid in blocks:
                seen: Set[str] = set()
                curr: Any = bid
                while curr is not None:
                    if curr in seen:
                        errors.append(
                            f"[{t_name}] Cycle detected in parent chain at block {curr!r}"
                        )
                        break
                    seen.add(curr)
                    if curr not in blocks:
                        break
                    curr = blocks[curr].get("parent")

            reachable: Set[str] = set()
            stack = [bid for bid, _, _ in top_level_coords]
            while stack:
                node_id = stack.pop()
                if node_id in reachable:
                    errors.append(
                        f"[{t_name}] Cycle or shared child detected at block {node_id!r}"
                    )
                    continue
                reachable.add(node_id)
                for child_id in children_map.get(node_id, ()):
                    stack.append(child_id)

            unreachable = set(blocks.keys()) - reachable
            for u_id in sorted(unreachable):
                errors.append(f"[{t_name}] Isolated/unreachable block {u_id!r}")

            # 4. Top-level overlap check
            for i in range(len(top_level_coords)):
                id1, x1, y1 = top_level_coords[i]
                for j in range(i + 1, len(top_level_coords)):
                    id2, x2, y2 = top_level_coords[j]
                    if abs(x1 - x2) < 120 and abs(y1 - y2) < 80:
                        errors.append(
                            f"[{t_name}] Overlapping topLevel blocks: {id1!r} ({x1},{y1}) "
                            f"and {id2!r} ({x2},{y2})"
                        )

            # Comments validation
            comments = target.get("comments", {})
            stats["comments"] += len(comments)
            for cid, cmt in comments.items():
                cbid = cmt.get("blockId")
                if cbid is not None and cbid not in blocks:
                    errors.append(
                        f"[{t_name}] Comment {cid!r} references missing blockId {cbid!r}"
                    )
                cx = cmt.get("x")
                cy = cmt.get("y")
                if isinstance(cx, (int, float)) and isinstance(cy, (int, float)):
                    for bid, bx, by in top_level_coords:
                        if abs(cx - bx) < 100 and abs(cy - by) < 50:
                            errors.append(
                                f"[{t_name}] Comment {cid!r} ({cx},{cy}) overlaps topLevel block {bid!r} ({bx},{by})"
                            )

        # Extension consistency check
        for ext in sorted(used_extensions):
            if ext not in extensions:
                errors.append(
                    f"Extension {ext!r} is used by blocks but missing from project.json 'extensions'"
                )

        # Unreferenced extra files check
        extra_files = zip_names - referenced_assets - {"project.json"}
        for extra in sorted(extra_files):
            warnings.append(f"Unreferenced file in archive: {extra}")

    return ValidationResult(
        path=sb3_path,
        ok=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        stats=stats,
    )


def _validate_asset(
    zf: zipfile.ZipFile,
    zip_names: Set[str],
    referenced_assets: Set[str],
    errors: List[str],
    target_name: str,
    asset_obj: dict,
    kind: str,
) -> None:
    a_name = asset_obj.get("name", "<unnamed>")
    asset_id = asset_obj.get("assetId", "")
    data_format = asset_obj.get("dataFormat", "")
    md5ext = asset_obj.get("md5ext", "")

    if not MD5_RE.match(str(asset_id)):
        errors.append(f"[{target_name}] {kind} {a_name!r} has invalid assetId: {asset_id!r}")
        return

    expected_md5ext = f"{asset_id}.{data_format}"
    if md5ext != expected_md5ext:
        errors.append(
            f"[{target_name}] {kind} {a_name!r} md5ext {md5ext!r} != {expected_md5ext!r}"
        )
        return

    if md5ext not in zip_names:
        errors.append(
            f"[{target_name}] {kind} {a_name!r} file {md5ext!r} missing from .sb3 archive"
        )
        return

    referenced_assets.add(md5ext)
    raw = zf.read(md5ext)
    actual_md5 = hashlib.md5(raw).hexdigest()
    if actual_md5 != asset_id:
        errors.append(
            f"[{target_name}] {kind} {a_name!r} MD5 mismatch: declared {asset_id}, actual {actual_md5}"
        )
        return

    if data_format == "svg":
        try:
            ET.fromstring(raw.decode("utf-8"))
        except Exception as exc:
            errors.append(
                f"[{target_name}] SVG costume {a_name!r} ({md5ext}) XML parse error: {exc}"
            )
    elif data_format == "wav":
        try:
            with wave.open(io.BytesIO(raw), "rb") as wf:
                if wf.getframerate() != asset_obj.get("rate"):
                    errors.append(
                        f"[{target_name}] WAV sound {a_name!r} rate mismatch: "
                        f"json={asset_obj.get('rate')} vs wav={wf.getframerate()}"
                    )
                if wf.getnframes() != asset_obj.get("sampleCount"):
                    errors.append(
                        f"[{target_name}] WAV sound {a_name!r} sampleCount mismatch: "
                        f"json={asset_obj.get('sampleCount')} vs wav={wf.getnframes()}"
                    )
        except Exception as exc:
            errors.append(
                f"[{target_name}] WAV sound {a_name!r} ({md5ext}) decode error: {exc}"
            )
