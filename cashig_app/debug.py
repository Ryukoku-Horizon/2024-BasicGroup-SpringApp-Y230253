import flet as ft
import sqlite3
import random
import os
import time
import asyncio

from exchange_calculate import calculate_payment

# --------------------
# DB操作：ランキング保存／取得
def save_ranking(score, player="anonymous", db_path="flet_app.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # rankingテーブルが無ければ作成
    cursor.execute("""CREATE TABLE IF NOT EXISTS ranking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player TEXT,
                        score INTEGER,
                        datetime TEXT)""")
    cursor.execute(
        "INSERT INTO ranking (player, score, datetime) VALUES (?, ?, datetime('now'))",
        (player, score)
    )
    conn.commit()
    conn.close()

# rankingテーブル作成の修正（get_ranking() でテーブルがなければ作成）
def get_ranking(db_path="flet_app.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS ranking (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               player TEXT,
               score INTEGER,
               datetime TEXT)"""
    )
    conn.commit()
    cursor.execute("SELECT player, score, datetime FROM ranking ORDER BY score DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# --------------------
# DBからランダムな注文取得
def fetch_random_orders(db_path="flet_app.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, image FROM line_list")
    all_orders = [{"name": row[0], "price": row[1], "image": row[2]} for row in cursor.fetchall()]
    conn.close()
    n = random.randint(1, 6)
    orders = random.choices(all_orders, k=n)
    combined = {}
    for order in orders:
        key = order["name"]
        if key in combined:
            combined[key]["qty"] += 1
        else:
            order["qty"] = 1
            combined[key] = order
    return list(combined.values())

# --------------------
# 注文内容一致判定ヘルパー
def is_orders_matching(customer_order, processed_orders) -> bool:
    if len(customer_order) != len(processed_orders):
        return False
    sorted_customer = sorted(customer_order, key=lambda x: x["name"])
    sorted_processed = sorted(processed_orders, key=lambda x: x["name"])
    for cust, proc in zip(sorted_customer, sorted_processed):
        if cust["name"] != proc["name"] or cust["qty"] != proc["qty"]:
            return False
    return True

# --------------------
# Dummy: 効果音再生（mp3ファイル名を指定）
def play_sound(filename: str):
    # flet の Audio ウィジェットを使用するか
    # 今回は placeholder としてコンソール出力
    print(f"Playing sound: {filename}")
    # 例: page.controls.append(ft.Audio(src=filename, autoplay=True))

# --------------------
# Dummy: 怒り演出（動画またはGIF再生）
def show_angry(page: ft.Page):
    # 怒っている動画やGIFを表示する例
    # assets/angry.gif を想定
    angry_control = ft.Image(src="assets/angry.gif", width=300, height=300)
    page.dialog = ft.AlertDialog(title=ft.Text("お客さんが怒ってます！"), content=angry_control)
    page.dialog.open = True
    page.update()
    # 3秒後に閉じる（※実装例）
    time.sleep(3)
    page.dialog.open = False
    page.update()

# --------------------
# ホーム画面
async def start_game(e):
    await game_view(e.page)

async def show_ranking(e):
    await ranking_view(e.page)

def home_view(page: ft.Page):
    page.views.clear()
    home = ft.View(
        route="/home",
        controls=[
            ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("レジ打ちゲーム", size=40, weight="bold"),
                    ft.ElevatedButton("ゲーム開始", on_click=start_game),
                    ft.ElevatedButton("ランキング", on_click=show_ranking)
                ]
            )
        ]
    )
    page.views.append(home)
    page.go(home.route)

# --------------------
# ランキング画面
def ranking_view(page: ft.Page):
    rankings = get_ranking()
    ranking_controls = []
    for r in rankings:
        ranking_controls.append(ft.Text(f"{r[0]}: {r[1]}({r[2]})"))
    view = ft.View(
        route="/ranking",
        controls=[
            ft.Column(
                controls=[
                    ft.Text("ランキング", size=30, weight="bold"),
                    ft.Column(controls=ranking_controls, scroll=True),
                    ft.ElevatedButton("ホームへ", on_click=lambda e: home_view(page))
                ]
            )
        ]
    )
    page.views.append(view)
    page.go(view.route)

# --------------------
# ゲーム画面
async def game_view(page: ft.Page):
    page.views.clear()
    # 注文取得
    customer_order = fetch_random_orders()
    order_sum = sum(item["price"] * item["qty"] for item in customer_order)
    customer_total = order_sum + random.randint(50, 500)
    simulated_payment = calculate_payment(order_sum, error_rate=0.9, max_payment=customer_total)

    # ゲーム状態
    lives = [3]        # リストにラップして参照渡し
    mistakes = [0]     # 同上
    score = 0
    start_time = time.time()
    change_selected = 0
    processed_orders = []  # ここは後の操作に合わせて更新

    # 表示部品作成（order_info, timer_display, などは既存実装）
    order_info = ft.Column(
        controls=[
            ft.Text("客側注文内容", size=20, weight="bold", color="blue"),
            ft.Divider(),
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Image(src=os.path.join("assets", "images", item["image"]).replace("\\", "/"),
                                     width=50, height=50, fit="contain"),
                            ft.Text(f"{item['name']}  {item['price']}円 x {item['qty']}")
                        ]
                    ) for item in customer_order
                ],
                spacing=5
            ),
            ft.Divider(),
            ft.Text(f"合計金額: {order_sum}円"),
            ft.Text(f"実際の支払い: {simulated_payment}円"),
            ft.Text(f"支払い可能金額: {customer_total}円")
        ]
    )

    change_display = ft.Text(f"お釣り: {change_selected}円", size=20, color="green")
    life_display = ft.Text(f"ライフ: {lives[0]}", size=20, color="red")
    timer_display = ft.Text("残り時間: 120秒", size=20, color="purple")
    score_display = ft.Text("スコア: 0", size=20, color="black")

    # 画像ボタン(硬貨)部分は先の回答の通り（ft.GestureDetector で実装）
    coin_values = [1, 5, 10, 50, 100, 500, 1000]
    def coin_click(e, value):
        nonlocal change_selected
        change_selected += value
        change_display.value = f"お釣り: {change_selected}円"
        play_sound("click.mp3")
        page.update()

    coin_buttons = ft.Row(
        spacing=10,
        controls=[
            ft.GestureDetector(
                content=ft.Image(src=f"assets/coins/{v}yen.png", width=50, height=50, fit="contain"),
                on_tap=lambda e, v=v: coin_click(e, v)
            ) for v in coin_values
        ]
    )

    # 制限時間タイマー（2分＝120秒）
    async def timer_loop(page, start_time, timer_display, lives_ref, mistakes_ref, score, customer_order, processed_orders):
        while True:
            await asyncio.sleep(1)
            elapsed = int(time.time() - start_time)
            remaining = 120 - elapsed
            if remaining <= 0:
                play_sound("timeout.mp3")
                show_angry(page)
                lives_ref[0] -= 1  # lives をリスト[初期値]でラップして参照渡し
                mistakes_ref[0] += 1
                timer_display.value = "残り時間: 0秒"
                page.update()
                if mistakes_ref[0] >= 3:
                    await game_over(page, score)  # ゲームオーバー画面へ
                else:
                    await game_view(page)         # 次の注文へ
                break
            else:
                timer_display.value = f"残り時間: {remaining}秒"
                page.update()

    asyncio.create_task(timer_loop(page, start_time, timer_display, lives, mistakes, score, customer_order, processed_orders))

    # 会計処理例（async で書く場合、on_click ハンドラも async）
    async def checkout(e):
        expected_change = simulated_payment - order_sum
        if change_selected == expected_change and is_orders_matching(customer_order, processed_orders):
            elapsed = int(time.time() - start_time)
            score = max(0, (120 - elapsed)) + (len(customer_order) * 10)
            score_display.value = f"スコア: {score}"
            play_sound("success.mp3")
            page.update()
            # 次の注文へ
            await game_view(page)
        else:
            play_sound("error.mp3")
            show_angry(page)
            mistakes[0] += 1
            if mistakes[0] >= 3:
                await game_over(page, score)
            else:
                await game_view(page)

    checkout_button = ft.ElevatedButton("会計", on_click=checkout)

    # ゲーム画面レイアウトの構築（既存コードに合わせて）
    game_view_control = ft.View(
        route="/game",
        controls=[
            ft.Column(
                controls=[
                    order_info,
                    ft.Divider(),
                    ft.Row(controls=[life_display, timer_display, score_display], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                    ft.Divider(),
                    coin_buttons,
                    ft.Divider(),
                    change_display,
                    ft.Divider(),
                    checkout_button
                ],
                scroll=True
            )
        ]
    )
    page.views.append(game_view_control)
    page.go(game_view_control.route)

# --------------------
# ゲームオーバー画面
async def game_over(page: ft.Page, final_score: int):
    play_sound("gameover.mp3")
    # ランキング保存
    save_ranking(final_score)
    over_view = ft.View(
        route="/gameover",
        controls=[
            ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(f"GAME OVER\n最終スコア: {final_score}", size=30, weight="bold"),
                    ft.ElevatedButton("リトライ", on_click=lambda e: asyncio.create_task(game_view(page))),
                    ft.ElevatedButton("ホームへ", on_click=lambda e: home_view(page))
                ]
            )
        ]
    )
    page.views.append(over_view)
    page.go(over_view.route)

# --------------------
def main(page: ft.Page):
    page.title = "レジ打ちゲーム"
    page.vertical_alignment = "start"
    page.views.clear()
    # 起動時はホーム画面
    home_view(page)

ft.app(target=main, assets_dir="assets")
