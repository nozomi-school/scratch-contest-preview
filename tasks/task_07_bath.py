"""Task 07: お風呂の自動お湯はり (07_bath)

水位がじわじわ上がり、満タンラインに達したら自動停止して完了音を鳴らす課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_chime_bath

TASK_ID = "07_bath"
TASK_TITLE = "おふろのじどうおゆはり"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

INITIAL_WATER_Y = -140
FULL_LINE_Y = 20  # Scratch Y=20 -> SVG y = 180 - 20 = 160


def _make_bath_backdrop_svg() -> str:
    """Create a 480x360 bathroom & cross-section bathtub SVG with full-water line at y=20."""
    tile_lines: list[str] = []
    for x in range(0, 481, 40):
        tile_lines.append(f'    <line x1="{x}" y1="0" x2="{x}" y2="360"/>')
    for y in range(0, 361, 40):
        tile_lines.append(f'    <line x1="0" y1="{y}" x2="480" y2="{y}"/>')
    tiles_svg = "\n".join(tile_lines)

    # Scratch y=20 corresponds to SVG y=160
    full_svg_y = 180 - FULL_LINE_Y
    init_svg_y = 180 - INITIAL_WATER_Y  # 320

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- 浴室タイル背景 -->
  <rect x="0" y="0" width="480" height="360" fill="#eef7ff"/>
  <g stroke="#d5e8fa" stroke-width="1.5">
{tiles_svg}
  </g>

  <!-- タイトル帯 -->
  <rect x="108" y="12" width="264" height="34" rx="17" fill="#ffffff" stroke="#3b82f6" stroke-width="2"/>
  <text x="240" y="35" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="17" font-weight="bold" fill="#1d4ed8">おふろ の じどう おゆはり</text>

  <!-- じゃぐち（左上） -->
  <g>
    <rect x="64" y="66" width="14" height="28" rx="4" fill="#94a3b8" stroke="#475569" stroke-width="2"/>
    <path d="M 78 76 L 122 76 Q 134 76 134 88 L 134 98 L 122 98 L 122 88 L 78 88 Z" fill="#cbd5e1" stroke="#475569" stroke-width="2"/>
    <!-- レバー -->
    <rect x="86" y="62" width="24" height="7" rx="3" fill="#60a5fa" stroke="#2563eb" stroke-width="1.5"/>
    <!-- しずく -->
    <path d="M 128 103 C 128 103 122 112 122 116 C 122 119.5 124.7 122 128 122 C 131.3 122 134 119.5 134 116 C 134 112 128 103 128 103 Z" fill="#38bdf8" opacity="0.85"/>
  </g>

  <!-- 浴槽の後ろ壁（内側） -->
  <rect x="82" y="114" width="316" height="246" fill="#ffffff"/>
  <!-- 浴槽の左右壁・フチ -->
  <rect x="64" y="114" width="18" height="246" fill="#e2e8f0" stroke="#64748b" stroke-width="2"/>
  <rect x="398" y="114" width="18" height="246" fill="#e2e8f0" stroke="#64748b" stroke-width="2"/>
  <rect x="56" y="106" width="368" height="14" rx="7" fill="#f8fafc" stroke="#64748b" stroke-width="2"/>

  <!-- スタート位置めやす線 (y = -140) -->
  <line x1="84" y1="{init_svg_y}" x2="396" y2="{init_svg_y}" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 4"/>
  <text x="14" y="{init_svg_y + 4}" font-family="{FONT_FAMILY}" font-size="11" fill="#64748b">y=-140</text>

  <!-- まんたんライン (y = 20 -> SVG y = 160) -->
  <line x1="78" y1="{full_svg_y}" x2="402" y2="{full_svg_y}" stroke="#ef4444" stroke-width="3" stroke-dasharray="8 5"/>
  <polygon points="404,{full_svg_y} 414,{full_svg_y - 6} 414,{full_svg_y + 6}" fill="#ef4444"/>
  <rect x="415" y="{full_svg_y - 18}" width="62" height="36" rx="6" fill="#fef2f2" stroke="#ef4444" stroke-width="1.8"/>
  <text x="446" y="{full_svg_y - 2}" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="11" font-weight="bold" fill="#dc2626">まんたん</text>
  <text x="446" y="{full_svg_y + 12}" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="10" font-weight="bold" fill="#dc2626">y = {FULL_LINE_Y}</text>
  <text x="18" y="{full_svg_y + 4}" font-family="{FONT_FAMILY}" font-size="11" font-weight="bold" fill="#dc2626">y={FULL_LINE_Y}</text>
</svg>"""


