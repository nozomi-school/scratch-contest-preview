"""Task 10: 自動ドア＆入店チャイム (10_auto_door)

人が近づくとチャイムが鳴り左右ドアが連動開閉する課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume, synth_door_chime

TASK_ID = "10_auto_door"
TASK_TITLE = "じどうドア＆にゅうてんチャイム"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

DOOR_Y = -10
LEFT_CLOSED_X = -40
LEFT_OPEN_X = -118
RIGHT_CLOSED_X = 40
RIGHT_OPEN_X = 118
CUSTOMER_START_X = -175
CUSTOMER_START_Y = -120


def _make_store_backdrop_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- お店の外壁 -->
  <rect x="0" y="0" width="480" height="270" fill="#fef9c3"/>
  <!-- 歩道 -->
  <rect x="0" y="270" width="480" height="90" fill="#e2e8f0"/>
  <line x1="0" y1="270" x2="480" y2="270" stroke="#94a3b8" stroke-width="3"/>

  <!-- 看板 -->
  <rect x="76" y="16" width="328" height="46" rx="10" fill="#16a34a" stroke="#14532d" stroke-width="3"/>
  <text x="240" y="47" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="20" font-weight="bold" fill="#ffffff">いらっしゃいませ！ おみせ</text>

  <!-- 入口の店内（奥） (Scratch x=-80..+80 -> SVG x=160..320, y=100..270) -->
  <rect x="154" y="94" width="172" height="176" fill="#334155"/>
  <rect x="160" y="100" width="160" height="170" fill="#fde68a"/>
  <!-- 店内の商品棚シルエット -->
  <rect x="176" y="146" width="128" height="14" rx="3" fill="#f59e0b" opacity="0.6"/>
  <rect x="176" y="182" width="128" height="14" rx="3" fill="#ef4444" opacity="0.5"/>
  <rect x="176" y="218" width="128" height="14" rx="3" fill="#3b82f6" opacity="0.5"/>
  <text x="240" y="132" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" font-weight="bold" fill="#92400e">OPEN</text>

  <!-- 赤外線センサーボックス -->
  <rect x="212" y="76" width="56" height="14" rx="4" fill="#1e293b"/>
  <circle cx="240" cy="83" r="3" fill="#ef4444"/>

  <!-- 操作説明 -->
  <text x="240" y="346" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" font-weight="bold" fill="#334155">やじるしキー で いりぐち に ちかづいて みよう！</text>
</svg>"""


def _make_door_svg(side: str) -> str:
    handle_x = 68 if side == "left" else 12
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="170" viewBox="0 0 80 170">
  <rect x="2" y="2" width="76" height="166" fill="#bae6fd" fill-opacity="0.82" stroke="#475569" stroke-width="4"/>
  <!-- ガラス反射ライン -->
  <line x1="16" y1="22" x2="48" y2="54" stroke="#ffffff" stroke-width="4" stroke-linecap="round" opacity="0.7"/>
  <line x1="20" y1="42" x2="36" y2="58" stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity="0.6"/>
  <!-- 安全ライン帯 -->
  <rect x="4" y="88" width="72" height="14" fill="#16a34a" opacity="0.75"/>
  <!-- 取っ手ライン -->
  <line x1="{handle_x}" y1="70" x2="{handle_x}" y2="115" stroke="#334155" stroke-width="3" stroke-linecap="round"/>
</svg>"""


def _make_sensor_mat_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="144" height="32" viewBox="0 0 144 32">
  <rect x="2" y="2" width="140" height="28" rx="6" fill="#15803d" stroke="#14532d" stroke-width="2"/>
  <rect x="8" y="7" width="128" height="18" rx="3" fill="none" stroke="#86efac" stroke-width="1.5" stroke-dasharray="5 3"/>
</svg>"""


