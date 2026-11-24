"""Task 26: 風船を膨らます (26_balloon)

入力や時間で膨張し、上限サイズで破裂させる課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_balloon_pop, synth_inflate_pump

TASK_ID = "26_balloon_pump"
TASK_TITLE = "ふうせん を ふくらます"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

INIT_SIZE = 60
POP_LIMIT_SIZE = 200


def _make_balloon_backdrop_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <rect x="0" y="0" width="480" height="360" fill="#dbeafe"/>
  <!-- 白い雲 -->
  <g fill="#ffffff" opacity="0.9">
    <ellipse cx="78" cy="116" rx="38" ry="18"/>
    <ellipse cx="104" cy="108" rx="24" ry="14"/>
    <ellipse cx="394" cy="132" rx="40" ry="18"/>
    <ellipse cx="420" cy="124" rx="24" ry="14"/>
  </g>

  <!-- タイトル帯 -->
  <rect x="116" y="12" width="268" height="34" rx="17" fill="#ffffff" stroke="#ec4899" stroke-width="2.5"/>
  <text x="250" y="35" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="16" font-weight="bold" fill="#be185d">ふうせん を ふくらまそう！</text>

  <!-- 下部ガイド -->
  <rect x="44" y="308" width="392" height="36" rx="18" fill="#ffffff" stroke="#f472b6" stroke-width="2"/>
  <text x="240" y="331" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="14" font-weight="bold" fill="#9d174d">スペースキー で くうき を いれよう！（200 で はれつ！）</text>
</svg>"""


def _make_balloon_normal_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="96" height="126" viewBox="0 0 96 126">
  <!-- ひも -->
  <path d="M 48 92 Q 40 106 50 122" fill="none" stroke="#64748b" stroke-width="2.5" stroke-linecap="round"/>
  <!-- 結び目 -->
  <polygon points="48,84 42,93 54,93" fill="#e11d48"/>
  <!-- 風船本体 -->
  <ellipse cx="48" cy="46" rx="34" ry="40" fill="#f43f5e" stroke="#be123c" stroke-width="3"/>
  <!-- 光沢ハイライト -->
  <ellipse cx="34" cy="32" rx="8" ry="14" transform="rotate(-20 34 32)" fill="#ffffff" opacity="0.45"/>
</svg>"""


def _make_balloon_popped_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
  <!-- はじけた衝撃線 -->
  <polygon points="60,6 72,38 106,20 86,50 116,64 84,74 102,106 70,88 60,116 48,88 18,106 36,74 4,64 34,50 14,20 48,38" fill="#fef08a" stroke="#f97316" stroke-width="2.5" stroke-linejoin="round"/>
  <!-- 飛び散る破片 -->
  <polygon points="24,32 36,28 32,42" fill="#f43f5e"/>
  <polygon points="88,26 98,36 84,38" fill="#f43f5e"/>
  <polygon points="28,86 40,94 26,98" fill="#f43f5e"/>
  <polygon points="84,84 96,90 88,100" fill="#f43f5e"/>
  <text x="60" y="67" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="18" font-weight="bold" fill="#be123c">パーン！</text>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("あおぞらのはいけい", _make_balloon_backdrop_svg(), 240, 180)
    )
    var_size = proj.stage.add_variable(
        "おおきさ", INIT_SIZE, show_monitor=True, monitor_x=8, monitor_y=8
    )

    balloon = proj.add_sprite(
        name="ふうせん",
        x=0,
        y=-10,
        size=INIT_SIZE,
        direction=90,
        rotation_style="don't rotate",
    )
    balloon.add_costume(make_svg_costume("つうじょう", _make_balloon_normal_svg(), 48, 56))
    balloon.add_costume(make_svg_costume("はれつ", _make_balloon_popped_svg(), 60, 60))
    balloon.add_sound(synth_inflate_pump("くうきおん"))
    balloon.add_sound(synth_balloon_pop("はれつおん"))
    return proj, balloon, balloon.builder, var_size


def build_template() -> Project:
    """Build template with normal/popped balloon, size reset, air & pop sounds, and hint."""
    proj, balloon, b, var_size = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, -10),
        b.switch_costume_to("つうじょう"),
        b.set_size_to(INIT_SIZE),
        b.set_variable(var_size, INIT_SIZE),
    )

    balloon.add_comment(
        text=(
            "【ヒント：ふうせん を ふくらませて はれつ！】\n"
            "「おおきさ ＞ 199 まで くりかえす」の なかで：\n"
            "  ・スペースキーが おされた まで まつ\n"
            "  ・「くうきおん」を ならす\n"
            "  ・おおきさ（サイズ）を 15 ずつ かえる\n"
            "  ・へんすう「おおきさ」を サイズ に する\n"
            "  ・スペースキーが はなされる まで まつ\n\n"
            "200 いじょう に なったら：\n"
            "  ・コスチュームを「はれつ」に する\n"
            "  ・「はれつおん」を ならして「パーン！」と いう！"
        ),
        x=420,
        y=48,
        width=345,
        height=245,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working balloon pump game that pops at size >= 200."""
    proj, balloon, b, var_size = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, -10),
        b.switch_costume_to("つうじょう"),
        b.set_size_to(INIT_SIZE),
        b.set_variable(var_size, INIT_SIZE),
        b.repeat_until(
            b.gt(b.looks_size(), POP_LIMIT_SIZE - 1),
            [
                b.wait_until(b.key_pressed("space")),
                b.play_sound("くうきおん"),
                b.change_size_by(15),
                b.set_variable(var_size, b.looks_size()),
                b.wait_until(b.logical_not(b.key_pressed("space"))),
            ],
        ),
        b.switch_costume_to("はれつ"),
        b.play_sound("はれつおん"),
        b.say_for_secs("パーン！ はれつ した！", 2),
    )

    balloon.add_comment(
        text=(
            "【おてほん】\n"
            "スペースキー で サイズを 15 ずつ ふやし、\n"
            "200 に たっしたら はれつ コスチューム と おと に きりかえます。"
        ),
        x=420,
        y=48,
        width=320,
        height=120,
        block=hat,
    )
    return proj