def _make_water_sprite_svg() -> str:
    """Create a 314x220 semi-transparent bath water sprite whose top wave sits at rotationCenterY=6."""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="314" height="220" viewBox="0 0 314 220">
  <!-- 半透明のお湯本体（背面のまんたんラインも透けて見える） -->
  <path d="M 0 8 Q 39 0 78 8 T 157 8 T 236 8 T 314 8 L 314 220 L 0 220 Z" fill="#38bdf8" fill-opacity="0.68"/>
  <!-- 水面のきらめきライン -->
  <path d="M 0 8 Q 39 0 78 8 T 157 8 T 236 8 T 314 8" fill="none" stroke="#0284c7" stroke-width="3"/>
  <path d="M 14 14 Q 46 8 78 14" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" opacity="0.8"/>
  <path d="M 164 14 Q 196 8 228 14" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" opacity="0.8"/>
  <!-- あわ・ゆらぎ -->
  <circle cx="62" cy="48" r="6" fill="#ffffff" opacity="0.45"/>
  <circle cx="76" cy="64" r="4" fill="#ffffff" opacity="0.45"/>
  <circle cx="242" cy="54" r="7" fill="#ffffff" opacity="0.45"/>
  <circle cx="228" cy="76" r="4" fill="#ffffff" opacity="0.45"/>
  <circle cx="156" cy="96" r="5" fill="#ffffff" opacity="0.35"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("おふろのはいけい", _make_bath_backdrop_svg(), 240, 180)
    )

    water = proj.add_sprite(
        name="おゆ",
        x=0,
        y=INITIAL_WATER_Y,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    # rotationCenterY=6 places the water surface right at the sprite's Y coordinate!
    water.add_costume(make_svg_costume("おゆのすいめん", _make_water_sprite_svg(), 157, 6))
    water.add_sound(synth_chime_bath("かんりょうおん"))
    return proj, water, water.builder


def build_template() -> Project:
    """Build remix template with bathtub backdrop, water sprite, chime sound, and init block."""
    proj, water, b = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, INITIAL_WATER_Y),
    )

    water.add_comment(
        text=(
            "【ヒント：じどう おゆはり】\n"
            "「yざひょう ＞ 19 まで くりかえす」の なかで：\n"
            "  ・yざひょう を 2 ずつ かえる\n"
            "  ・0.05 びょう まつ\n"
            "を いれると、じわじわ おゆが たまるよ！\n\n"
            "まんたん（y = 20）に ついたら：\n"
            "  ・おわるまで「かんりょうおん」のおとを ならす\n"
            "  ・「おふろが わきました！」と いう\n"
            "  ・このスクリプト を とめる"
        ),
        x=380,
        y=48,
        width=320,
        height=230,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working reference solution that raises water smoothly and chimes when full."""
    proj, water, b = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, INITIAL_WATER_Y),
        b.repeat_until(
            b.gt(b.y_position(), FULL_LINE_Y - 1),
            [
                b.change_y_by(2),
                b.wait(0.05),
            ],
        ),
        b.play_sound_until_done("かんりょうおん"),
        b.say_for_secs("おふろが わきました！", 3),
        b.stop("this script"),
    )

    water.add_comment(
        text=(
            "【おてほん】\n"
            "y = -140 から スタートして、\n"
            "まんたんライン (y = 20) に つくまで\n"
            "じわじわ あがり、ついたら チャイムを ならして とまります。"
        ),
        x=380,
        y=48,
        width=300,
        height=135,
        block=hat,
    )
    return proj
