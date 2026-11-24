"""Task 09: 自動信号機・横断歩道 (09_traffic_light)

青→点滅→黄→赤を繰り返し、赤侵入で警告音を鳴らす課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_warning_alarm

TASK_ID = "09_traffic_light"
TASK_TITLE = "じどう しんごうき・おうだんほどう"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

WALKER_START_X = -165
WALKER_START_Y = -65
CROSSWALK_MIN_X = -90
CROSSWALK_MAX_X = 90


def _make_crosswalk_backdrop_svg() -> str:
    stripes = "\n".join(
        f'    <rect x="164" y="{y}" width="152" height="16" rx="2" fill="#ffffff"/>'
        for y in range(186, 336, 30)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- 空と街背景 -->
  <rect x="0" y="0" width="480" height="165" fill="#dbeafe"/>
  <!-- タイトル帯 -->
  <rect x="92" y="8" width="296" height="30" rx="15" fill="#ffffff" stroke="#0284c7" stroke-width="2"/>
  <text x="240" y="28" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="14" font-weight="bold" fill="#0369a1">じどう しんごうき・おうだんほどう</text>

  <!-- 信号の支柱 -->
  <rect x="234" y="96" width="12" height="72" fill="#64748b"/>

  <!-- 左の歩道 (x < -90 -> SVG x < 150) -->
  <rect x="0" y="165" width="150" height="195" fill="#e2e8f0"/>
  <line x1="150" y1="165" x2="150" y2="360" stroke="#94a3b8" stroke-width="3"/>
  <text x="75" y="192" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="12" font-weight="bold" fill="#475569">ほどう</text>

  <!-- 右の歩道 (x > 90 -> SVG x > 330) -->
  <rect x="330" y="165" width="150" height="195" fill="#e2e8f0"/>
  <line x1="330" y1="165" x2="330" y2="360" stroke="#94a3b8" stroke-width="3"/>
  <text x="405" y="192" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="12" font-weight="bold" fill="#475569">ほどう</text>

  <!-- 道路＋横断歩道 (SVG x = 150..330 -> Scratch x = -90..+90) -->
  <rect x="150" y="165" width="180" height="195" fill="#475569"/>
  <g>
{stripes}
  </g>

  <!-- 操作説明 -->
  <rect x="74" y="334" width="332" height="22" rx="11" fill="#ffffff" opacity="0.92"/>
  <text x="240" y="350" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="12" font-weight="bold" fill="#334155">← → キー で ほこうしゃ を うごかそう！（あか は きけん！）</text>
</svg>"""


def _make_traffic_light_svg(state: str) -> str:
    """Create horizontal 3-lamp Japanese traffic light (left=blue/green, center=yellow, right=red)."""
    blue_on = state == "blue"
    yellow_on = state == "yellow"
    red_on = state == "red"

    blue_fill = "#10b981" if blue_on else "#1e293b"
    yellow_fill = "#facc15" if yellow_on else "#1e293b"
    red_fill = "#ef4444" if red_on else "#1e293b"

    glow = ""
    if blue_on:
        glow = '<circle cx="32" cy="26" r="19" fill="#34d399" opacity="0.35"/>'
    elif yellow_on:
        glow = '<circle cx="76" cy="26" r="19" fill="#fde047" opacity="0.35"/>'
    elif red_on:
        glow = '<circle cx="120" cy="26" r="19" fill="#f87171" opacity="0.35"/>'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="152" height="52" viewBox="0 0 152 52">
  <rect x="3" y="3" width="146" height="46" rx="23" fill="#334155" stroke="#0f172a" stroke-width="3"/>
  {glow}
  <circle cx="32" cy="26" r="14" fill="{blue_fill}" stroke="#0f172a" stroke-width="2"/>
  <circle cx="76" cy="26" r="14" fill="{yellow_fill}" stroke="#0f172a" stroke-width="2"/>
  <circle cx="120" cy="26" r="14" fill="{red_fill}" stroke="#0f172a" stroke-width="2"/>
