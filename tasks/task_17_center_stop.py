"""Task 17: ぴったり真ん中ストップ (17_center_stop)

左右に往復するバーを、スペースキーで中央の赤いゾーン内に止められたか判定する課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_buzzer_fail, synth_chime_success

TASK_ID = "17_center_stop"
TASK_TITLE = "ぴったりまんなかストップ"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

INITIAL_BAR_X = -180
ZONE_HALF_WIDTH = 35  # Red zone spans Scratch x in [-35, +35] (width = 70px)


def _make_game_backdrop_svg() -> str:
    """Create a 480x360 horizontal gauge backdrop with a red target zone in the center."""
    zone_x = 240 - ZONE_HALF_WIDTH
    zone_w = ZONE_HALF_WIDTH * 2

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- 明るいゲーム画面背景 -->
  <rect x="0" y="0" width="480" height="360" fill="#fffbeb"/>

  <!-- 装飾ドット -->
  <g fill="#fde68a" opacity="0.65">
    <circle cx="36" cy="40" r="14"/>
    <circle cx="444" cy="48" r="18"/>
    <circle cx="48" cy="318" r="16"/>
    <circle cx="432" cy="312" r="14"/>
  </g>

  <!-- タイトル帯 -->
  <rect x="86" y="18" width="308" height="40" rx="20" fill="#ffffff" stroke="#f59e0b" stroke-width="2.5"/>
  <text x="240" y="45" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="19" font-weight="bold" fill="#b45309">ぴったり まんなか ストップ！</text>

  <!-- ゲージ外枠（左右の端まで往復できるトラック） -->
  <rect x="8" y="140" width="464" height="80" rx="14" fill="#e2e8f0" stroke="#475569" stroke-width="3"/>
  <!-- 左・右のはずれゾーン -->
  <rect x="12" y="144" width="456" height="72" rx="10" fill="#f1f5f9"/>

  <!-- まんなかの赤いあたりゾーン (Scratch x = -35..+35 -> SVG x = 205..275) -->
  <rect x="{zone_x}" y="142" width="{zone_w}" height="76" fill="#ef4444"/>
  <line x1="{zone_x}" y1="142" x2="{zone_x}" y2="218" stroke="#991b1b" stroke-width="2"/>
  <line x1="{zone_x + zone_w}" y1="142" x2="{zone_x + zone_w}" y2="218" stroke="#991b1b" stroke-width="2"/>

  <!-- まんなか基準線 -->
  <line x1="240" y1="142" x2="240" y2="218" stroke="#ffffff" stroke-width="2" stroke-dasharray="5 4" opacity="0.9"/>

  <!-- あたりラベル -->
  <rect x="196" y="102" width="88" height="28" rx="14" fill="#ef4444"/>
  <text x="240" y="121" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="14" font-weight="bold" fill="#ffffff">あたり！</text>
  <polygon points="240,138 233,129 247,129" fill="#ef4444"/>

  <!-- 座標ヒント目盛り -->
  <text x="{zone_x}" y="236" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="11" fill="#b91c1c">-35</text>
  <text x="240" y="236" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="11" font-weight="bold" fill="#b91c1c">0</text>
  <text x="{zone_x + zone_w}" y="236" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="11" fill="#b91c1c">+35</text>

  <!-- 下部の操作説明 -->
  <rect x="52" y="284" width="376" height="40" rx="20" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
  <text x="240" y="310" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="15" font-weight="bold" fill="#334155">スペースキー で あかい ゾーン に とめよう！</text>
</svg>"""


def _make_bar_sprite_svg() -> str:
    """Create a 24x112 high-contrast moving bar sprite centered at (12, 56)."""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="112" viewBox="0 0 24 112">
  <!-- 上矢印マーカー -->
  <polygon points="12,18 4,4 20,4" fill="#facc15" stroke="#1e293b" stroke-width="2"/>
  <!-- バー本体 -->
  <rect x="7" y="16" width="10" height="80" rx="4" fill="#1e293b" stroke="#ffffff" stroke-width="2.5"/>
  <!-- まんなか白いアクセント -->
  <rect x="10" y="46" width="4" height="20" rx="2" fill="#38bdf8"/>
  <!-- 下矢印マーカー -->
  <polygon points="12,94 4,108 20,108" fill="#facc15" stroke="#1e293b" stroke-width="2"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("ゲージはいけい", _make_game_backdrop_svg(), 240, 180)
    )

    bar = proj.add_sprite(
        name="バー",
        x=INITIAL_BAR_X,
        y=0,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    bar.add_costume(make_svg_costume("うごくバー", _make_bar_sprite_svg(), 12, 56))
    bar.add_sound(synth_chime_success("せいこうおん"))
    bar.add_sound(synth_buzzer_fail("しっぱいおん"))
    return proj, bar, bar.builder


def build_template() -> Project:
    """Build remix template with red-zone backdrop, bar sprite, sounds, and init block."""
    proj, bar, b = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.set_rotation_style("don't rotate"),
        b.go_to_xy(INITIAL_BAR_X, 0),
        b.point_in_direction(90),
    )

    bar.add_comment(
        text=(
            "【ヒント：ぴったり まんなか ストップ】\n"
            "1.「スペースキーが おされた まで くりかえす」の なかで：\n"
            "   ・12ぽ うごかす\n"
            "   ・もし はしに ついたら、はねかえる\n\n"
            "2. とまったあと、「もし〜なら、でなければ」で はんてい：\n"
            "   じょうけん：(xざひょう ＞ -36) かつ (xざひょう ＜ 36)\n"
            "   ※「あかいろに ふれた」でも OK！\n"
            "   ・あたり →「せいこうおん」を ならして「せいこう！」\n"
            "   ・はずれ →「しっぱいおん」を ならして「ざんねん！」"
        ),
        x=380,
        y=48,
        width=340,
        height=245,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working reference solution that bounces bar until Space and judges center zone."""
    proj, bar, b = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.set_rotation_style("don't rotate"),
        b.go_to_xy(INITIAL_BAR_X, 0),
        b.point_in_direction(90),
        b.repeat_until(
            b.key_pressed("space"),
            [
                b.move_steps(12),
                b.if_on_edge_bounce(),
            ],
        ),
        b.if_else(
            b.logical_and(
                b.gt(b.x_position(), -(ZONE_HALF_WIDTH + 1)),
                b.lt(b.x_position(), ZONE_HALF_WIDTH + 1),
            ),
            then_body=[
                b.play_sound("せいこうおん"),
                b.say_for_secs("せいこう！", 2),
            ],
            else_body=[
                b.play_sound("しっぱいおん"),
                b.say_for_secs("ざんねん！", 2),
            ],
        ),
    )

    bar.add_comment(
        text=(
            "【おてほん】\n"
            "スペースキーが おされるまで さゆうに おうふくし、\n"
            "とまった xざひょう が -35〜35 の あいだ なら\n"
            "せいこうおん＋「せいこう！」、そと なら しっぱいおん＋「ざんねん！」"
        ),
        x=380,
        y=48,
        width=320,
        height=140,
        block=hat,
    )
    return proj
