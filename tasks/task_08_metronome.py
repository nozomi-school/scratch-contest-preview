"""Task 08: 4拍子メトロノーム (08_metronome)

針を左右に振りつつ4回に1回だけ高い音を鳴らす課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_tick_high, synth_tick_low

TASK_ID = "08_metronome"
TASK_TITLE = "4びょうし メトロノーム"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

PIVOT_X = 0
PIVOT_Y = -110  # Scratch y=-110 -> SVG y=290


def _make_metronome_backdrop_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- 音楽室ふう背景 -->
  <rect x="0" y="0" width="480" height="360" fill="#fdf4ff"/>

  <!-- タイトル帯 -->
  <rect x="116" y="10" width="248" height="32" rx="16" fill="#ffffff" stroke="#9333ea" stroke-width="2"/>
  <text x="240" y="32" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="16" font-weight="bold" fill="#6b21a8">4びょうし メトロノーム</text>

  <!-- メトロノーム本体台形 -->
  <polygon points="180,68 300,68 346,322 134,322" fill="#b45309" stroke="#78350f" stroke-width="3.5" stroke-linejoin="round"/>
  <!-- 内側パネル -->
  <polygon points="196,86 284,86 306,296 174,296" fill="#fef3c7" stroke="#92400e" stroke-width="2"/>

  <!-- 目盛りの線 -->
  <g stroke="#d97706" stroke-width="1.5" opacity="0.7">
    <line x1="216" y1="120" x2="264" y2="120"/>
    <line x1="210" y1="155" x2="270" y2="155"/>
    <line x1="204" y1="190" x2="276" y2="190"/>
    <line x1="198" y1="225" x2="282" y2="225"/>
  </g>
  <text x="240" y="108" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="11" font-weight="bold" fill="#92400e">1・2・3・4</text>

  <!-- 回転中心の台座（SVG (240, 290) = Scratch (0, -110)） -->
  <rect x="148" y="294" width="184" height="24" rx="5" fill="#78350f"/>
  <circle cx="240" cy="290" r="10" fill="#fde047" stroke="#78350f" stroke-width="2"/>

  <!-- 下部ガイド -->
  <text x="240" y="346" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" fill="#6b21a8">1ぱくめ だけ「たかいおん」、2〜4ぱくめ は「ひくいおん」！</text>
</svg>"""


def _make_needle_svg() -> str:
    """Needle drawn pointing RIGHT (+X) from pivot (16, 16) so Scratch direction 0 = straight UP, -30 = left, +30 = right."""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="192" height="32" viewBox="0 0 192 32">
  <!-- 針のシャフト -->
  <rect x="14" y="13" width="166" height="6" rx="3" fill="#334155" stroke="#0f172a" stroke-width="1.5"/>
  <!-- テンポおもり（台形） -->
  <polygon points="104,5 128,8 128,24 104,27" fill="#f59e0b" stroke="#92400e" stroke-width="2"/>
  <!-- 先端の赤丸 -->
  <circle cx="180" cy="16" r="5" fill="#ef4444" stroke="#991b1b" stroke-width="1.5"/>
  <!-- 回転中心ピボット (16, 16) -->
  <circle cx="16" cy="16" r="8" fill="#e2e8f0" stroke="#334155" stroke-width="2"/>
  <circle cx="16" cy="16" r="3" fill="#334155"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("メトロノームのはいけい", _make_metronome_backdrop_svg(), 240, 180)
    )
    var_count = proj.stage.add_variable("カウント", 0, show_monitor=True, monitor_x=8, monitor_y=8)

    needle = proj.add_sprite(
        name="はり",
        x=PIVOT_X,
        y=PIVOT_Y,
        size=100,
        direction=0,
        rotation_style="all around",
    )
    # Pivot is at (16, 16) so direction=0 points straight up, -30 tilts left, +30 tilts right
    needle.add_costume(make_svg_costume("はり", _make_needle_svg(), 16, 16))
    needle.add_sound(synth_tick_high("たかいおん"))
    needle.add_sound(synth_tick_low("ひくいおん"))
    return proj, needle, needle.builder, var_count


def build_template() -> Project:
    """Build template with pivoted needle, high/low sounds, and カウント variable."""
    proj, needle, b, var_count = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(PIVOT_X, PIVOT_Y),
        b.point_in_direction(0),
        b.set_variable(var_count, 0),
    )

    needle.add_comment(
        text=(
            "【ヒント：4びょうし メトロノーム】\n"
            "「ずっと」の なかで くりかえそう：\n"
            "1. カウント を 1ずつ かえる\n"
            "2. もし (カウント ＝ 1) なら「たかいおん」を ならす\n"
            "   でなければ「ひくいおん」を ならす\n"
            "3. はり を -30ど（ひだり）と 30ど（みぎ）に\n"
            "   こうご に むける（カウント を 2 で わった あまり で はんてい！）\n"
            "4. もし (カウント ＝ 4) なら カウント を 0 に する\n"
            "5. 0.5 びょう まつ"
        ),
        x=420,
        y=48,
        width=340,
        height=240,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working 4/4 metronome alternating left/right with accented beat 1."""
    proj, needle, b, var_count = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(PIVOT_X, PIVOT_Y),
        b.point_in_direction(0),
        b.set_variable(var_count, 0),
        b.forever(
            [
                b.change_variable(var_count, 1),
                b.if_else(
                    b.eq(var_count, 1),
                    then_body=[b.play_sound("たかいおん")],
                    else_body=[b.play_sound("ひくいおん")],
                ),
                b.if_else(
                    b.eq(b.mod(var_count, 2), 1),
                    then_body=[b.point_in_direction(-30)],
                    else_body=[b.point_in_direction(30)],
                ),
                b.if_then(
                    b.eq(var_count, 4),
                    [b.set_variable(var_count, 0)],
                ),
                b.wait(0.5),
            ]
        ),
    )

    needle.add_comment(
        text=(
            "【おてほん】\n"
            "カウント 1〜4 を くりかえしながら、\n"
            "1ぱくめ だけ たかいおん を ならし、\n"
            "はり を -30ど と 30ど に ふります。"
        ),
        x=420,
        y=48,
        width=300,
        height=135,
        block=hat,
    )
    return proj
