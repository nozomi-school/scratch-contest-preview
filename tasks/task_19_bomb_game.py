"""Task 19: 爆弾ゲーム (19_bomb_game)

ランダム秒後に爆発する導火線・点滅演出を作る課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_explosion, synth_tick_tock

TASK_ID = "19_bomb_game"
TASK_TITLE = "ばくだん ゲーム"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"


def _make_bomb_backdrop_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <rect x="0" y="0" width="480" height="360" fill="#1e293b"/>
  <!-- スポットライト円 -->
  <circle cx="240" cy="190" r="136" fill="#334155"/>
  <circle cx="240" cy="190" r="108" fill="#475569" opacity="0.55"/>

  <!-- タイトル帯 -->
  <rect x="104" y="14" width="272" height="36" rx="18" fill="#fef08a" stroke="#f59e0b" stroke-width="2.5"/>
  <text x="240" y="38" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="17" font-weight="bold" fill="#92400e">ドキドキ ばくだん ゲーム！</text>

  <!-- 下部ガイド -->
  <text x="240" y="340" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="14" font-weight="bold" fill="#f8fafc">いつ ばくはつ するかな…？</text>
</svg>"""


def _make_bomb_svg(flashing: bool) -> str:
    body_fill = "#dc2626" if flashing else "#0f172a"
    body_stroke = "#fef08a" if flashing else "#475569"
    spark_r = 14 if flashing else 8
    spark_color = "#fef08a" if flashing else "#fb923c"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="140" height="150" viewBox="0 0 140 150">
  <!-- 導火線 -->
  <path d="M 70 42 Q 78 16 104 20" fill="none" stroke="#d6d3d1" stroke-width="5" stroke-linecap="round"/>
  <!-- 火花 -->
  <circle cx="106" cy="20" r="{spark_r}" fill="{spark_color}" opacity="0.9"/>
  <circle cx="106" cy="20" r="{spark_r // 2}" fill="#ffffff"/>
  <!-- 口金 -->
  <rect x="56" y="38" width="28" height="14" rx="4" fill="#64748b" stroke="#334155" stroke-width="2"/>
  <!-- 爆弾本体 -->
  <circle cx="70" cy="92" r="46" fill="{body_fill}" stroke="{body_stroke}" stroke-width="4"/>
  <!-- 光沢 -->
  <ellipse cx="52" cy="76" rx="10" ry="16" transform="rotate(-25 52 76)" fill="#ffffff" opacity="0.25"/>
</svg>"""


def _make_explosion_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180" viewBox="0 0 180 180">
  <!-- 外側の爆発ギザギザ -->
  <polygon points="90,6 110,48 156,28 134,72 176,92 132,112 156,156 110,136 90,176 70,136 24,156 48,112 4,92 46,72 24,28 70,48" fill="#ef4444" stroke="#991b1b" stroke-width="3" stroke-linejoin="round"/>
  <polygon points="90,28 104,60 138,48 122,80 154,92 122,106 136,136 104,122 90,154 76,122 44,136 58,106 26,92 58,80 42,48 76,60" fill="#f97316"/>
  <circle cx="90" cy="92" r="36" fill="#fef08a"/>
  <text x="90" y="99" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="20" font-weight="bold" fill="#b91c1c">ドカーン！</text>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("ばくだんステージ", _make_bomb_backdrop_svg(), 240, 180)
    )
    # 残り回数（ひみつにするためモニターは非表示）
    var_remain = proj.stage.add_variable("のこり", 0, show_monitor=False)

    bomb = proj.add_sprite(
        name="ばくだん",
        x=0,
        y=-10,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    bomb.add_costume(make_svg_costume("つうじょう", _make_bomb_svg(False), 70, 75))
    bomb.add_costume(make_svg_costume("てんめつ", _make_bomb_svg(True), 70, 75))
    bomb.add_costume(make_svg_costume("ばくはつ", _make_explosion_svg(), 90, 90))
    bomb.add_sound(synth_tick_tock("チクタクおん"))
    bomb.add_sound(synth_explosion("ばくはつおん"))
    return proj, bomb, bomb.builder, var_remain


def build_template() -> Project:
    """Build template with normal/flash/explode costumes, tick & boom sounds, and init block."""
    proj, bomb, b, var_remain = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, -10),
        b.switch_costume_to("つうじょう"),
        b.set_variable(var_remain, 0),
    )

    bomb.add_comment(
        text=(
            "【ヒント：ランダム ばくだん】\n"
            "1.「のこり を 4 から 9 までの らんすう に する」\n"
            "2.「のこり ＜ 1 まで くりかえす」の なかで：\n"
            "   ・チクタクおん を ならす\n"
            "   ・コスチューム「てんめつ」→ 0.25びょう まつ\n"
            "   ・コスチューム「つうじょう」→ 0.25びょう まつ\n"
            "   ・のこり を -1 ずつ かえる\n"
            "3. ループを でたら：\n"
            "   ・コスチューム「ばくはつ」→「ばくはつおん」→「ドカーン！！」"
        ),
        x=420,
        y=48,
        width=355,
        height=245,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working random-delay bomb with ticking flash and explosion."""
    proj, bomb, b, var_remain = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, -10),
        b.switch_costume_to("つうじょう"),
        b.set_variable(var_remain, b.pick_random(4, 9)),
        b.repeat_until(
            b.lt(var_remain, 1),
            [
                b.play_sound("チクタクおん"),
                b.switch_costume_to("てんめつ"),
                b.wait(0.25),
                b.switch_costume_to("つうじょう"),
                b.wait(0.25),
                b.change_variable(var_remain, -1),
            ],
        ),
        b.switch_costume_to("ばくはつ"),
        b.play_sound("ばくはつおん"),
        b.say("ドカーン！！"),
    )

    bomb.add_comment(
        text=(
            "【おてほん】\n"
            "らんすう で きめた かいすう だけ\n"
            "チクタク てんめつ したあとに ばくはつ します。"
        ),
        x=420,
        y=48,
        width=305,
        height=115,
        block=hat,
    )
    return proj
