"""Task 04: レンガ積み上げ (04_bricks)

偶数段だけ横半分ずらしてレンガの壁を積む課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume

TASK_ID = "04_brick_wall"
TASK_TITLE = "レンガ つみあげ"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

BRICK_W = 60
BRICK_H = 30
START_X_ODD = -150
START_X_EVEN = -120  # Shifted right by half a brick (30px)
START_Y = -115       # Bottom edge touches ground at y = -130


def _make_sky_ground_backdrop_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- 青空 -->
  <rect x="0" y="0" width="480" height="310" fill="#e0f2fe"/>
  <!-- 白い雲 -->
  <g fill="#ffffff" opacity="0.88">
    <ellipse cx="88" cy="76" rx="34" ry="15"/>
    <ellipse cx="110" cy="72" rx="22" ry="13"/>
    <ellipse cx="385" cy="84" rx="36" ry="15"/>
    <ellipse cx="408" cy="79" rx="20" ry="12"/>
  </g>
  <!-- タイトル帯 -->
  <rect x="108" y="12" width="264" height="32" rx="16" fill="#ffffff" stroke="#c2410c" stroke-width="2"/>
  <text x="240" y="34" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="16" font-weight="bold" fill="#9a3412">レンガ の かべ を つみあげよう！</text>

  <!-- 地面（y = -130 -> SVG y = 310） -->
  <rect x="0" y="310" width="480" height="50" fill="#86efac"/>
  <line x1="0" y1="310" x2="480" y2="310" stroke="#16a34a" stroke-width="3"/>
  <text x="240" y="342" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" font-weight="bold" fill="#14532d">ぐうすう だん は よこ はんぶん（30）ずらそう！</text>
</svg>"""


def _make_brick_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="60" height="30" viewBox="0 0 60 30">
  <rect x="1" y="1" width="58" height="28" rx="3" fill="#c2410c" stroke="#fed7aa" stroke-width="2"/>
  <line x1="5" y1="5" x2="55" y2="5" stroke="#fb923c" stroke-width="2" stroke-linecap="round" opacity="0.7"/>
  <line x1="5" y1="25" x2="55" y2="25" stroke="#7c2d12" stroke-width="2" stroke-linecap="round" opacity="0.5"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object]:
    proj = Project()
    proj.add_extension("pen")

    proj.stage.add_costume(
        make_svg_costume("そらとじめん", _make_sky_ground_backdrop_svg(), 240, 180)
    )
    var_row = proj.stage.add_variable("だん", 1, show_monitor=False)

    brick = proj.add_sprite(
        name="レンガ",
        x=START_X_ODD,
        y=START_Y,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    brick.add_costume(make_svg_costume("レンガ", _make_brick_svg(), 30, 15))
    return proj, brick, brick.builder, var_row


def build_template() -> Project:
    """Build template with brick sprite, pen init, start pos, and width memo comment."""
    proj, brick, b, var_row = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.pen_clear(),
        b.show(),
        b.go_to_xy(START_X_ODD, START_Y),
        b.set_variable(var_row, 1),
    )

    brick.add_comment(
        text=(
            "【メモ：レンガ の おおきさ】\n"
            "・よこはば ＝ 60（はんぶん ＝ 30）\n"
            "・たかさ   ＝ 30\n"
            "・1だんめ スタート：x = -150, y = -115\n\n"
            "【ヒント】\n"
            "「6かい くりかえす（6だん）」の なかで：\n"
            "1. もし (だん を 2 で わった あまり ＝ 0) なら\n"
            "   xざひょう を -120 に する（よこに 30 ずらす！）\n"
            "   でなければ xざひょう を -150 に する\n"
            "2. 6かい くりかえす：スタンプ → xを 60 かえる\n"
            "3. yを 30 かえる → だん を 1 ずつ かえる"
        ),
        x=420,
        y=48,
        width=335,
        height=265,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working 6-row staggered brick wall."""
    proj, brick, b, var_row = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.pen_clear(),
        b.show(),
        b.go_to_xy(START_X_ODD, START_Y),
        b.set_variable(var_row, 1),
        b.repeat(
            6,
            [
                b.if_else(
                    b.eq(b.mod(var_row, 2), 0),
                    then_body=[b.set_x(START_X_EVEN)],
                    else_body=[b.set_x(START_X_ODD)],
                ),
                b.repeat(
                    6,
                    [
                        b.pen_stamp(),
                        b.change_x_by(BRICK_W),
                    ],
                ),
                b.change_y_by(BRICK_H),
                b.change_variable(var_row, 1),
            ],
        ),
        b.hide(),
    )

    brick.add_comment(
        text=(
            "【おてほん】\n"
            "ぐうすう だん の ときだけ スタート xざひょう を\n"
            "レンガ はんぶん（+30）ずらして 6だん つみあげます。"
        ),
        x=420,
        y=48,
        width=310,
        height=120,
        block=hat,
    )
    return proj
