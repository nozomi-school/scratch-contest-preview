"""Task 27: お掃除ロボット可視化 (27_vacuum_robot)

跳ね返り移動しながらゴミ回収・軌跡を可視化する課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_chime_bath, synth_pickup_coin

TASK_ID = "27_vacuum_robot"
TASK_TITLE = "おそうじ ロボット かしか"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

DUST_POSITIONS = [
    (-150, 95),
    (145, 85),
    (-135, -90),
    (140, -85),
    (15, 110),
]


def _make_room_backdrop_svg() -> str:
    planks = "\n".join(
        f'    <line x1="12" y1="{y}" x2="468" y2="{y}"/>'
        for y in range(44, 348, 36)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- 部屋の壁枠 -->
  <rect x="0" y="0" width="480" height="360" fill="#cbd5e1"/>
  <!-- フローリング床 -->
  <rect x="12" y="12" width="456" height="336" rx="8" fill="#fef3c7" stroke="#92400e" stroke-width="4"/>
  <g stroke="#e5cfa3" stroke-width="1.5">
{planks}
  </g>

  <!-- タイトル帯 -->
  <rect x="128" y="16" width="244" height="30" rx="15" fill="#ffffff" opacity="0.92" stroke="#0284c7" stroke-width="2"/>
  <text x="250" y="36" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="15" font-weight="bold" fill="#0369a1">おそうじ ロボット かしか！</text>
</svg>"""


def _make_robot_svg() -> str:
    """Round vacuum robot facing RIGHT (+X) with clear directional bumper."""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 52 52">
  <!-- 本体 -->
  <circle cx="26" cy="26" r="22" fill="#f8fafc" stroke="#334155" stroke-width="3"/>
  <!-- 前面バンパー（右側＝進行方向） -->
  <path d="M 34 6 A 22 22 0 0 1 34 46" fill="none" stroke="#0284c7" stroke-width="5" stroke-linecap="round"/>
  <!-- 中央ボタン -->
  <circle cx="24" cy="26" r="8" fill="#38bdf8" stroke="#0369a1" stroke-width="2"/>
  <!-- 向き矢印 -->
  <polygon points="36,21 44,26 36,31" fill="#0284c7"/>
</svg>"""


def _make_dust_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 34 34">
  <g fill="#94a3b8" stroke="#64748b" stroke-width="1.5">
    <circle cx="13" cy="17" r="7"/>
    <circle cx="21" cy="15" r="8"/>
    <circle cx="17" cy="22" r="6"/>
  </g>
  <circle cx="14" cy="14" r="2" fill="#cbd5e1"/>
  <circle cx="22" cy="18" r="2" fill="#cbd5e1"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object]:
    proj = Project()
    proj.add_extension("pen")

    proj.stage.add_costume(
        make_svg_costume("へやのはいけい", _make_room_backdrop_svg(), 240, 180)
    )
    var_collected = proj.stage.add_variable(
        "とったごみ", 0, show_monitor=True, monitor_x=16, monitor_y=16
    )

    robot = proj.add_sprite(
        name="おそうじロボ",
        x=0,
        y=0,
        size=100,
        direction=53,
        rotation_style="all around",
    )
    robot.add_costume(make_svg_costume("ロボット", _make_robot_svg(), 26, 26))
    robot.add_sound(synth_chime_bath("かんりょうおん"))

    dust_costume = make_svg_costume("ほこり", _make_dust_svg(), 17, 17)
    pickup_sound = synth_pickup_coin("ぽんおん")

    # テンプレ仕様：ゴミ複数（ゴミ側消滅コード済！）
    for idx, (gx, gy) in enumerate(DUST_POSITIONS, start=1):
        dust = proj.add_sprite(
            name=f"ゴミ{idx}",
            x=gx,
            y=gy,
            size=100,
            direction=90,
            rotation_style="don't rotate",
        )
        dust.add_costume(dust_costume)
        dust.add_sound(pickup_sound)
        db = dust.builder
        db.script(
            db.when_flag_clicked(),
            db.go_to_xy(gx, gy),
            db.show(),
            db.wait_until(db.touching_object("おそうじロボ")),
            db.play_sound("ぽんおん"),
            db.change_variable(var_collected, 1),
            db.hide(),
        )

    return proj, robot, robot.builder, var_collected


def build_template() -> Project:
    """Build template with room backdrop, pen-ready robot, and 5 self-vanishing dust sprites."""
    proj, robot, b, var_collected = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.pen_clear(),
        b.pen_up(),
        b.pen_set_color("#7dd3fc"),
        b.pen_set_size(14),
        b.go_to_xy(0, 0),
        b.point_in_direction(53),
        b.set_variable(var_collected, 0),
    )

    robot.add_comment(
        text=(
            "【ヒント：おそうじ ロボット】\n"
            "ゴミがわ の しょうめつコード は もう できているよ！\n"
            "しょきか の あとに つなげて みよう：\n"
            "1.「ペンをおろす」（とおった みち が みえる！）\n"
            "2.「とったごみ ＝ 5 まで くりかえす」（または ずっと）：\n"
            "   ・8ぽ うごかす\n"
            "   ・もし はしに ついたら、はねかえる\n"
            "3. ぜんぶ とれたら：\n"
            "   ・ペンをあげる →「かんりょうおん」→「おそうじ かんりょう！」"
        ),
        x=420,
        y=48,
        width=355,
        height=240,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working autonomous bouncing vacuum robot leaving a clean swept trail."""
    proj, robot, b, var_collected = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.pen_clear(),
        b.pen_up(),
        b.pen_set_color("#7dd3fc"),
        b.pen_set_size(14),
        b.go_to_xy(0, 0),
        b.point_in_direction(53),
        b.set_variable(var_collected, 0),
        b.pen_down(),
        b.repeat_until(
            b.eq(var_collected, len(DUST_POSITIONS)),
            [
                b.move_steps(8),
                b.if_on_edge_bounce(),
            ],
        ),
        b.pen_up(),
        b.play_sound("かんりょうおん"),
        b.say("おそうじ かんりょう！ ぴかぴか だよ！"),
    )

    robot.add_comment(
        text=(
            "【おてほん】\n"
            "ななめ（53ど）に はねかえり ながら そうじ し、\n"
            "ペンで とおった きせき を かしか します。"
        ),
        x=420,
        y=48,
        width=310,
        height=115,
        block=hat,
    )
    return proj