def _make_customer_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="68" viewBox="0 0 48 68">
  <circle cx="24" cy="18" r="12" fill="#fed7aa" stroke="#9a3412" stroke-width="2"/>
  <circle cx="20" cy="17" r="2" fill="#1e293b"/>
  <circle cx="28" cy="17" r="2" fill="#1e293b"/>
  <path d="M 20 23 Q 24 26 28 23" fill="none" stroke="#9a3412" stroke-width="1.8" stroke-linecap="round"/>
  <rect x="13" y="31" width="22" height="22" rx="8" fill="#f97316" stroke="#c2410c" stroke-width="2"/>
  <line x1="19" y1="53" x2="17" y2="65" stroke="#1e293b" stroke-width="4" stroke-linecap="round"/>
  <line x1="29" y1="53" x2="31" y2="65" stroke="#1e293b" stroke-width="4" stroke-linecap="round"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object, object, object, object, object]:
    proj = Project()
    proj.stage.add_costume(
        make_svg_costume("おみせのはいけい", _make_store_backdrop_svg(), 240, 180)
    )
    var_state = proj.stage.add_variable(
        "ドアじょうたい", "しまっている", show_monitor=True, monitor_x=8, monitor_y=8
    )
    bc_open = proj.add_broadcast("ドアひらく")
    bc_close = proj.add_broadcast("ドアしまる")

    sensor = proj.add_sprite(
        name="センサー",
        x=0,
        y=-106,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    sensor.add_costume(make_svg_costume("マット", _make_sensor_mat_svg(), 72, 16))

    left_door = proj.add_sprite(
        name="ひだりドア",
        x=LEFT_CLOSED_X,
        y=DOOR_Y,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    left_door.add_costume(make_svg_costume("ひだりドア", _make_door_svg("left"), 40, 85))

    right_door = proj.add_sprite(
        name="みぎドア",
        x=RIGHT_CLOSED_X,
        y=DOOR_Y,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    right_door.add_costume(make_svg_costume("みぎドア", _make_door_svg("right"), 40, 85))

    customer = proj.add_sprite(
        name="おきゃくさん",
        x=CUSTOMER_START_X,
        y=CUSTOMER_START_Y,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    customer.add_costume(make_svg_costume("おきゃくさん", _make_customer_svg(), 24, 34))
    customer.add_sound(synth_door_chime("チャイムおん"))

    return proj, sensor, left_door, right_door, customer, var_state, bc_open, bc_close


def _add_customer_controls(customer: object, var_state: object) -> object:
    cb = customer.builder
    return cb.script(
        cb.when_flag_clicked(),
        cb.go_to_xy(CUSTOMER_START_X, CUSTOMER_START_Y),
        cb.set_variable(var_state, "しまっている"),
        cb.forever(
            [
                cb.if_then(cb.key_pressed("right arrow"), [cb.change_x_by(6)]),
                cb.if_then(cb.key_pressed("left arrow"), [cb.change_x_by(-6)]),
                cb.if_then(cb.key_pressed("up arrow"), [cb.change_y_by(6)]),
                cb.if_then(cb.key_pressed("down arrow"), [cb.change_y_by(-6)]),
            ]
        ),
    )


def build_template() -> Project:
    """Build template with pre-placed doors, controllable customer, chime sound, and broadcasts."""
    proj, _sensor, left_door, right_door, customer, var_state, _bc_open, _bc_close = (
        _create_base_project()
    )

    lb = left_door.builder
    l_hat = lb.script(lb.when_flag_clicked(), lb.go_to_xy(LEFT_CLOSED_X, DOOR_Y))
    left_door.add_comment(
        text=(
            "【ヒント：ひだりドア】\n"
            "・「ドアひらく」を うけとったとき：\n"
            "   0.4びょうで x=-118, y=-10 に かえる\n"
            "・「ドアしまる」を うけとったとき：\n"
            "   0.4びょうで x=-40, y=-10 に かえる"
        ),
        x=420,
        y=48,
        width=310,
        height=150,
        block=l_hat,
    )

    rb = right_door.builder
    r_hat = rb.script(rb.when_flag_clicked(), rb.go_to_xy(RIGHT_CLOSED_X, DOOR_Y))
    right_door.add_comment(
        text=(
            "【ヒント：みぎドア】\n"
            "・「ドアひらく」を うけとったとき：\n"
            "   0.4びょうで x=118, y=-10 に かえる\n"
            "・「ドアしまる」を うけとったとき：\n"
            "   0.4びょうで x=40, y=-10 に かえる"
        ),
        x=420,
        y=48,
        width=310,
        height=150,
        block=r_hat,
    )

    c_hat = _add_customer_controls(customer, var_state)
    customer.add_comment(
        text=(
            "【ヒント：きょり はんてい＆れんだ ぼうし】\n"
            "キャラの いどう は もう できているよ！\n"
            "「センサー までの きょり ＜ 95」かつ\n"
            "「ドアじょうたい ＝ しまっている」の ときだけ：\n"
            "  ・ドアじょうたい を「あいている」に する\n"
            "  ・「チャイムおん」を ならす\n"
            "  ・「ドアひらく」を おくる\n"
            "はなれたら（きょり ＞ 115）\n"
            "  ・ドアじょうたい を「しまっている」にして「ドアしまる」をおくる！"
        ),
        x=488,
        y=48,
        width=355,
        height=240,
        block=c_hat,
    )
    return proj


def build_sample() -> Project:
    """Build working automatic door with distance sensor, hysteresis, and single chime."""
    proj, _sensor, left_door, right_door, customer, var_state, bc_open, bc_close = (
        _create_base_project()
    )

    lb = left_door.builder
    lb.script(lb.when_flag_clicked(), lb.go_to_xy(LEFT_CLOSED_X, DOOR_Y))
    lb.script(
        lb.when_broadcast_received(bc_open),
        lb.glide_secs_to_xy(0.4, LEFT_OPEN_X, DOOR_Y),
    )
    lb.script(
        lb.when_broadcast_received(bc_close),
        lb.glide_secs_to_xy(0.4, LEFT_CLOSED_X, DOOR_Y),
    )

    rb = right_door.builder
    rb.script(rb.when_flag_clicked(), rb.go_to_xy(RIGHT_CLOSED_X, DOOR_Y))
    rb.script(
        rb.when_broadcast_received(bc_open),
        rb.glide_secs_to_xy(0.4, RIGHT_OPEN_X, DOOR_Y),
    )
    rb.script(
        rb.when_broadcast_received(bc_close),
        rb.glide_secs_to_xy(0.4, RIGHT_CLOSED_X, DOOR_Y),
    )

    _add_customer_controls(customer, var_state)
    cb = customer.builder
    c_sense = cb.script(
        cb.when_flag_clicked(),
        cb.forever(
            [
                cb.if_then(
                    cb.logical_and(
                        cb.lt(cb.distance_to("センサー"), 95),
                        cb.eq(var_state, "しまっている"),
                    ),
                    [
                        cb.set_variable(var_state, "あいている"),
                        cb.play_sound("チャイムおん"),
                        cb.broadcast(bc_open),
                    ],
                ),
                cb.if_then(
                    cb.logical_and(
                        cb.gt(cb.distance_to("センサー"), 115),
                        cb.eq(var_state, "あいている"),
                    ),
                    [
                        cb.set_variable(var_state, "しまっている"),
                        cb.broadcast(bc_close),
                    ],
                ),
            ]
        ),
    )
    customer.add_comment(
        text="【おてほん】ドアじょうたい を かんり することで チャイムの れんだ を ふせぎます。",
        x=488,
        y=340,
        width=320,
        height=95,
        block=c_sense,
    )
    return proj
