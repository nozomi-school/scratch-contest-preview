"""Task 16: 連打スピードメーター (16_mash_speed)

5秒間の連打回数を計測（押しっぱなし禁止）する課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_chime_bath, synth_pop

TASK_ID = "16_mash_meter"
TASK_TITLE = "れんだ スピードメーター"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"


def _make_arena_backdrop_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <rect x="0" y="0" width="480" height="360" fill="#fff7ed"/>
  <!-- 集中線ふう放射ライン -->
  <g stroke="#fed7aa" stroke-width="3" opacity="0.6">
    <line x1="240" y1="180" x2="0" y2="0"/>
    <line x1="240" y1="180" x2="480" y2="0"/>
    <line x1="240" y1="180" x2="0" y2="360"/>
    <line x1="240" y1="180" x2="480" y2="360"/>
    <line x1="240" y1="180" x2="0" y2="180"/>
    <line x1="240" y1="180" x2="480" y2="180"/>
  </g>
  <circle cx="240" cy="180" r="106" fill="#ffffff" stroke="#fb923c" stroke-width="4"/>

  <!-- タイトル帯 -->
  <rect x="122" y="12" width="268" height="34" rx="17" fill="#ffffff" stroke="#ea580c" stroke-width="2.5"/>
  <text x="256" y="35" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="16" font-weight="bold" fill="#c2410c">5びょうかん れんだ チャレンジ！</text>

  <!-- 下部操作説明 -->
  <rect x="52" y="308" width="376" height="36" rx="18" fill="#ffffff" stroke="#f97316" stroke-width="2"/>
  <text x="240" y="331" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="14" font-weight="bold" fill="#9a3412">スペースキー を れんだ！（おしっぱなし は ダメ！）</text>
</svg>"""


def _make_challenger_svg(jumping: bool) -> str:
    body_y = 26 if jumping else 38
    arm_y = 24 if jumping else 52
    spark = (
        '<text x="50" y="18" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="bold" fill="#ea580c">★</text>'
        if jumping
        else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  {spark}
  <!-- 丸い元気キャラ -->
  <circle cx="50" cy="{body_y + 24}" r="28" fill="#fb923c" stroke="#9a3412" stroke-width="3"/>
  <!-- 腕 -->
  <line x1="22" y1="{body_y + 24}" x2="10" y2="{arm_y}" stroke="#9a3412" stroke-width="5" stroke-linecap="round"/>
  <line x1="78" y1="{body_y + 24}" x2="90" y2="{arm_y}" stroke="#9a3412" stroke-width="5" stroke-linecap="round"/>
  <!-- 目・口 -->
  <circle cx="40" cy="{body_y + 20}" r="4" fill="#1e293b"/>
  <circle cx="60" cy="{body_y + 20}" r="4" fill="#1e293b"/>
  <path d="M 40 {body_y + 32} Q 50 {body_y + 42} 60 {body_y + 32}" fill="none" stroke="#1e293b" stroke-width="3" stroke-linecap="round"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("れんだステージ", _make_arena_backdrop_svg(), 240, 180)
    )
    var_count = proj.stage.add_variable(
        "かいすう", 0, show_monitor=True, monitor_x=8, monitor_y=8
    )
    var_remain = proj.stage.add_variable(
        "のこりじかん", 5, show_monitor=True, monitor_x=8, monitor_y=40
    )

    hero = proj.add_sprite(
        name="チャレンジャー",
        x=0,
        y=-10,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    hero.add_costume(make_svg_costume("たいき", _make_challenger_svg(False), 50, 50))
    hero.add_costume(make_svg_costume("ジャンプ", _make_challenger_svg(True), 50, 50))
    hero.add_sound(synth_pop("ポンおん"))
    hero.add_sound(synth_chime_bath("しゅうりょうおん"))
    return proj, hero, hero.builder, var_count, var_remain


def _add_five_sec_timer_script(b: object, var_count: object, var_remain: object) -> object:
    """Pre-built 5-second countdown & stop script shared by template and sample."""
    return b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, -10),
        b.switch_costume_to("たいき"),
        b.set_variable(var_count, 0),
        b.set_variable(var_remain, 5),
        b.repeat(
            5,
            [
                b.wait(1),
                b.change_variable(var_remain, -1),
            ],
        ),
        b.play_sound("しゅうりょうおん"),
        b.say(b.join("しゅうりょう！ きろくは ", b.join(var_count, "かい！"))),
        b.stop("all"),
    )


def build_template() -> Project:
    """Build template with pre-implemented 5-second finish script and かいすう variable."""
    proj, hero, b, var_count, var_remain = _create_base_project()

    _add_five_sec_timer_script(b, var_count, var_remain)
    mash_hat = b.script(b.when_flag_clicked())

    hero.add_comment(
        text=(
            "【ヒント：おしっぱなし ぼうし の れんだ けいそく】\n"
            "ひだり の「5びょう しゅうりょう」は もう できているよ！\n"
            "こっち の みどりのはた に「ずっと」を つなげて：\n"
            "1.「スペースキーが おされた まで まつ」\n"
            "2.「かいすう を 1ずつ かえる」（＋ポンおん・ジャンプ）\n"
            "3.「スペースキーが おされた では ない まで まつ」\n"
            "   ★これで キーを はなすまで つぎが ふえないよ！"
        ),
        x=488,
        y=220,
        width=355,
        height=215,
        block=mash_hat,
    )
    return proj


def build_sample() -> Project:
    """Build working 5-second mash speed counter with anti-hold wait_until(not key)."""
    proj, hero, b, var_count, var_remain = _create_base_project()

    _add_five_sec_timer_script(b, var_count, var_remain)
    mash_hat = b.script(
        b.when_flag_clicked(),
        b.forever(
            [
                b.wait_until(b.key_pressed("space")),
                b.change_variable(var_count, 1),
                b.play_sound("ポンおん"),
                b.switch_costume_to("ジャンプ"),
                b.wait_until(b.logical_not(b.key_pressed("space"))),
                b.switch_costume_to("たいき"),
            ]
        ),
    )

    hero.add_comment(
        text=(
            "【おてほん】\n"
            "「キーが おされた では ない まで まつ」を いれることで\n"
            "おしっぱなし の ズル を ふせぎます。"
        ),
        x=488,
        y=340,
        width=320,
        height=115,
        block=mash_hat,
    )
    return proj
