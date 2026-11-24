"""Task 25: 花火（カウントダウン） (25_fireworks)

5→0のカウントダウン後に中心から花火を開く課題。
"""

from __future__ import annotations

from builder import (
    Project,
    make_svg_costume,
    synth_beep,
    synth_explosion,
    synth_launch_whistle,
)

TASK_ID = "25_fireworks"
TASK_TITLE = "はなび（カウントダウン）"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

FIREWORK_X = 0
FIREWORK_Y = 20


def _make_night_sky_backdrop_svg() -> str:
    stars = [
        (46, 54, 2.2), (112, 82, 1.8), (176, 44, 2.4), (318, 52, 2.0),
        (392, 74, 2.5), (440, 42, 1.8), (74, 152, 1.7), (418, 146, 2.1),
        (146, 128, 1.6), (344, 118, 1.9), (60, 224, 1.6), (430, 212, 1.8),
    ]
    stars_svg = "\n".join(
        f'  <circle cx="{x}" cy="{y}" r="{r}" fill="#fef08a" opacity="0.85"/>'
        for x, y, r in stars
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- 夜空 -->
  <rect x="0" y="0" width="480" height="360" fill="#0f172a"/>
  <!-- 星空 -->
{stars_svg}

  <!-- タイトル帯 -->
  <rect x="132" y="10" width="236" height="32" rx="16" fill="#1e293b" stroke="#facc15" stroke-width="2"/>
  <text x="250" y="31" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="16" font-weight="bold" fill="#fef08a">カウントダウン はなび！</text>

  <!-- 街のシルエット -->
  <g fill="#1e293b">
    <rect x="0" y="302" width="66" height="58"/>
    <rect x="74" y="286" width="54" height="74"/>
    <rect x="138" y="310" width="70" height="50"/>
    <rect x="218" y="292" width="48" height="68"/>
    <rect x="276" y="306" width="62" height="54"/>
    <rect x="348" y="282" width="58" height="78"/>
    <rect x="414" y="298" width="66" height="62"/>
  </g>
  <!-- 窓あかり -->
  <g fill="#fde047" opacity="0.7">
    <rect x="86" y="298" width="8" height="8"/><rect x="104" y="298" width="8" height="8"/>
    <rect x="86" y="316" width="8" height="8"/><rect x="232" y="304" width="8" height="8"/>
    <rect x="362" y="296" width="8" height="8"/><rect x="380" y="296" width="8" height="8"/>
  </g>
</svg>"""


def _make_firework_spark_svg() -> str:
    """Bright firework streak/orb pointing right (+X) so cloning around 360 deg creates a burst."""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="56" height="24" viewBox="0 0 56 24">
  <!-- 光の尾 -->
  <polygon points="4,12 40,5 40,19" fill="#fb7185" opacity="0.65"/>
  <!-- 輝く光の玉 -->
  <circle cx="42" cy="12" r="9" fill="#f43f5e"/>
  <circle cx="43" cy="12" r="5" fill="#fef08a"/>
  <circle cx="44" cy="12" r="2.2" fill="#ffffff"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("よぞらのはいけい", _make_night_sky_backdrop_svg(), 240, 180)
    )
    var_count = proj.stage.add_variable(
        "カウント", 5, show_monitor=True, monitor_x=8, monitor_y=8
    )

    fw = proj.add_sprite(
        name="はなびパーツ",
        x=FIREWORK_X,
        y=FIREWORK_Y,
        size=100,
        direction=0,
        visible=False,
        rotation_style="all around",
    )
    fw.add_costume(make_svg_costume("ひかりのつぶ", _make_firework_spark_svg(), 28, 12))
    fw.add_sound(synth_beep("ピッおん", freq=987.77, duration=0.14))
    fw.add_sound(synth_launch_whistle("うちあげおん"))
    fw.add_sound(synth_explosion("はなびおん"))
    return proj, fw, fw.builder, var_count


def build_template() -> Project:
    """Build template with centered hidden firework part, countdown var, sounds, and init block."""
    proj, fw, b, var_count = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.hide(),
        b.go_to_xy(FIREWORK_X, FIREWORK_Y),
        b.set_size_to(100),
        b.clear_graphic_effects(),
        b.set_variable(var_count, 5),
    )

    fw.add_comment(
        text=(
            "【ヒント：カウントダウン → はなび！】\n"
            "1.「5かい くりかえす」で カウントダウン：\n"
            "   ・ピッおん → 1びょう まつ → カウント を -1 かえる\n"
            "2. 0 に なったら はなび を ひらく！\n"
            "   ・おわるまで「うちあげおん」→「はなびおん」\n"
            "   ・12かい くりかえす：\n"
            "     じぶんのクローンをつくる → 30ど まわす → いろこうか を 15 かえる\n"
            "3.「クローンされたとき」：\n"
            "   ひょうじする → 25かい くりかえす（5ぽ うごかす＋ゆうれいこうか +4）\n"
            "   → このクローンを さくじょする"
        ),
        x=420,
        y=48,
        width=365,
        height=260,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working 5->0 countdown followed by 12-ray colorful clone firework burst."""
    proj, fw, b, var_count = _create_base_project()

    b.script(
        b.when_flag_clicked(),
        b.hide(),
        b.go_to_xy(FIREWORK_X, FIREWORK_Y),
        b.set_size_to(100),
        b.clear_graphic_effects(),
        b.set_variable(var_count, 5),
        b.repeat(
            5,
            [
                b.play_sound("ピッおん"),
                b.wait(1),
                b.change_variable(var_count, -1),
            ],
        ),
        b.play_sound_until_done("うちあげおん"),
        b.play_sound("はなびおん"),
        b.point_in_direction(0),
        b.repeat(
            12,
            [
                b.create_clone_of("_myself_"),
                b.turn_right(30),
                b.change_effect_by("COLOR", 15),
            ],
        ),
    )

    clone_hat = b.script(
        b.when_start_as_clone(),
        b.show(),
        b.repeat(
            25,
            [
                b.move_steps(5),
                b.change_effect_by("GHOST", 4),
            ],
        ),
        b.delete_this_clone(),
    )

    fw.add_comment(
        text=(
            "【おてほん】\n"
            "5→0 の カウントダウン の あと、\n"
            "12ほうこう に クローンを ひろげて はなび を さかせます。"
        ),
        x=488,
        y=300,
        width=320,
        height=115,
        block=clone_hat,
    )
    return proj
