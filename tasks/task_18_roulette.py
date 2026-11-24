"""Task 18: タイミング・ルーレット止め (18_roulette)

高速で切り替わる絵柄を止めて当たり／ハズレ判定をする課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_buzzer_fail, synth_chime_success

TASK_ID = "18_roulette_stop"
TASK_TITLE = "タイミング・ルーレットどめ"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"


def _make_roulette_backdrop_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <rect x="0" y="0" width="480" height="360" fill="#fef2f2"/>
  <!-- タイトル帯 -->
  <rect x="108" y="14" width="264" height="36" rx="18" fill="#ffffff" stroke="#e11d48" stroke-width="2.5"/>
  <text x="240" y="38" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="17" font-weight="bold" fill="#be123c">タイミング ルーレット！</text>

  <!-- スロットマシン外枠 -->
  <rect x="132" y="72" width="216" height="216" rx="26" fill="#f59e0b" stroke="#b45309" stroke-width="4"/>
  <!-- 光る電球ドット -->
  <g fill="#fef08a">
    <circle cx="154" cy="86" r="5"/><circle cx="240" cy="82" r="5"/><circle cx="326" cy="86" r="5"/>
    <circle cx="154" cy="274" r="5"/><circle cx="240" cy="278" r="5"/><circle cx="326" cy="274" r="5"/>
  </g>
  <!-- 中央表示窓 -->
  <rect x="156" y="96" width="168" height="168" rx="18" fill="#ffffff" stroke="#92400e" stroke-width="3"/>

  <!-- 操作説明 -->
  <rect x="52" y="308" width="376" height="36" rx="18" fill="#ffffff" stroke="#fb7185" stroke-width="2"/>
  <text x="240" y="331" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="14" font-weight="bold" fill="#9f1239">スペースキー で「ほし（1ばん）」を とめよう！</text>
</svg>"""


def _make_symbol_star_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140" viewBox="0 0 140 140">
  <rect x="4" y="4" width="132" height="132" rx="16" fill="#fef9c3" stroke="#eab308" stroke-width="3"/>
  <polygon points="70,18 84,50 119,53 92,76 100,110 70,92 40,110 48,76 21,53 56,50" fill="#facc15" stroke="#ca8a04" stroke-width="3" stroke-linejoin="round"/>
  <text x="70" y="128" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" font-weight="bold" fill="#b45309">1ばん：あたり！</text>
</svg>"""


def _make_symbol_apple_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140" viewBox="0 0 140 140">
  <rect x="4" y="4" width="132" height="132" rx="16" fill="#fee2e2" stroke="#f87171" stroke-width="3"/>
  <path d="M 70 36 L 74 20" stroke="#78350f" stroke-width="4" stroke-linecap="round"/>
  <ellipse cx="83" cy="28" rx="10" ry="5" transform="rotate(-25 83 28)" fill="#22c55e"/>
  <circle cx="57" cy="70" r="28" fill="#ef4444"/>
  <circle cx="83" cy="70" r="28" fill="#ef4444"/>
  <ellipse cx="52" cy="58" rx="7" ry="11" fill="#ffffff" opacity="0.35"/>
  <text x="70" y="126" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" font-weight="bold" fill="#991b1b">2ばん：りんご</text>
</svg>"""


def _make_symbol_banana_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140" viewBox="0 0 140 140">
  <rect x="4" y="4" width="132" height="132" rx="16" fill="#fefce8" stroke="#facc15" stroke-width="3"/>
  <path d="M 38 92 Q 72 108 104 42 Q 94 34 86 42 Q 66 78 36 80 Z" fill="#fde047" stroke="#ca8a04" stroke-width="3" stroke-linejoin="round"/>
  <text x="70" y="126" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" font-weight="bold" fill="#854d0e">3ばん：バナナ</text>
</svg>"""


def _make_symbol_grape_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140" viewBox="0 0 140 140">
  <rect x="4" y="4" width="132" height="132" rx="16" fill="#f3e8ff" stroke="#c084fc" stroke-width="3"/>
  <path d="M 70 32 L 70 18" stroke="#15803d" stroke-width="4" stroke-linecap="round"/>
  <g fill="#9333ea" stroke="#581c87" stroke-width="2">
    <circle cx="52" cy="50" r="13"/><circle cx="70" cy="50" r="13"/><circle cx="88" cy="50" r="13"/>
    <circle cx="61" cy="70" r="13"/><circle cx="79" cy="70" r="13"/>
    <circle cx="70" cy="90" r="13"/>
  </g>
  <text x="70" y="126" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" font-weight="bold" fill="#6b21a8">4ばん：ぶどう</text>
</svg>"""


def _create_base_project() -> tuple[Project, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("ルーレットはいけい", _make_roulette_backdrop_svg(), 240, 180)
    )

    wheel = proj.add_sprite(
        name="ルーレット",
        x=0,
        y=0,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    wheel.add_costume(make_svg_costume("1_ほし_あたり", _make_symbol_star_svg(), 70, 70))
    wheel.add_costume(make_svg_costume("2_りんご", _make_symbol_apple_svg(), 70, 70))
    wheel.add_costume(make_svg_costume("3_バナナ", _make_symbol_banana_svg(), 70, 70))
    wheel.add_costume(make_svg_costume("4_ぶどう", _make_symbol_grape_svg(), 70, 70))
    wheel.add_sound(synth_chime_success("あたりおん"))
    wheel.add_sound(synth_buzzer_fail("はずれおん"))
    return proj, wheel, wheel.builder


def build_template() -> Project:
    """Build template with 4 roulette costumes, win/lose sounds, and init block."""
    proj, wheel, b = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, 0),
        b.switch_costume_to("1_ほし_あたり"),
    )

    wheel.add_comment(
        text=(
            "【ヒント：コスチューム ばんごう で はんてい！】\n"
            "1.「スペースキーが おされた まで くりかえす」の なかで：\n"
            "   ・つぎのコスチューム に する\n"
            "   ・0.08 びょう まつ\n"
            "2. とまったあと、「もし〜なら、でなければ」で：\n"
            "   じょうけん：「コスチューム の ばんごう ＝ 1」\n"
            "   ・あたり →「あたりおん」＋「だいあたり！」\n"
            "   ・はずれ →「はずれおん」＋「はずれ…」"
        ),
        x=420,
        y=48,
        width=340,
        height=215,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working timing roulette that checks costume_number() == 1 on Space."""
    proj, wheel, b = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, 0),
        b.wait_until(b.logical_not(b.key_pressed("space"))),
        b.repeat_until(
            b.key_pressed("space"),
            [
                b.next_costume(),
                b.wait(0.08),
            ],
        ),
        b.if_else(
            b.eq(b.costume_number(), 1),
            then_body=[
                b.play_sound("あたりおん"),
                b.say_for_secs("だいあたり！ ほし だよ！", 2),
            ],
            else_body=[
                b.play_sound("はずれおん"),
                b.say_for_secs("はずれ… もういちど！", 2),
            ],
        ),
    )

    wheel.add_comment(
        text=(
            "【おてほん】\n"
            "スペースキー で とまった ときの\n"
            "コスチュームの ばんごう が 1（ほし）なら あたりです。"
        ),
        x=420,
        y=48,
        width=305,
        height=115,
        block=hat,
    )
    return proj