</svg>"""


def _make_walker_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="72" viewBox="0 0 48 72">
  <!-- 黄色い通学帽 -->
  <path d="M 10 18 Q 24 4 38 18 Z" fill="#facc15" stroke="#a16207" stroke-width="2"/>
  <line x1="10" y1="18" x2="42" y2="18" stroke="#a16207" stroke-width="2.5" stroke-linecap="round"/>
  <!-- 顔 -->
  <circle cx="24" cy="25" r="10" fill="#fed7aa" stroke="#9a3412" stroke-width="1.8"/>
  <circle cx="28" cy="24" r="1.8" fill="#1e293b"/>
  <!-- 体（ランドセル＋シャツ） -->
  <rect x="11" y="36" width="8" height="16" rx="3" fill="#ef4444" stroke="#991b1b" stroke-width="1.5"/>
  <rect x="17" y="35" width="15" height="20" rx="5" fill="#3b82f6" stroke="#1d4ed8" stroke-width="1.8"/>
  <!-- 足 -->
  <line x1="21" y1="55" x2="17" y2="69" stroke="#1e293b" stroke-width="4" stroke-linecap="round"/>
  <line x1="28" y1="55" x2="33" y2="69" stroke="#1e293b" stroke-width="4" stroke-linecap="round"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("おうだんほどう", _make_crosswalk_backdrop_svg(), 240, 180)
    )
    var_signal = proj.stage.add_variable(
        "しんごう", "あお", show_monitor=True, monitor_x=8, monitor_y=8
    )

    light = proj.add_sprite(
        name="しんごうき",
        x=0,
        y=105,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    light.add_costume(make_svg_costume("あお", _make_traffic_light_svg("blue"), 76, 26))
    light.add_costume(make_svg_costume("あおてんめつ", _make_traffic_light_svg("off"), 76, 26))
    light.add_costume(make_svg_costume("きいろ", _make_traffic_light_svg("yellow"), 76, 26))
    light.add_costume(make_svg_costume("あか", _make_traffic_light_svg("red"), 76, 26))

    walker = proj.add_sprite(
        name="ほこうしゃ",
        x=WALKER_START_X,
        y=WALKER_START_Y,
        size=100,
        direction=90,
        rotation_style="left-right",
    )
    walker.add_costume(make_svg_costume("あるくひと", _make_walker_svg(), 24, 36))
    walker.add_sound(synth_warning_alarm("けいこくおん"))
    return proj, light, walker, var_signal


def _add_walker_controls(walker: object) -> object:
    """Pre-built left/right arrow controls shared by both template and sample."""
    wb = walker.builder
    return wb.script(
        wb.when_flag_clicked(),
        wb.set_rotation_style("left-right"),
        wb.go_to_xy(WALKER_START_X, WALKER_START_Y),
        wb.point_in_direction(90),
        wb.forever(
            [
                wb.if_then(
                    wb.key_pressed("right arrow"),
                    [wb.point_in_direction(90), wb.change_x_by(5)],
                ),
                wb.if_then(
                    wb.key_pressed("left arrow"),
                    [wb.point_in_direction(-90), wb.change_x_by(-5)],
                ),
            ]
        ),
    )


def build_template() -> Project:
    """Build template with multi-costume traffic light, pre-coded walker controls, alarm, and しんごう var."""
    proj, light, walker, var_signal = _create_base_project()

    lb = light.builder
    l_hat = lb.script(
        lb.when_flag_clicked(),
        lb.go_to_xy(0, 105),
        lb.switch_costume_to("あお"),
        lb.set_variable(var_signal, "あお"),
    )
    light.add_comment(
        text=(
            "【ヒント：しんごうき】\n"
            "「ずっと」の なかで じゅんばんに かえよう：\n"
            "1. しんごう＝「あお」→ コスチューム「あお」→ 3びょう まつ\n"
            "2. てんめつ（3かい くりかえす）：\n"
            "   「あおてんめつ」0.3びょう →「あお」0.3びょう\n"
            "3. しんごう＝「きいろ」→「きいろ」→ 1.5びょう まつ\n"
            "4. しんごう＝「あか」→「あか」→ 3びょう まつ"
        ),
        x=420,
        y=48,
        width=335,
        height=210,
        block=l_hat,
    )

    w_hat = _add_walker_controls(walker)
    walker.add_comment(
        text=(
            "【ヒント：あかしんごう けいこく】\n"
            "さゆうキー の そうさ は もう できているよ！\n"
            "もうひとつ「みどりのはた」スクリプトを つくって：\n"
            "もし (しんごう ＝「あか」) かつ (xざひょう ＞ -90 かつ xざひょう ＜ 90)\n"
            "なら「けいこくおん」を ならして\n"
            "「あぶない！あかしんごう だよ！」と いおう！"
        ),
        x=488,
        y=48,
        width=340,
        height=205,
        block=w_hat,
    )
    return proj


def build_sample() -> Project:
    """Build working traffic light cycle + red-light crosswalk violation alarm."""
    proj, light, walker, var_signal = _create_base_project()

    lb = light.builder
    l_hat = lb.script(
        lb.when_flag_clicked(),
        lb.go_to_xy(0, 105),
        lb.forever(
            [
                lb.set_variable(var_signal, "あお"),
                lb.switch_costume_to("あお"),
                lb.wait(3),
                lb.set_variable(var_signal, "あおてんめつ"),
                lb.repeat(
                    3,
                    [
                        lb.switch_costume_to("あおてんめつ"),
                        lb.wait(0.3),
                        lb.switch_costume_to("あお"),
                        lb.wait(0.3),
                    ],
                ),
                lb.set_variable(var_signal, "きいろ"),
                lb.switch_costume_to("きいろ"),
                lb.wait(1.5),
                lb.set_variable(var_signal, "あか"),
                lb.switch_costume_to("あか"),
                lb.wait(3),
            ]
        ),
    )
    light.add_comment(
        text="【おてほん】あお → てんめつ → きいろ → あか を くりかえします。",
        x=420,
        y=48,
        width=280,
        height=90,
        block=l_hat,
    )

    _add_walker_controls(walker)
    wb = walker.builder
    w_check = wb.script(
        wb.when_flag_clicked(),
        wb.forever(
            [
                wb.if_then(
                    wb.logical_and(
                        wb.eq(var_signal, "あか"),
                        wb.logical_and(
                            wb.gt(wb.x_position(), CROSSWALK_MIN_X),
                            wb.lt(wb.x_position(), CROSSWALK_MAX_X),
                        ),
                    ),
                    [
                        wb.play_sound("けいこくおん"),
                        wb.say_for_secs("あぶない！あかしんごう だよ！", 1.2),
                        wb.go_to_xy(WALKER_START_X, WALKER_START_Y),
                    ],
                )
            ]
        ),
    )
    walker.add_comment(
        text="【おてほん】あかしんごう で おうだんほどう に はいると けいこくおん が なります。",
        x=488,
        y=320,
        width=310,
        height=95,
        block=w_check,
    )
    return proj
