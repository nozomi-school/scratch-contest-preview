"""Task 03: ボードゲーム盤形成 (03_checkerboard)

スタンプで4×4などの市松模様の盤面を描く課題。
"""

from __future__ import annotations

from builder import Project, make_svg_costume

TASK_ID = "03_board_grid"
TASK_TITLE = "ボードゲームばん けいせい"

FONT_FAMILY = "'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif"

START_X = -90
START_Y = 90
TILE_SIZE = 60


def _make_board_backdrop_svg() -> str:
    """Create a 480x360 wooden table with a 240x240 4x4 board guide frame centered at (240, 180)."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <!-- 背景テーブル -->
  <rect x="0" y="0" width="480" height="360" fill="#fef3c7"/>
  <!-- タイトル帯 -->
  <rect x="108" y="10" width="264" height="32" rx="16" fill="#ffffff" stroke="#b45309" stroke-width="2"/>
  <text x="240" y="32" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="16" font-weight="bold" fill="#78350f">4×4 の ボードばん を つくろう！</text>

  <!-- 盤面の外枠（中央 240x240 のエリア: x=120..360, y=60..300） -->
  <rect x="110" y="50" width="260" height="260" rx="10" fill="#92400e" stroke="#451a03" stroke-width="3"/>
  <rect x="120" y="60" width="240" height="240" fill="#f8fafc" stroke="#451a03" stroke-width="2"/>

  <!-- うすい4x4ガイド線 -->
  <g stroke="#cbd5e1" stroke-width="1" stroke-dasharray="4 4">
    <line x1="180" y1="60" x2="180" y2="300"/>
    <line x1="240" y1="60" x2="240" y2="300"/>
    <line x1="300" y1="60" x2="300" y2="300"/>
    <line x1="120" y1="120" x2="360" y2="120"/>
    <line x1="120" y1="180" x2="360" y2="180"/>
    <line x1="120" y1="240" x2="360" y2="240"/>
  </g>

  <!-- 下部ガイド -->
  <text x="240" y="340" text-anchor="middle" font-family="{FONT_FAMILY}" font-size="13" fill="#78350f">1マス ＝ 60ぽ ｜ しろ・くろ を こうご に スタンプしよう！</text>
</svg>"""


def _make_tile_svg(fill: str, stroke: str, accent: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 60 60">
  <rect x="1" y="1" width="58" height="58" fill="{fill}" stroke="{stroke}" stroke-width="2"/>
  <rect x="6" y="6" width="48" height="48" fill="none" stroke="{accent}" stroke-width="1.2" opacity="0.45"/>
</svg>"""


def _create_base_project() -> tuple[Project, object, object, object, object]:
    proj = Project()
    proj.add_extension("pen")

    proj.stage.add_costume(
        make_svg_costume("ボードのはいけい", _make_board_backdrop_svg(), 240, 180)
    )
    var_row = proj.stage.add_variable("ぎょう", 0, show_monitor=False)
    var_col = proj.stage.add_variable("れつ", 0, show_monitor=False)

    tile = proj.add_sprite(
        name="マス",
        x=START_X,
        y=START_Y,
        size=100,
        direction=90,
        rotation_style="don't rotate",
    )
    tile.add_costume(make_svg_costume("しろ", _make_tile_svg("#f8fafc", "#94a3b8", "#cbd5e1"), 30, 30))
    tile.add_costume(make_svg_costume("くろ", _make_tile_svg("#334155", "#0f172a", "#64748b"), 30, 30))
    return proj, tile, tile.builder, var_row, var_col


def build_template() -> Project:
    """Build template with white/black tile costumes, pen init, start pos, and variables."""
    proj, tile, b, var_row, var_col = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.pen_clear(),
        b.show(),
        b.switch_costume_to("しろ"),
        b.go_to_xy(START_X, START_Y),
        b.set_variable(var_row, 0),
        b.set_variable(var_col, 0),
    )

    tile.add_comment(
        text=(
            "【ヒント：いちまつ もよう（4×4）】\n"
            "・1マス の おおきさ は 60 だよ！\n"
            "・スタートいち は x = -90, y = 90。\n\n"
            "「4かい くりかえす（たて）」の なかに\n"
            "「4かい くりかえす（よこ）」を いれよう：\n"
            "  よこ：スタンプ → xを 60 かえる → つぎのコスチューム\n\n"
            "★ポイント（しまもよう バグ ぼうし）：\n"
            "4マスは ぐうすう なので、1ぎょう おわるたびに\n"
            "もう1かい「つぎのコスチューム」を いれてから\n"
            "xを -90 に もどして yを -60 かえよう！"
        ),
        x=420,
        y=48,
        width=330,
        height=260,
        block=hat,
    )
    return proj


def build_sample() -> Project:
    """Build working 4x4 checkerboard pattern using nested loops and row parity shift."""
    proj, tile, b, var_row, var_col = _create_base_project()

    hat = b.script(
        b.when_flag_clicked(),
        b.pen_clear(),
        b.show(),
        b.switch_costume_to("しろ"),
        b.go_to_xy(START_X, START_Y),
        b.set_variable(var_row, 0),
        b.set_variable(var_col, 0),
        b.repeat(
            4,
            [
                b.change_variable(var_row, 1),
                b.set_variable(var_col, 0),
                b.set_x(START_X),
                b.repeat(
                    4,
                    [
                        b.change_variable(var_col, 1),
                        b.pen_stamp(),
                        b.change_x_by(TILE_SIZE),
                        b.next_costume(),
                    ],
                ),
                b.next_costume(),
                b.change_y_by(-TILE_SIZE),
            ],
        ),
        b.hide(),
    )

    tile.add_comment(
        text=(
            "【おてほん】\n"
            "4×4 の にじゅうループ で スタンプし、\n"
            "1ぎょう おわるごとに もう1かい いろを きりかえることで\n"
            "きれいな いちまつ もよう に なります。"
        ),
        x=420,
        y=48,
        width=300,
        height=135,
        block=hat,
    )
    return proj
