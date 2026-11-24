"""Task 24: キャラクターでドミノ (24_domino)

複数キャラが順番にアクションをリレーしていく課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_note

TASK_ID = "24_domino_relay"
TASK_TITLE = "キャラクター で ドミノ"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

DOMINO_Y = -90  # Base pivot sits cleanly on stage floor (y = -90 -> SVG y = 270)
DOMINO_SPECS = [
    ("キャラ1", -165, "#ef4444", "#991b1b", "ドおん", 523.25),
    ("キャラ2", -55, "#3b82f6", "#1d4ed8", "ミおん", 659.25),
    ("キャラ3", 55, "#22c55e", "#15803d", "ソおん", 783.99),
    ("キャラ4", 165, "#eab308", "#a16207", "たかいドおん", 1046.50),
]


def _make_domino_backdrop_svg() -> str:
    spots = "\n".join(
        f'  <circle cx="{240 + x}" cy="296" r="14" fill="#ffffff" stroke="#94a3b8" stroke-width="2"/>\n'
        f'  <text x="{240 + x}" y="301" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" font-weight="bold" fill="#334155">{idx + 1}</text>'
        for idx, (_, x, _, _, _, _) in enumerate(DOMINO_SPECS)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <rect x="0" y="0" width="480" height="270" fill="#f0f9ff"/>
  <!-- タイトル帯 -->
  <rect x="96" y="14" width="288" height="36" rx="18" fill="#ffffff" stroke="#0284c7" stroke-width="2.5"/>
  <text x="240" y="38" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="17" font-weight="bold" fill="#0369a1">キャラクター で ドミノ リレー！</text>

  <!-- ステージ床（y = -90 -> SVG y = 270） -->
  <rect x="0" y="270" width="480" height="90" fill="#e2e8f0"/>
  <line x1="0" y1="270" x2="480" y2="270" stroke="#64748b" stroke-width="3"/>

  <!-- 順番マーカー -->
{spots}

  <text x="240" y="344" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" font-weight="bold" fill="#475569">メッセージ「1ばんめ → 2ばんめ → 3ばんめ」で つなごう！</text>
</svg>"""


def _make_domino_char_svg(label: str, fill: str, stroke: str) -> str:
    """Upright domino character with base pivot at (28, 92) so turning right topples it cleanly."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="56" height="96" viewBox="0 0 56 96">
  <rect x="6" y="4" width="44" height="88" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="3"/>
  <!-- 顔 -->
  <circle cx="20" cy="30" r="3.5" fill="#ffffff"/>
  <circle cx="36" cy="30" r="3.5" fill="#ffffff"/>
  <circle cx="21" cy="30" r="1.6" fill="#0f172a"/>
  <circle cx="37" cy="30" r="1.6" fill="#0f172a"/>
  <path d="M 21 42 Q 28 48 35 42" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
  <!-- 番号バッジ -->
  <circle cx="28" cy="68" r="12" fill="#ffffff" opacity="0.9"/>
  <text x="28" y="73" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="14" font-weight="bold" fill="{stroke}">{label}</text>
</svg>"""


def _create_base_project() -> tuple[Project, list[object], list[object]]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("ドミノステージ", _make_domino_backdrop_svg(), 240, 180)
    )
    broadcasts = [
        proj.add_broadcast("1ばんめ"),
        proj.add_broadcast("2ばんめ"),
        proj.add_broadcast("3ばんめ"),
    ]

    chars = []
    for idx, (name, x, fill, stroke, sound_name, freq) in enumerate(DOMINO_SPECS):
        sp = proj.add_sprite(
            name=name,
            x=x,
            y=DOMINO_Y,
            size=100,
            direction=90,
            rotation_style="all around",
        )
        # Pivot at bottom center (28, 92) for realistic toppling rotation
        sp.add_costume(
            make_svg_costume(name, _make_domino_char_svg(str(idx + 1), fill, stroke), 28, 92)
        )
        sp.add_sound(synth_note(sound_name, freq, duration=0.3))
        chars.append(sp)

    return proj, chars, broadcasts


def build_template() -> Project:
    """Build template with 4 positioned domino characters, reset scripts, and broadcasts 1~3."""
    proj, chars, _broadcasts = _create_base_project()

    for idx, (sp, (name, x, _, _, sound_name, _)) in enumerate(zip(chars, DOMINO_SPECS)):
        b = sp.builder
        hat = b.script(
            b.when_flag_clicked(),
            b.go_to_xy(x, DOMINO_Y),
            b.point_in_direction(90),
        )
        if idx == 0:
            hint = (
                "【ヒント：キャラ1（スタート）】\n"
                "しょきか の あとに：\n"
                "・0.5びょう まつ →「ドおん」を ならす\n"
                "・9かい くりかえす（みぎに 10ど まわす）で たおれる\n"
                "・「1ばんめ」を おくる！"
            )
        elif idx < 3:
            recv_name = f"{idx}ばんめ"
            send_name = f"{idx + 1}ばんめ"
            hint = (
                f"【ヒント：{name}】\n"
                f"「{recv_name}」を うけとったとき：\n"
                f"・「{sound_name}」を ならす\n"
                f"・9かい くりかえす（みぎに 10ど まわす）\n"
                f"・「{send_name}」を おくる！"
            )
        else:
            hint = (
                "【ヒント：キャラ4（ゴール）】\n"
                "「3ばんめ」を うけとったとき：\n"
                "・「たかいドおん」を ならす\n"
                "・9かい くりかえす（みぎに 10ど まわす）\n"
                "・「ゴール！！」と 2びょう いう！"
            )
        sp.add_comment(text=hint, x=420, y=48, width=320, height=175, block=hat)

    return proj


def build_sample() -> Project:
    """Build working 4-character message-relay domino chain with ascending chord."""
    proj, chars, broadcasts = _create_base_project()

    # キャラ1: start domino -> broadcast 1ばんめ
    c1 = chars[0]
    b1 = c1.builder
    b1.script(
        b1.when_flag_clicked(),
        b1.go_to_xy(DOMINO_SPECS[0][1], DOMINO_Y),
        b1.point_in_direction(90),
        b1.wait(0.5),
        b1.play_sound(DOMINO_SPECS[0][4]),
        b1.repeat(9, [b1.turn_right(10)]),
        b1.broadcast(broadcasts[0]),
    )

    # キャラ2, 3: receive -> topple -> broadcast next
    for idx in (1, 2):
        sp = chars[idx]
        b = sp.builder
        b.script(
            b.when_flag_clicked(),
            b.go_to_xy(DOMINO_SPECS[idx][1], DOMINO_Y),
            b.point_in_direction(90),
        )
        b.script(
            b.when_broadcast_received(broadcasts[idx - 1]),
            b.play_sound(DOMINO_SPECS[idx][4]),
            b.repeat(9, [b.turn_right(10)]),
            b.broadcast(broadcasts[idx]),
        )

    # キャラ4: receive 3ばんめ -> topple -> celebrate
    c4 = chars[3]
    b4 = c4.builder
    b4.script(
        b4.when_flag_clicked(),
        b4.go_to_xy(DOMINO_SPECS[3][1], DOMINO_Y),
        b4.point_in_direction(90),
    )
    b4.script(
        b4.when_broadcast_received(broadcasts[2]),
        b4.play_sound(DOMINO_SPECS[3][4]),
        b4.repeat(9, [b4.turn_right(10)]),
        b4.say_for_secs("ゴール！！", 2),
    )

    return proj
