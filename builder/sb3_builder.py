"""Scratch 3.0 (.sb3) programmatic Project / Target / BlockBuilder module.

Constructs valid Scratch 3.0 project.json structures with automatic parent/next/
topLevel/input/field/shadow block wiring and deterministic ID allocation.
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

from .assets import Asset


# Scratch 3.0 primitive shadow types
SHADOW_NUMBER = 4
SHADOW_POS_NUMBER = 5
SHADOW_POS_INTEGER = 6
SHADOW_INTEGER = 7
SHADOW_ANGLE = 8
SHADOW_COLOR = 9
SHADOW_STRING = 10
SHADOW_BROADCAST = 11
SHADOW_VARIABLE = 12
SHADOW_LIST = 13


@dataclass(frozen=True)
class VarRef:
    """Reference to a Scratch variable."""

    name: str
    var_id: str
    is_stage: bool


@dataclass(frozen=True)
class ListRef:
    """Reference to a Scratch list."""

    name: str
    list_id: str
    is_stage: bool


@dataclass(frozen=True)
class BroadcastRef:
    """Reference to a Scratch broadcast message."""

    name: str
    broadcast_id: str


@dataclass(frozen=True)
class BlockNode:
    """Handle to a block already registered inside a Target's block map."""

    block_id: str
    kind: str  # "statement", "hat", "reporter", "boolean"


ValueExpr = Union[BlockNode, VarRef, int, float, str]
BoolExpr = BlockNode


class _IdGenerator:
    """Deterministic short ID generator compatible with Scratch 3.0."""

    def __init__(self, prefix: str = "id") -> None:
        self._prefix = prefix
        self._counter = 0

    def next(self, tag: str = "") -> str:
        self._counter += 1
        if tag:
            return f"{self._prefix}_{tag}_{self._counter:04d}"
        return f"{self._prefix}_{self._counter:04d}"


