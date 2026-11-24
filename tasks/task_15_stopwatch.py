"""Task 15: 簡易的ストップウォッチ (15_stopwatch)

5秒前後で止められたか（早い／成功／遅い）を判定する課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_buzzer_fail, synth_chime_success

TASK_ID = "15_stopwatch"
TASK_TITLE = "かんいてき ストップウォッチ"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"


def _make_stopwatch_backdrop_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <rect x="0" y="0" width="480" height="360" fill="#ecfeff"/>

  <!-- タイトル帯 -->
  <rect x="118" y="12" width="268" height="34" rx="17" fill="#ffffff" stroke="#0891b2" stroke-width="2.5"/>
  <text x="252" y="35" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="16" font-weight="bold" fill="#0e7490">5びょう ストップウォッチ！</text>

  <!-- ストップウォッチイラスト装飾 -->
  <rect x="226" y="64" width="28" height="14" rx="4" fill="#64748b"/>
  <circle cx="240" cy="176" r="102" fill="#ffffff" stroke="#0891b2" stroke-width="6"/>
  <circle cx="240" cy="176" r="90" fill="#f0fdfa" stroke="#99f6e4" stroke-width="2"/>
  <text x="240" y="126" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="22" font-weight="bold" fill="#0f766e">もくひょう：5.0 びょう</text>
  <text x="240" y="150" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" fill="#0e7490">（4.5 〜 5.5 びょう で せいこう！）</text>

  <!-- 下部ガイド -->
  <rect x="66" y="302" width="348" height="38" rx="19" fill="#ffffff" stroke="#06b6d4" stroke-width="2"/>
  <text x="240" y="326" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="14" font-weight="bold" fill="#155e75">5びょう に なったら スペースキー で とめよう！</text>
</svg>"""


def _make_guide_char_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="84" height="84" viewBox="0 0 84 84">
  <!-- かわいいタイマー案内ロボ -->
  <line x1="42" y1="6" x2="42" y2="16" stroke="#0f766e" stroke-width="4" stroke-linecap="round"/>
  <circle cx="42" cy="6" r="5" fill="#f59e0b"/>
  <rect x="14" y="16" width="56" height="52" rx="16" fill="#14b8a6" stroke="#0f766e" stroke-width="3"/>
  <rect x="22" y="25" width="40" height="24" rx="8" fill="#ffffff"/>
  <circle cx="33" cy="37" r="4" fill="#0f172a"/>
  <circle cx="51" cy="37" r="4" fill="#0f172a"/>
  <path d="M 34 56 Q 42 62 50 56" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("ストップウォッチはいけい", _make_stopwatch_backdrop_svg(), 240, 180)
    )
    # テンプレ仕様：タイマー表示オン設定済！
    proj.show_timer_monitor(visible=True, x=8, y=8)
    var_record = proj.stage.add_variable(
        "きろく", 0, show_monitor=True, monitor_x=8, monitor_y=40
    )

    guide = proj.add_sprite(
        name="あんないキャラ",
        x=0,
        y=-45,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    guide.add_costume(make_svg_costume("あんないロボ", _make_guide_char_svg(), 42, 42))
    guide.add_sound(synth_chime_success("せいこうおん"))
    guide.add_sound(synth_buzzer_fail("しっぱいおん"))
    return proj, guide, guide.builder, var_record


def build_template() -> Project:
    """Build template with guide character, backdrop, timer monitor enabled, and init block."""
    proj, guide, b, var_record = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, -45),
        b.set_variable(var_record, 0),
        b.reset_timer(),
        b.say("5びょう だ と おもったら スペースキー を おしてね！"),
    )

    guide.add_comment(
        text=(
            "【ヒント：5びょう はんてい】\n"
            "1.「スペースキーが おされた まで まつ」\n"
            "2.「きろく を タイマー に する」\n"
            "3.「もし〜なら、でなければ」で 3つ に わけよう：\n"
            "   ・きろく ＜ 4.5 →「はやいよ！」\n"
            "   ・きろく ＞ 5.5 →「おそいよ！」\n"
            "   ・それいがい（4.5〜5.5）→「だいせいこう！」\n"
            "   ※ かつ（and）と ふとうごう で はんい はんてい しても OK！"
        ),
        x=420,
        y=48,
        width=345,
        height=230,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working 5-second stopwatch challenge with early/success/late judgment."""
    proj, guide, b, var_record = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.go_to_xy(0, -45),
        b.set_variable(var_record, 0),
        b.say("5びょう だ と おもったら スペースキー を おしてね！"),
        b.wait_until(b.logical_not(b.key_pressed("space"))),
        b.reset_timer(),
        b.wait_until(b.key_pressed("space")),
        b.set_variable(
            var_record,
            b.divide(b.round_num(b.multiply(b.timer(), 100)), 100),
        ),
        b.if_else(
            b.lt(var_record, 4.5),
            then_body=[
                b.play_sound("しっぱいおん"),
                b.say(b.join(var_record, "びょう！ はやいよ！")),
            ],
            else_body=[
                b.if_else(
                    b.gt(var_record, 5.5),
                    then_body=[
                        b.play_sound("しっぱいおん"),
                        b.say(b.join(var_record, "びょう！ おそいよ！")),
                    ],
                    else_body=[
                        b.play_sound("せいこうおん"),
                        b.say(b.join(var_record, "びょう！ だいせいこう！")),
                    ],
                )
            ],
        ),
    )

    guide.add_comment(
        text=(
            "【おてほん】\n"
            "タイマー を リセットして スペースキー を まち、\n"
            "4.5びょう みまん＝はやい、5.5びょう よりおおきい＝おそい、\n"
            "4.5〜5.5びょう＝せいこう と はんていします。"
        ),
        x=420,
        y=48,
        width=320,
        height=135,
        block=hat,
    )
    return proj
