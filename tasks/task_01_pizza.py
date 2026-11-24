"""Task 01: ピザを〇等分 (01_pizza)

円の中心から角度を等分（初期値8等分）して切り込み線を引く課題。
"""

from __future__ import annotations

import math

from builder import Project, make_svg_costume

TASK_ID = "01_pizza"
TASK_TITLE = "ピザを〇とうぶん"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"


def _make_pizza_backdrop_svg() -> str:
    """Create a 480x360 wooden table + round pizza centered at (240, 180)."""
    cx, cy = 240, 180

    # Symmetrical toppings placed neatly inside the 8 slices (offset by 22.5 deg)
    toppings: list[str] = []
    for i in range(8):
        angle_rad = math.radians(i * 45 + 22.5)
        # Pepperoni
        px = cx + 66 * math.cos(angle_rad)
        py = cy + 66 * math.sin(angle_rad)
        toppings.append(
            f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="13" fill="#d93829" stroke="#a62217" stroke-width="2"/>'
        )
        # Inner smaller pepperoni / tomato accent on alternating slices
        if i % 2 == 0:
            ix = cx + 34 * math.cos(angle_rad)
            iy = cy + 34 * math.sin(angle_rad)
            toppings.append(
                f'  <circle cx="{ix:.1f}" cy="{iy:.1f}" r="8" fill="#4aa94a" stroke="#2d7a2d" stroke-width="2"/>'
            )
        else:
            ix = cx + 36 * math.cos(angle_rad)
            iy = cy + 36 * math.sin(angle_rad)
            toppings.append(
                f'  <ellipse cx="{ix:.1f}" cy="{iy:.1f}" rx="9" ry="6" '
                f'transform="rotate({i * 45 + 22.5:.1f} {ix:.1f} {iy:.1f})" '
                f'fill="#fff3d6" stroke="#d4b886" stroke-width="1.5"/>'
            )

    toppings_svg = "\n".join(toppings)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- 木目テーブル背景 -->
  <rect x="0" y="0" width="480" height="360" fill="#f6e7cb"/>
  <g stroke="#e9d2aa" stroke-width="2" opacity="0.65">
    <line x1="0" y1="45" x2="480" y2="45"/>
    <line x1="0" y1="105" x2="480" y2="105"/>
    <line x1="0" y1="165" x2="480" y2="165"/>
    <line x1="0" y1="225" x2="480" y2="225"/>
    <line x1="0" y1="285" x2="480" y2="285"/>
    <line x1="0" y1="340" x2="480" y2="340"/>
  </g>

  <!-- タイトル帯 -->
  <rect x="132" y="10" width="216" height="32" rx="16" fill="#ffffff" stroke="#d99b43" stroke-width="2"/>
  <text x="240" y="32" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="17" font-weight="bold" fill="#7c3f00">ピザを 8とうぶん しよう！</text>

  <!-- ピザのお皿・影 -->
  <circle cx="{cx + 4}" cy="{cy + 6}" r="130" fill="#000000" opacity="0.12"/>
  <circle cx="{cx}" cy="{cy}" r="130" fill="#ffffff" stroke="#e2d6c3" stroke-width="3"/>

  <!-- ピザ生地（みみ） -->
  <circle cx="{cx}" cy="{cy}" r="120" fill="#e59a45" stroke="#c07323" stroke-width="3"/>
  <!-- トマトソース -->
  <circle cx="{cx}" cy="{cy}" r="105" fill="#e04832"/>
  <!-- とろけるチーズ -->
  <circle cx="{cx}" cy="{cy}" r="99" fill="#ffd666"/>

  <!-- トッピング -->
{toppings_svg}

  <!-- まんなか目印 -->
  <circle cx="{cx}" cy="{cy}" r="4" fill="#7c3f00" opacity="0.7"/>

  <!-- 下部ガイド -->
  <text x="240" y="344" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" fill="#7c562c">まんなか (0, 0) から 8ほん の せん を ひこう！</text>
</svg>"""


def _make_cutter_svg() -> str:
    """Create a 48x48 pizza cutter sprite centered at (24, 24), pointing right (+X)."""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <!-- 持ち手（左側から中心へ） -->
  <rect x="3" y="19" width="18" height="10" rx="5" fill="#e11d48" stroke="#881337" stroke-width="2"/>
  <!-- 金具アーム -->
  <rect x="19" y="21" width="9" height="6" rx="2" fill="#94a3b8" stroke="#475569" stroke-width="1.5"/>
  <!-- 銀色の丸刃（中心が (24,24) ではなく刃の先端寄りでも見やすいよう中心配置） -->
  <circle cx="24" cy="24" r="10" fill="#e2e8f0" stroke="#334155" stroke-width="2"/>
  <circle cx="24" cy="24" r="3.5" fill="#e11d48"/>
  <!-- 進む向きを示す小さな三角 -->
  <polygon points="37,19 45,24 37,29" fill="#e11d48" stroke="#ffffff" stroke-width="1.5"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object]:
    """Create shared stage, assets, variables, extension, and sprite."""
    proj = Project()
    proj.add_extension("pen")

    proj.stage.add_costume(
        make_svg_costume("ピザのはいけい", _make_pizza_backdrop_svg(), 240, 180)
    )
    proj.stage.add_variable("なんとうぶん", 8, show_monitor=True, monitor_x=8, monitor_y=8)

    cutter = proj.add_sprite(
        name="ピザカッター",
        x=0,
        y=0,
        size=85,
        direction=90,
        rotation_style="all around",
    )
    cutter.add_costume(make_svg_costume("カッター", _make_cutter_svg(), 24, 24))
    return proj, cutter, cutter.builder


def build_template() -> Project:
    """Build remix template with assets, pen extension, init blocks, and angle hint."""
    proj, cutter, b = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.pen_clear(),
        b.pen_up(),
        b.pen_set_color("#3b1e08"),
        b.pen_set_size(4),
        b.go_to_xy(0, 0),
        b.point_in_direction(90),
    )

    cutter.add_comment(
        text=(
            "【ヒント：かくど の けいさん】\n"
            "ピザの まる は 1しゅう 360ど だよ！\n"
            "8とうぶん する ときは：\n"
            "  360 ÷ 8 ＝ 45ど ずつ まわそう。\n\n"
            "つぎの ブロックを「8かい くりかえす」に\n"
            "いれて、したに つなげて みよう：\n"
            "・ペンをおろす\n"
            "・120ぽ うごかす\n"
            "・ペンをあげる\n"
            "・xざひょうを 0、yざひょうを 0 にする\n"
            "・みぎに 45ど まわす"
        ),
        x=380,
        y=48,
        width=310,
        height=245,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working reference solution cutting the pizza cleanly into 8 slices."""
    proj, cutter, b = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.pen_clear(),
        b.pen_up(),
        b.pen_set_color("#3b1e08"),
        b.pen_set_size(4),
        b.go_to_xy(0, 0),
        b.point_in_direction(90),
        b.repeat(
            8,
            [
                b.pen_down(),
                b.move_steps(120),
                b.pen_up(),
                b.go_to_xy(0, 0),
                b.turn_right(45),
            ],
        ),
    )

    cutter.add_comment(
        text=(
            "【おてほん】\n"
            "1しゅう 360ど ÷ 8 ＝ 45ど ずつ まわしながら\n"
            "まんなか (0, 0) から 120ぽ せんを ひきます。"
        ),
        x=380,
        y=48,
        width=280,
        height=120,
        block=hat,
    )
    return proj