class BlockBuilder:
    """High-level Scratch 3.0 block tree builder with automatic link wiring."""

    def __init__(self, target: "Target") -> None:
        self._target = target
        self._project = target.project
        self._attached_ids: set[str] = set()
        self._next_script_x = 48
        self._next_script_y = 48

    # ------------------------------------------------------------------
    # Internal block creation and wiring helpers
    # ------------------------------------------------------------------

    def _new_block(
        self,
        opcode: str,
        kind: str,
        inputs: Optional[dict] = None,
        fields: Optional[dict] = None,
        shadow: bool = False,
        mutation: Optional[dict] = None,
    ) -> BlockNode:
        if opcode.startswith("pen_"):
            self._project.add_extension("pen")

        block_id = self._target._ids.next("blk")
        block: dict[str, Any] = {
            "opcode": opcode,
            "next": None,
            "parent": None,
            "inputs": inputs if inputs is not None else {},
            "fields": fields if fields is not None else {},
            "shadow": shadow,
            "topLevel": False,
        }
        if mutation is not None:
            block["mutation"] = mutation
        self._target.blocks[block_id] = block
        return BlockNode(block_id=block_id, kind=kind)

    def _claim_child(self, child_id: str, parent_id: str) -> None:
        if child_id in self._attached_ids:
            raise ValueError(
                f"Block {child_id!r} is already attached to another parent/script."
            )
        blk = self._target.blocks[child_id]
        blk["parent"] = parent_id
        blk["topLevel"] = False
        blk.pop("x", None)
        blk.pop("y", None)
        self._attached_ids.add(child_id)

    def _encode_value_input(
        self,
        parent_id: str,
        value: ValueExpr,
        shadow_type: int,
        default_literal: str,
    ) -> list:
        if isinstance(value, BlockNode):
            if value.kind not in ("reporter", "boolean"):
                raise ValueError(
                    f"Expected reporter/boolean block for value input, got {value.kind!r}"
                )
            self._claim_child(value.block_id, parent_id)
            return [3, value.block_id, [shadow_type, default_literal]]

        if isinstance(value, VarRef):
            return [
                3,
                [SHADOW_VARIABLE, value.name, value.var_id],
                [shadow_type, default_literal],
            ]

        return [1, [shadow_type, str(value)]]

    def _encode_bool_input(
        self, parent_id: str, cond: Optional[BoolExpr]
    ) -> Optional[list]:
        if cond is None:
            return None
        if not isinstance(cond, BlockNode) or cond.kind != "boolean":
            raise ValueError(f"Expected boolean BlockNode, got {cond!r}")
        self._claim_child(cond.block_id, parent_id)
        return [2, cond.block_id]

    def _attach_shadow_menu(
        self, parent_id: str, menu_opcode: str, field_name: str, field_value: str
    ) -> list:
        menu = self._new_block(
            opcode=menu_opcode,
            kind="reporter",
            fields={field_name: [field_value, None]},
            shadow=True,
        )
        self._claim_child(menu.block_id, parent_id)
        return [1, menu.block_id]

    def _wire_chain(
        self, nodes: Sequence[BlockNode], parent_id: Optional[str]
    ) -> Optional[str]:
        if not nodes:
            return None
        first_id = nodes[0].block_id
        for idx, node in enumerate(nodes):
            if node.kind not in ("statement", "hat"):
                raise ValueError(
                    f"Only statement or hat blocks can be chained in a stack, got {node.kind!r}"
                )
            if idx == 0:
                if parent_id is not None:
                    self._claim_child(node.block_id, parent_id)
                else:
                    if node.block_id in self._attached_ids:
                        raise ValueError(f"Block {node.block_id!r} already attached")
                    self._attached_ids.add(node.block_id)
            else:
                prev_id = nodes[idx - 1].block_id
                self._target.blocks[prev_id]["next"] = node.block_id
                self._claim_child(node.block_id, prev_id)
        return first_id

    # ------------------------------------------------------------------
    # Top-level script placement
    # ------------------------------------------------------------------

    def script(
        self,
        *nodes: BlockNode,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> BlockNode:
        """Assemble a top-level stack of blocks with automatic layout coordinates."""
        if not nodes:
            raise ValueError("script() requires at least one block")
        first_id = self._wire_chain(nodes, parent_id=None)
        assert first_id is not None

        px = self._next_script_x if x is None else int(x)
        py = self._next_script_y if y is None else int(y)
        if x is None:
            self._next_script_x += 440

        top_blk = self._target.blocks[first_id]
        top_blk["topLevel"] = True
        top_blk["parent"] = None
        top_blk["x"] = px
        top_blk["y"] = py
        return nodes[0]

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def when_flag_clicked(self) -> BlockNode:
        return self._new_block("event_whenflagclicked", kind="hat")

    def when_key_pressed(self, key: str = "space") -> BlockNode:
        return self._new_block(
            "event_whenkeypressed",
            kind="hat",
            fields={"KEY_OPTION": [key, None]},
        )

    def when_this_sprite_clicked(self) -> BlockNode:
        return self._new_block("event_whenthisspriteclicked", kind="hat")

    def when_broadcast_received(self, broadcast: BroadcastRef) -> BlockNode:
        return self._new_block(
            "event_whenbroadcastreceived",
            kind="hat",
            fields={"BROADCAST_OPTION": [broadcast.name, broadcast.broadcast_id]},
        )

    def broadcast(self, broadcast: BroadcastRef) -> BlockNode:
        return self._new_block(
            "event_broadcast",
            kind="statement",
            inputs={
                "BROADCAST_INPUT": [
                    1,
                    [SHADOW_BROADCAST, broadcast.name, broadcast.broadcast_id],
                ]
            },
        )

    def broadcast_and_wait(self, broadcast: BroadcastRef) -> BlockNode:
        return self._new_block(
            "event_broadcastandwait",
            kind="statement",
            inputs={
                "BROADCAST_INPUT": [
                    1,
                    [SHADOW_BROADCAST, broadcast.name, broadcast.broadcast_id],
                ]
            },
        )

    # ------------------------------------------------------------------
    # Motion
    # ------------------------------------------------------------------

    def move_steps(self, steps: ValueExpr) -> BlockNode:
        node = self._new_block("motion_movesteps", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["STEPS"] = (
            self._encode_value_input(node.block_id, steps, SHADOW_NUMBER, "10")
        )
        return node

    def turn_right(self, degrees: ValueExpr) -> BlockNode:
        node = self._new_block("motion_turnright", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["DEGREES"] = (
            self._encode_value_input(node.block_id, degrees, SHADOW_NUMBER, "15")
        )
        return node

    def turn_left(self, degrees: ValueExpr) -> BlockNode:
        node = self._new_block("motion_turnleft", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["DEGREES"] = (
            self._encode_value_input(node.block_id, degrees, SHADOW_NUMBER, "15")
        )
        return node

    def go_to_xy(self, x: ValueExpr, y: ValueExpr) -> BlockNode:
        node = self._new_block("motion_gotoxy", kind="statement")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["X"] = self._encode_value_input(node.block_id, x, SHADOW_NUMBER, "0")
        inputs["Y"] = self._encode_value_input(node.block_id, y, SHADOW_NUMBER, "0")
        return node

    def glide_secs_to_xy(
        self, secs: ValueExpr, x: ValueExpr, y: ValueExpr
    ) -> BlockNode:
        node = self._new_block("motion_glidesecstoxy", kind="statement")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["SECS"] = self._encode_value_input(
            node.block_id, secs, SHADOW_NUMBER, "1"
        )
        inputs["X"] = self._encode_value_input(node.block_id, x, SHADOW_NUMBER, "0")
        inputs["Y"] = self._encode_value_input(node.block_id, y, SHADOW_NUMBER, "0")
        return node

    def go_to(self, target_name: str = "_random_") -> BlockNode:
        node = self._new_block("motion_goto", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["TO"] = self._attach_shadow_menu(
            node.block_id, "motion_goto_menu", "TO", target_name
        )
        return node

    def point_towards(self, target_name: str = "_mouse_") -> BlockNode:
        node = self._new_block("motion_pointtowards", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["TOWARDS"] = (
            self._attach_shadow_menu(
                node.block_id, "motion_pointtowards_menu", "TOWARDS", target_name
            )
        )
        return node

    def set_x(self, x: ValueExpr) -> BlockNode:
        node = self._new_block("motion_setx", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["X"] = self._encode_value_input(
            node.block_id, x, SHADOW_NUMBER, "0"
        )
        return node

    def set_y(self, y: ValueExpr) -> BlockNode:
        node = self._new_block("motion_sety", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["Y"] = self._encode_value_input(
            node.block_id, y, SHADOW_NUMBER, "0"
        )
        return node

    def change_x_by(self, dx: ValueExpr) -> BlockNode:
        node = self._new_block("motion_changexby", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["DX"] = self._encode_value_input(
            node.block_id, dx, SHADOW_NUMBER, "10"
        )
        return node

    def change_y_by(self, dy: ValueExpr) -> BlockNode:
        node = self._new_block("motion_changeyby", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["DY"] = self._encode_value_input(
            node.block_id, dy, SHADOW_NUMBER, "10"
        )
        return node

    def point_in_direction(self, direction: ValueExpr) -> BlockNode:
        node = self._new_block("motion_pointindirection", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["DIRECTION"] = (
            self._encode_value_input(node.block_id, direction, SHADOW_ANGLE, "90")
        )
        return node

    def if_on_edge_bounce(self) -> BlockNode:
        return self._new_block("motion_ifonedgebounce", kind="statement")

    def set_rotation_style(self, style: str = "left-right") -> BlockNode:
        if style not in ("left-right", "don't rotate", "all around"):
            raise ValueError(f"Invalid rotation style: {style!r}")
        return self._new_block(
            "motion_setrotationstyle",
            kind="statement",
            fields={"STYLE": [style, None]},
        )

    def x_position(self) -> BlockNode:
        return self._new_block("motion_xposition", kind="reporter")

    def y_position(self) -> BlockNode:
        return self._new_block("motion_yposition", kind="reporter")

    def direction(self) -> BlockNode:
        return self._new_block("motion_direction", kind="reporter")

    # ------------------------------------------------------------------
    # Looks
    # ------------------------------------------------------------------

    def say(self, message: ValueExpr) -> BlockNode:
        node = self._new_block("looks_say", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["MESSAGE"] = (
            self._encode_value_input(node.block_id, message, SHADOW_STRING, "こんにちは！")
        )
        return node

    def say_for_secs(self, message: ValueExpr, secs: ValueExpr) -> BlockNode:
        node = self._new_block("looks_sayforsecs", kind="statement")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["MESSAGE"] = self._encode_value_input(
            node.block_id, message, SHADOW_STRING, "こんにちは！"
        )
        inputs["SECS"] = self._encode_value_input(
            node.block_id, secs, SHADOW_NUMBER, "2"
        )
        return node

    def show(self) -> BlockNode:
        return self._new_block("looks_show", kind="statement")

    def hide(self) -> BlockNode:
        return self._new_block("looks_hide", kind="statement")

    def set_size_to(self, size: ValueExpr) -> BlockNode:
        node = self._new_block("looks_setsizeto", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["SIZE"] = (
            self._encode_value_input(node.block_id, size, SHADOW_NUMBER, "100")
        )
        return node

    def change_size_by(self, delta: ValueExpr) -> BlockNode:
        node = self._new_block("looks_changesizeby", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["CHANGE"] = (
            self._encode_value_input(node.block_id, delta, SHADOW_NUMBER, "10")
        )
        return node

    def looks_size(self) -> BlockNode:
        return self._new_block("looks_size", kind="reporter")

    def switch_costume_to(self, costume_name: str) -> BlockNode:
        node = self._new_block("looks_switchcostumeto", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["COSTUME"] = (
            self._attach_shadow_menu(
                node.block_id, "looks_costume", "COSTUME", costume_name
            )
        )
        return node

    def next_costume(self) -> BlockNode:
        return self._new_block("looks_nextcostume", kind="statement")

    def costume_number(self) -> BlockNode:
        return self._new_block(
            "looks_costumenumbername",
            kind="reporter",
            fields={"NUMBER_NAME": ["number", None]},
        )

    def costume_name(self) -> BlockNode:
        return self._new_block(
            "looks_costumenumbername",
            kind="reporter",
            fields={"NUMBER_NAME": ["name", None]},
        )

    def change_effect_by(self, effect: str, change: ValueExpr) -> BlockNode:
        node = self._new_block(
            "looks_changeeffectby",
            kind="statement",
            fields={"EFFECT": [effect.upper(), None]},
        )
        self._target.blocks[node.block_id]["inputs"]["CHANGE"] = (
            self._encode_value_input(node.block_id, change, SHADOW_NUMBER, "25")
        )
        return node

    def set_effect_to(self, effect: str, value: ValueExpr) -> BlockNode:
        node = self._new_block(
            "looks_seteffectto",
            kind="statement",
            fields={"EFFECT": [effect.upper(), None]},
        )
        self._target.blocks[node.block_id]["inputs"]["VALUE"] = (
            self._encode_value_input(node.block_id, value, SHADOW_NUMBER, "0")
        )
        return node

    def clear_graphic_effects(self) -> BlockNode:
        return self._new_block("looks_cleargraphiceffects", kind="statement")

    def go_to_front_back(self, front_back: str = "front") -> BlockNode:
        if front_back not in ("front", "back"):
            raise ValueError(f"Invalid layer target: {front_back!r}")
        return self._new_block(
            "looks_gotofrontback",
            kind="statement",
            fields={"FRONT_BACK": [front_back, None]},
        )

    # ------------------------------------------------------------------
    # Sound
    # ------------------------------------------------------------------

    def play_sound(self, sound_name: str) -> BlockNode:
        node = self._new_block("sound_play", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["SOUND_MENU"] = (
            self._attach_shadow_menu(
                node.block_id, "sound_sounds_menu", "SOUND_MENU", sound_name
            )
        )
        return node

    def play_sound_until_done(self, sound_name: str) -> BlockNode:
        node = self._new_block("sound_playuntildone", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["SOUND_MENU"] = (
            self._attach_shadow_menu(
                node.block_id, "sound_sounds_menu", "SOUND_MENU", sound_name
            )
        )
        return node

    def stop_all_sounds(self) -> BlockNode:
        return self._new_block("sound_stopallsounds", kind="statement")

    # ------------------------------------------------------------------
    # Control (Loops, Branching, Wait, Clones)
    # ------------------------------------------------------------------

    def wait(self, secs: ValueExpr) -> BlockNode:
        node = self._new_block("control_wait", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["DURATION"] = (
            self._encode_value_input(node.block_id, secs, SHADOW_POS_NUMBER, "1")
        )
        return node

    def wait_until(self, condition: BoolExpr) -> BlockNode:
        node = self._new_block("control_wait_until", kind="statement")
        encoded = self._encode_bool_input(node.block_id, condition)
        if encoded is not None:
            self._target.blocks[node.block_id]["inputs"]["CONDITION"] = encoded
        return node

    def repeat(self, times: ValueExpr, body: Sequence[BlockNode]) -> BlockNode:
        node = self._new_block("control_repeat", kind="statement")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["TIMES"] = self._encode_value_input(
            node.block_id, times, SHADOW_POS_INTEGER, "10"
        )
        first_body = self._wire_chain(body, parent_id=node.block_id)
        if first_body is not None:
            inputs["SUBSTACK"] = [2, first_body]
        return node

    def forever(self, body: Sequence[BlockNode]) -> BlockNode:
        node = self._new_block("control_forever", kind="statement")
        inputs = self._target.blocks[node.block_id]["inputs"]
        first_body = self._wire_chain(body, parent_id=node.block_id)
        if first_body is not None:
            inputs["SUBSTACK"] = [2, first_body]
        return node

    def repeat_until(
        self, condition: BoolExpr, body: Sequence[BlockNode]
    ) -> BlockNode:
        node = self._new_block("control_repeat_until", kind="statement")
        inputs = self._target.blocks[node.block_id]["inputs"]
        encoded_cond = self._encode_bool_input(node.block_id, condition)
        if encoded_cond is not None:
            inputs["CONDITION"] = encoded_cond
        first_body = self._wire_chain(body, parent_id=node.block_id)
        if first_body is not None:
            inputs["SUBSTACK"] = [2, first_body]
        return node

    def if_then(self, condition: BoolExpr, body: Sequence[BlockNode]) -> BlockNode:
        node = self._new_block("control_if", kind="statement")
        inputs = self._target.blocks[node.block_id]["inputs"]
        encoded_cond = self._encode_bool_input(node.block_id, condition)
        if encoded_cond is not None:
            inputs["CONDITION"] = encoded_cond
        first_body = self._wire_chain(body, parent_id=node.block_id)
        if first_body is not None:
            inputs["SUBSTACK"] = [2, first_body]
        return node

    def if_else(
        self,
        condition: BoolExpr,
        then_body: Sequence[BlockNode],
        else_body: Sequence[BlockNode],
    ) -> BlockNode:
        node = self._new_block("control_if_else", kind="statement")
        inputs = self._target.blocks[node.block_id]["inputs"]
        encoded_cond = self._encode_bool_input(node.block_id, condition)
        if encoded_cond is not None:
            inputs["CONDITION"] = encoded_cond
        first_then = self._wire_chain(then_body, parent_id=node.block_id)
        if first_then is not None:
            inputs["SUBSTACK"] = [2, first_then]
        first_else = self._wire_chain(else_body, parent_id=node.block_id)
        if first_else is not None:
            inputs["SUBSTACK2"] = [2, first_else]
        return node

    def stop(self, option: str = "all") -> BlockNode:
        if option not in ("all", "this script", "other scripts in sprite"):
            raise ValueError(f"Invalid stop option: {option!r}")
        hasnext = "true" if option == "other scripts in sprite" else "false"
        return self._new_block(
            "control_stop",
            kind="statement",
            fields={"STOP_OPTION": [option, None]},
            mutation={
                "tagName": "mutation",
                "children": [],
                "hasnext": hasnext,
            },
        )

    def when_start_as_clone(self) -> BlockNode:
        return self._new_block("control_start_as_clone", kind="hat")

    def create_clone_of(self, target_name: str = "_myself_") -> BlockNode:
        node = self._new_block("control_create_clone_of", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["CLONE_OPTION"] = (
            self._attach_shadow_menu(
                node.block_id,
                "control_create_clone_of_menu",
                "CLONE_OPTION",
                target_name,
            )
        )
        return node

    def delete_this_clone(self) -> BlockNode:
        return self._new_block("control_delete_this_clone", kind="statement")

    # ------------------------------------------------------------------
    # Sensing (Keys, Touching, Timer, Distance)
    # ------------------------------------------------------------------

    def key_pressed(self, key: str = "space") -> BlockNode:
        node = self._new_block("sensing_keypressed", kind="boolean")
        self._target.blocks[node.block_id]["inputs"]["KEY_OPTION"] = (
            self._attach_shadow_menu(
                node.block_id, "sensing_keyoptions", "KEY_OPTION", key
            )
        )
        return node

    def touching_color(self, hex_color: str) -> BlockNode:
        node = self._new_block("sensing_touchingcolor", kind="boolean")
        self._target.blocks[node.block_id]["inputs"]["COLOR"] = [
            1,
            [SHADOW_COLOR, hex_color],
        ]
        return node

    def touching_object(self, target_name: str = "_edge_") -> BlockNode:
        node = self._new_block("sensing_touchingobject", kind="boolean")
        self._target.blocks[node.block_id]["inputs"]["TOUCHINGOBJECTMENU"] = (
            self._attach_shadow_menu(
                node.block_id,
                "sensing_touchingobjectmenu",
                "TOUCHINGOBJECTMENU",
                target_name,
            )
        )
        return node

    def distance_to(self, target_name: str = "_mouse_") -> BlockNode:
        node = self._new_block("sensing_distanceto", kind="reporter")
        self._target.blocks[node.block_id]["inputs"]["DISTANCETOMENU"] = (
            self._attach_shadow_menu(
                node.block_id,
                "sensing_distancetomenu",
                "DISTANCETOMENU",
                target_name,
            )
        )
        return node

    def timer(self) -> BlockNode:
        return self._new_block("sensing_timer", kind="reporter")

    def reset_timer(self) -> BlockNode:
        return self._new_block("sensing_resettimer", kind="statement")

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def _binary_math(
        self, opcode: str, left: ValueExpr, right: ValueExpr
    ) -> BlockNode:
        node = self._new_block(opcode, kind="reporter")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["NUM1"] = self._encode_value_input(node.block_id, left, SHADOW_NUMBER, "")
        inputs["NUM2"] = self._encode_value_input(node.block_id, right, SHADOW_NUMBER, "")
        return node

    def add(self, left: ValueExpr, right: ValueExpr) -> BlockNode:
        return self._binary_math("operator_add", left, right)

    def subtract(self, left: ValueExpr, right: ValueExpr) -> BlockNode:
        return self._binary_math("operator_subtract", left, right)

    def multiply(self, left: ValueExpr, right: ValueExpr) -> BlockNode:
        return self._binary_math("operator_multiply", left, right)

    def divide(self, left: ValueExpr, right: ValueExpr) -> BlockNode:
        return self._binary_math("operator_divide", left, right)

    def mod(self, left: ValueExpr, right: ValueExpr) -> BlockNode:
        return self._binary_math("operator_mod", left, right)

    def round_num(self, num: ValueExpr) -> BlockNode:
        node = self._new_block("operator_round", kind="reporter")
        self._target.blocks[node.block_id]["inputs"]["NUM"] = (
            self._encode_value_input(node.block_id, num, SHADOW_NUMBER, "")
        )
        return node

    def join(self, left: ValueExpr, right: ValueExpr) -> BlockNode:
        node = self._new_block("operator_join", kind="reporter")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["STRING1"] = self._encode_value_input(
            node.block_id, left, SHADOW_STRING, "りんご"
        )
        inputs["STRING2"] = self._encode_value_input(
            node.block_id, right, SHADOW_STRING, "バナナ"
        )
        return node

    def _compare(self, opcode: str, left: ValueExpr, right: ValueExpr) -> BlockNode:
        node = self._new_block(opcode, kind="boolean")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["OPERAND1"] = self._encode_value_input(
            node.block_id, left, SHADOW_STRING, ""
        )
        inputs["OPERAND2"] = self._encode_value_input(
            node.block_id, right, SHADOW_STRING, "50"
        )
        return node

    def gt(self, left: ValueExpr, right: ValueExpr) -> BlockNode:
        return self._compare("operator_gt", left, right)

    def lt(self, left: ValueExpr, right: ValueExpr) -> BlockNode:
        return self._compare("operator_lt", left, right)

    def eq(self, left: ValueExpr, right: ValueExpr) -> BlockNode:
        return self._compare("operator_equals", left, right)

    def logical_and(self, left: BoolExpr, right: BoolExpr) -> BlockNode:
        node = self._new_block("operator_and", kind="boolean")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["OPERAND1"] = self._encode_bool_input(node.block_id, left)
        inputs["OPERAND2"] = self._encode_bool_input(node.block_id, right)
        return node

    def logical_or(self, left: BoolExpr, right: BoolExpr) -> BlockNode:
        node = self._new_block("operator_or", kind="boolean")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["OPERAND1"] = self._encode_bool_input(node.block_id, left)
        inputs["OPERAND2"] = self._encode_bool_input(node.block_id, right)
        return node

    def logical_not(self, operand: BoolExpr) -> BlockNode:
        node = self._new_block("operator_not", kind="boolean")
        self._target.blocks[node.block_id]["inputs"]["OPERAND"] = (
            self._encode_bool_input(node.block_id, operand)
        )
        return node

    def math_op(self, operator: str, num: ValueExpr) -> BlockNode:
        node = self._new_block(
            "operator_mathop",
            kind="reporter",
            fields={"OPERATOR": [operator, None]},
        )
        self._target.blocks[node.block_id]["inputs"]["NUM"] = (
            self._encode_value_input(node.block_id, num, SHADOW_NUMBER, "0")
        )
        return node

    def pick_random(self, from_val: ValueExpr, to_val: ValueExpr) -> BlockNode:
        node = self._new_block("operator_random", kind="reporter")
        inputs = self._target.blocks[node.block_id]["inputs"]
        inputs["FROM"] = self._encode_value_input(
            node.block_id, from_val, SHADOW_NUMBER, "1"
        )
        inputs["TO"] = self._encode_value_input(
            node.block_id, to_val, SHADOW_NUMBER, "10"
        )
        return node

    # ------------------------------------------------------------------
    # Data (Variables & Lists)
    # ------------------------------------------------------------------

    def set_variable(self, var: VarRef, value: ValueExpr) -> BlockNode:
        node = self._new_block(
            "data_setvariableto",
            kind="statement",
            fields={"VARIABLE": [var.name, var.var_id]},
        )
        self._target.blocks[node.block_id]["inputs"]["VALUE"] = (
            self._encode_value_input(node.block_id, value, SHADOW_STRING, "0")
        )
        return node

    def change_variable(self, var: VarRef, delta: ValueExpr) -> BlockNode:
        node = self._new_block(
            "data_changevariableby",
            kind="statement",
            fields={"VARIABLE": [var.name, var.var_id]},
        )
        self._target.blocks[node.block_id]["inputs"]["VALUE"] = (
            self._encode_value_input(node.block_id, delta, SHADOW_NUMBER, "1")
        )
        return node

    def show_variable(self, var: VarRef) -> BlockNode:
        return self._new_block(
            "data_showvariable",
            kind="statement",
            fields={"VARIABLE": [var.name, var.var_id]},
        )

    def hide_variable(self, var: VarRef) -> BlockNode:
        return self._new_block(
            "data_hidevariable",
            kind="statement",
            fields={"VARIABLE": [var.name, var.var_id]},
        )

    def add_to_list(self, lst: ListRef, item: ValueExpr) -> BlockNode:
        node = self._new_block(
            "data_addtolist",
            kind="statement",
            fields={"LIST": [lst.name, lst.list_id]},
        )
        self._target.blocks[node.block_id]["inputs"]["ITEM"] = (
            self._encode_value_input(node.block_id, item, SHADOW_STRING, "なにか")
        )
        return node

    def delete_of_list(self, lst: ListRef, index: ValueExpr) -> BlockNode:
        node = self._new_block(
            "data_deleteoflist",
            kind="statement",
            fields={"LIST": [lst.name, lst.list_id]},
        )
        self._target.blocks[node.block_id]["inputs"]["INDEX"] = (
            self._encode_value_input(node.block_id, index, SHADOW_INTEGER, "1")
        )
        return node

    def delete_all_of_list(self, lst: ListRef) -> BlockNode:
        return self._new_block(
            "data_deletealloflist",
            kind="statement",
            fields={"LIST": [lst.name, lst.list_id]},
        )

    def item_of_list(self, lst: ListRef, index: ValueExpr) -> BlockNode:
        node = self._new_block(
            "data_itemoflist",
            kind="reporter",
            fields={"LIST": [lst.name, lst.list_id]},
        )
        self._target.blocks[node.block_id]["inputs"]["INDEX"] = (
            self._encode_value_input(node.block_id, index, SHADOW_INTEGER, "1")
        )
        return node

    def length_of_list(self, lst: ListRef) -> BlockNode:
        return self._new_block(
            "data_lengthoflist",
            kind="reporter",
            fields={"LIST": [lst.name, lst.list_id]},
        )

    def list_contains_item(self, lst: ListRef, item: ValueExpr) -> BlockNode:
        node = self._new_block(
            "data_listcontainsitem",
            kind="boolean",
            fields={"LIST": [lst.name, lst.list_id]},
        )
        self._target.blocks[node.block_id]["inputs"]["ITEM"] = (
            self._encode_value_input(node.block_id, item, SHADOW_STRING, "なにか")
        )
        return node

    # ------------------------------------------------------------------
    # Pen Extension
    # ------------------------------------------------------------------

    def pen_clear(self) -> BlockNode:
        return self._new_block("pen_clear", kind="statement")

    def pen_stamp(self) -> BlockNode:
        return self._new_block("pen_stamp", kind="statement")

    def pen_down(self) -> BlockNode:
        return self._new_block("pen_penDown", kind="statement")

    def pen_up(self) -> BlockNode:
        return self._new_block("pen_penUp", kind="statement")

    def pen_set_color(self, hex_color: str) -> BlockNode:
        node = self._new_block("pen_setPenColorToColor", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["COLOR"] = [
            1,
            [SHADOW_COLOR, hex_color],
        ]
        return node

    def pen_set_size(self, size: ValueExpr) -> BlockNode:
        node = self._new_block("pen_setPenSizeTo", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["SIZE"] = (
            self._encode_value_input(node.block_id, size, SHADOW_NUMBER, "1")
        )
        return node

    def pen_change_size(self, delta: ValueExpr) -> BlockNode:
        node = self._new_block("pen_changePenSizeBy", kind="statement")
        self._target.blocks[node.block_id]["inputs"]["SIZE"] = (
            self._encode_value_input(node.block_id, delta, SHADOW_NUMBER, "1")
        )
        return node


class Target:
    """Represents either the Scratch Stage or a Sprite target."""

    def __init__(
        self,
        project: "Project",
        name: str,
        is_stage: bool,
        layer_order: int,
        x: float = 0,
        y: float = 0,
        size: float = 100,
        direction: float = 90,
        visible: bool = True,
        draggable: bool = False,
        rotation_style: str = "all around",
    ) -> None:
        self.project = project
        self.name = name
        self.is_stage = is_stage
        self.layer_order = layer_order
        self.x = x
        self.y = y
        self.size = size
        self.direction = direction
        self.visible = visible
        self.draggable = draggable
        self.rotation_style = rotation_style

        self._ids = _IdGenerator(prefix="stg" if is_stage else f"spr{layer_order}")
        self.variables: dict[str, list[Any]] = {}
        self.lists: dict[str, list[Any]] = {}
        self.broadcasts: dict[str, str] = {}
        self.blocks: dict[str, dict[str, Any]] = {}
        self.comments: dict[str, dict[str, Any]] = {}
        self.costumes: list[Asset] = []
        self.sounds: list[Asset] = []
        self.current_costume = 0
        self.volume = 100
        self._builder = BlockBuilder(self)

    @property
    def builder(self) -> BlockBuilder:
        return self._builder

    def add_costume(self, asset: Asset) -> Asset:
        if asset.data_format != "svg":
            raise ValueError("Only SVG costumes are supported by this pipeline")
        self.costumes.append(asset)
        self.project._register_asset(asset)
        return asset

    def add_sound(self, asset: Asset) -> Asset:
        if asset.data_format != "wav":
            raise ValueError("Only WAV sounds are supported by this pipeline")
        self.sounds.append(asset)
        self.project._register_asset(asset)
        return asset

    def add_variable(
        self,
        name: str,
        initial_value: Union[int, float, str] = 0,
        show_monitor: bool = False,
        monitor_x: int = 8,
        monitor_y: int = 8,
    ) -> VarRef:
        var_id = self._ids.next("var")
        self.variables[var_id] = [name, initial_value]
        if show_monitor:
            self.project.monitors.append(
                {
                    "id": var_id,
                    "mode": "default",
                    "opcode": "data_variable",
                    "params": {"VARIABLE": name},
                    "spriteName": None if self.is_stage else self.name,
                    "value": initial_value,
                    "width": 0,
                    "height": 0,
                    "x": monitor_x,
                    "y": monitor_y,
                    "visible": True,
                    "sliderMin": 0,
                    "sliderMax": 100,
                    "isDiscrete": True,
                }
            )
        return VarRef(name=name, var_id=var_id, is_stage=self.is_stage)

    def add_list(
        self,
        name: str,
        initial_items: Optional[Sequence[Any]] = None,
        show_monitor: bool = False,
        monitor_x: int = 8,
        monitor_y: int = 8,
        width: int = 120,
        height: int = 160,
    ) -> ListRef:
        list_id = self._ids.next("lst")
        items = list(initial_items) if initial_items is not None else []
        self.lists[list_id] = [name, items]
        if show_monitor:
            self.project.monitors.append(
                {
                    "id": list_id,
                    "mode": "list",
                    "opcode": "data_listcontents",
                    "params": {"LIST": name},
                    "spriteName": None if self.is_stage else self.name,
                    "value": items,
                    "width": width,
                    "height": height,
                    "x": monitor_x,
                    "y": monitor_y,
                    "visible": True,
                }
            )
        return ListRef(name=name, list_id=list_id, is_stage=self.is_stage)

    def add_broadcast(self, name: str) -> BroadcastRef:
        """Register a broadcast on the Stage (Scratch 3.0 stores all broadcasts on Stage)."""
        return self.project.add_broadcast(name)

    def add_comment(
        self,
        text: str,
        x: int = 420,
        y: int = 48,
        width: int = 300,
        height: int = 190,
        block: Optional[BlockNode] = None,
        minimized: bool = False,
    ) -> str:
        comment_id = self._ids.next("cmt")
        block_id = block.block_id if block is not None else None
        if block_id is not None and block_id not in self.blocks:
            raise ValueError(f"Comment references unknown block ID {block_id!r}")
        self.comments[comment_id] = {
            "blockId": block_id,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "minimized": minimized,
            "text": text,
        }
        return comment_id

    def to_dict(self) -> dict[str, Any]:
        if not self.costumes:
            raise ValueError(f"Target {self.name!r} must have at least one costume")

        base: dict[str, Any] = {
            "isStage": self.is_stage,
            "name": self.name,
            "variables": self.variables,
            "lists": self.lists,
            "broadcasts": self.broadcasts,
            "blocks": self.blocks,
            "comments": self.comments,
            "currentCostume": self.current_costume,
            "costumes": [c.to_costume_dict() for c in self.costumes],
            "sounds": [s.to_sound_dict() for s in self.sounds],
            "volume": self.volume,
            "layerOrder": self.layer_order,
        }
        if self.is_stage:
            base.update(
                {
                    "tempo": 60,
                    "videoTransparency": 50,
                    "videoState": "on",
                    "textToSpeechLanguage": None,
                }
            )
        else:
            base.update(
                {
                    "visible": self.visible,
                    "x": self.x,
                    "y": self.y,
                    "size": self.size,
                    "direction": self.direction,
                    "draggable": self.draggable,
                    "rotationStyle": self.rotation_style,
                }
            )
        return base


class Project:
    """Top-level Scratch 3.0 project container that writes valid .sb3 archives."""

    def __init__(self) -> None:
        self.stage = Target(self, name="Stage", is_stage=True, layer_order=0)
        self.sprites: List[Target] = []
        self.monitors: List[dict[str, Any]] = []
        self.extensions: List[str] = []
        self._assets_by_md5ext: dict[str, Asset] = {}

    def _register_asset(self, asset: Asset) -> None:
        existing = self._assets_by_md5ext.get(asset.md5ext)
        if existing is not None and existing.data != asset.data:
            raise ValueError(f"MD5 collision detected for {asset.md5ext}")
        self._assets_by_md5ext[asset.md5ext] = asset

    def add_extension(self, extension_id: str) -> None:
        if extension_id not in self.extensions:
            self.extensions.append(extension_id)

    def add_broadcast(self, name: str) -> BroadcastRef:
        for existing_id, existing_name in self.stage.broadcasts.items():
            if existing_name == name:
                return BroadcastRef(name=name, broadcast_id=existing_id)
        bc_id = self.stage._ids.next("bc")
        self.stage.broadcasts[bc_id] = name
        return BroadcastRef(name=name, broadcast_id=bc_id)

    def show_timer_monitor(
        self, visible: bool = True, x: int = 8, y: int = 8
    ) -> None:
        """Add or update the built-in sensing_timer monitor on the stage."""
        for m in self.monitors:
            if m.get("id") == "timer":
                m["visible"] = visible
                m["x"] = x
                m["y"] = y
                return
        self.monitors.append(
            {
                "id": "timer",
                "mode": "default",
                "opcode": "sensing_timer",
                "params": {},
                "spriteName": None,
                "value": 0,
                "width": 0,
                "height": 0,
                "x": x,
                "y": y,
                "visible": visible,
                "sliderMin": 0,
                "sliderMax": 100,
                "isDiscrete": True,
            }
        )

    def add_sprite(
        self,
        name: str,
        x: float = 0,
        y: float = 0,
        size: float = 100,
        direction: float = 90,
        visible: bool = True,
        draggable: bool = False,
        rotation_style: str = "all around",
    ) -> Target:
        layer_order = len(self.sprites) + 1
        sprite = Target(
            self,
            name=name,
            is_stage=False,
            layer_order=layer_order,
            x=x,
            y=y,
            size=size,
            direction=direction,
            visible=visible,
            draggable=draggable,
            rotation_style=rotation_style,
        )
        self.sprites.append(sprite)
        return sprite

    def to_dict(self) -> dict[str, Any]:
        targets = [self.stage.to_dict()] + [s.to_dict() for s in self.sprites]
        return {
            "targets": targets,
            "monitors": self.monitors,
            "extensions": self.extensions,
            "meta": {
                "semver": "3.0.0",
                "vm": "0.2.0",
                "agent": "Scratch3-SB3-Builder/1.1",
            },
        }

    def save(self, output_path: Union[str, Path]) -> Path:
        """Write project.json and all MD5-hashed assets into an .sb3 ZIP archive."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        project_json_bytes = json.dumps(
            self.to_dict(), ensure_ascii=False, indent=2
        ).encode("utf-8")

        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("project.json", project_json_bytes)
            for md5ext, asset in sorted(self._assets_by_md5ext.items()):
                zf.writestr(md5ext, asset.data)

        return out
