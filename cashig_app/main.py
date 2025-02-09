import threading
import flet as ft
import sqlite3
import random
import os
import asyncio
import time
from exchange_calculate import calculate_payment
import pygame 
from score import record_ranking  # ranking 登録用

pygame.mixer.init()
global_score = 0
global_lives = 3

def fetch_random_orders(db_path="flet_app.db"):
    # 全商品を取得してからランダムに選ぶ（重複もあり、個数をまとめる）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, image FROM line_list")
    all_orders = [{"name": row[0], "price": row[1], "image": row[2]} for row in cursor.fetchall()]
    conn.close()
    # ランダムな注文個数（1～6）で抽出（重複あり）
    n = random.randint(1, 6)
    orders = random.choices(all_orders, k=n)
    # 同じ商品の場合、qty を集計
    combined = {}
    for order in orders:
        key = order["name"]
        if key in combined:
            combined[key]["qty"] += 1
        else:
            order["qty"] = 1
            combined[key] = order
    return list(combined.values())

# 注文内容の一致を判定するヘルパー関数
def is_orders_matching(customer_order, processed_orders) -> bool:
    if len(customer_order) != len(processed_orders):
        return False
    sorted_customer = sorted(customer_order, key=lambda x: x["name"])
    sorted_processed = sorted(processed_orders, key=lambda x: x["name"])
    for cust, proc in zip(sorted_customer, sorted_processed):
        if cust["name"] != proc["name"]:
            return False
        if cust["price"] != proc["price"]:
            return False
        if cust.get("qty", 1) != proc.get("qty", 1):
            return False
    return True

def play_sound(filename: str):
    # assets/sounds フォルダ内のサウンドファイルを再生
    sound_path = os.path.join("assets", "sounds", filename)
    try:
        sound = pygame.mixer.Sound(sound_path)
        sound.set_volume(0.1)
        sound.play()
    except Exception as ex:
        print(f"Error playing sound: {ex}")

# 新たな関数: available_coins の設定および支払額選択
def select_payment(order_sum: int, available: dict) -> int:
    """
    available: {コイン額面: 個数, ...}
    order_sum 以上の支払額で、可能な組み合わせの中から最小額を返す。
    DP により、利用可能な金額の組み合わせを評価する。
    """
    total_available = sum(denom * count for denom, count in available.items())
    max_sum = total_available
    dp = [False] * (max_sum + 1)
    dp[0] = True

    # 各額面ごとに個数分ループ
    for denom in sorted(available.keys(), reverse=True):
        quantity = available[denom]
        for _ in range(quantity):
            for s in range(max_sum, denom - 1, -1):
                if dp[s - denom]:
                    dp[s] = True

    for s in range(order_sum, max_sum + 1):
        if dp[s]:
            return s
    return order_sum

def simulate_payment(order_sum: int):
    """
    お客さんが持っている小銭・札をランダムに設定（各額面の個数は 0～3 の乱数）。
    合計金額が order_sum よりも大きくなるよう調整し、その中から
    お釣り（支払額 - order_sum）が最小になる支払い額を返す。
    """
    denominations = [10000, 5000, 1000, 500, 100, 50, 10, 5, 1]
    available = {}
    for d in denominations:
        available[d] = random.randint(0, 4)
    total_available = sum(d * cnt for d, cnt in available.items())
    # 合計が order_sum 以下の場合は、最低額 1円硬貨で足す
    while total_available <= order_sum:
        available[1] += 1
        total_available = sum(d * cnt for d, cnt in available.items())
    payment = select_payment(order_sum, available)
    return payment, available

# --------------------
# ホーム画面
def home_view(page: ft.Page):
    page.views.clear()
    
    background = ft.Image(
        src="assets/images/cash.jpg",
        width=page.window_width,
        height=page.window_height,
        fit=ft.ImageFit.COVER
    )
    
    content = ft.Column(
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("レジ打ちゲーム", size=40, weight="bold", color=ft.Colors.WHITE),
            ft.ElevatedButton("ゲームスタート", on_click=lambda e: main_game(page)),
            ft.ElevatedButton("ランキング", on_click=lambda e: ranking_view(page))
        ]
    )
    
    home = ft.View(
        route="/home",
        controls=[
            ft.Stack(
                controls=[
                    background,
                    ft.Container(
                        width=page.window_width,
                        height=page.window_height,
                        content=content
                    )
                ]
            )
        ]
    )
    page.views.append(home)
    page.go(home.route)

# --------------------
# ランキング画面
def ranking_view(page: ft.Page):
    play_sound("click2.mp3")
    conn = sqlite3.connect("flet_app.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ranking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    cursor.execute("SELECT  score, timestamp FROM ranking ORDER BY score DESC")
    rows = cursor.fetchall()
    conn.close()

    ranking_controls = []
    for r in rows:
        ranking_controls.append(ft.Text(f" {r[0]}点 ({r[1]})"))
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
# ゲーム画面（既存UI・処理そのまま）
def main_game(page: ft.Page):
    play_sound("click2.mp3")
    page.title = "レジ打ちゲーム"
    page.vertical_alignment = "start"
    page.views.clear()

    lives = 3
    customer_order = fetch_random_orders()
    order_sum = sum(item['price'] * item['qty'] for item in customer_order)
    simulated_payment, available_coins = simulate_payment(order_sum)
    print(f"注文合計: {order_sum}円, お客さん所持: {available_coins}, 支払い: {simulated_payment}円")
    processed_orders = []
    operator_total = 0
    numeric_input = 0

    # ------------------------------
    # 追加：ライフ表示用コンテナ
    life_container = ft.Container()

    def update_life_icons():
        icons = []
        max_lives = 3
        for i in range(max_lives):
            # global_lives で残ライフを判定（i番目が生きていれば life.png、そうでなければ lifeout.png）
            icon_src = "assets/images/life.png" if i < global_lives else "assets/images/lifeout.png"
            icons.append(ft.Image(src=icon_src, width=60, height=60))
        life_container.content = ft.Row(controls=icons)
    update_life_icons()
    # ------------------------------

    answered = False  # この問題で既に回答済みかチェックするフラグ
    countdown_remaining = 60  # 60秒カウントダウン
    timer_widget = ft.Text(value=f"{countdown_remaining}秒", size=35)  # color will be set in update_countdown
    
    # 上部GIFとタイマー表示用（timer_widget を kutiobake.gif の下に配置）
    top_gif = ft.Image(
        src="assets/gifs/kutiobake.gif",
        width=300,
        height=350,
        fit="contain"
    )
    top_stack = ft.Stack(
        controls=[
            ft.Container(
                alignment=ft.Alignment(-0.4, -0.4),
                content=top_gif
            ),
            ft.Container(
                alignment=ft.Alignment(-0.3, 1.0),  # 下部に配置
                content=timer_widget
            )
        ],
        height=400
    )
    
    # タイマー更新用の再帰関数
    def update_countdown():
        nonlocal countdown_remaining, answered
        if answered:
            return

        if countdown_remaining > 0:
            countdown_remaining -= 1
            timer_widget.value = f"{countdown_remaining}秒"
            # 残りが10秒未満なら赤色、それ以外は黒色で表示
            timer_widget.color = "red" if countdown_remaining < 11 else "black"
            page.update()
            threading.Timer(1, update_countdown).start()
        else:
            # タイムアウト時の処理（既存の内容）＋追加処理
            if not answered:
                answered = True
                calc_button.disabled = True
                global global_lives
                global_lives -= 1
                update_life_icons()
                change_display.value = f"時間切れ！ 残りライフ: {global_lives}"
                
                top_stack.controls = [
                    ft.Container(
                        alignment=ft.Alignment(-0.4, -0.4),
                        content=ft.Image(
                            src="assets/gifs/oikari2.gif",
                            width=450,
                            height=350,
                            fit="contain"
                        )
                    ),
                    ft.Container(
                        alignment=ft.Alignment(0, -0.4),
                        content=ft.Image(
                            src="assets/gifs/killyou.gif",
                            width=359,
                            height=350,
                            fit="contain"
                        )
                    )
                ]
                page.update()
                
                # killyou.gif 表示後1秒で punch.mp3 と grass.mp3 を再生し、
                # その直後に画面全体で punch.gif を表示する処理
                def show_punch():
                    top_stack.controls = [
                        ft.Container(
                            expand=True,
                            alignment=ft.alignment.center,
                            content=ft.Image(
                                src="assets/gifs/punch.gif",
                                width=page.window_width,
                                height=page.window_height,
                                fit="contain"
                            )
                        )
                    ]
                    page.update()
                    if global_lives <= 0:
                        threading.Timer(2, game_over).start()
                    else:
                        threading.Timer(2, lambda: main_game(page)).start()
                
                def play_sounds_and_show_punch():
                    play_sound("punch.mp3")
                    play_sound("grass.mp3")
                    show_punch()
                
                threading.Timer(1, play_sounds_and_show_punch).start()
    
    # スタート時にカウントダウン開始
    update_countdown()

    # processed_orders 表示用のカラム（白背景）
    order_list = ft.Column(controls=[])
    order_list_container = ft.Container(
        bgcolor="white",
        padding=10,
        content=order_list
    )
    total_display = ft.Text("商品合計: 0円", size=16)
    numeric_display = ft.Text("", size=24)
    change_display = ft.Text("お釣り: ", size=16, color="green")

    # --- order_info 部分の変更 ---
    # order_payment_info コンテナを定義（初期は非表示）
    order_payment_info = ft.Container(
        content=ft.Column(
            controls=[
                #ft.Text(f"注文合計金額　　　　　{order_sum}円", size=16),
                ft.Text(f"支払い金額　　　{simulated_payment}円", size=16, color="red")
            ]
        ),
        visible=False
    )

    order_info_content = ft.Column(
        controls=[
            ft.Text("客側の注文内容", size=20, weight="bold", color="blue"),
            ft.Divider(height=10),
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Image(src=os.path.join("assets", "images", item["image"]).replace("\\", "/"), width=50, height=50, fit="contain"),
                            ft.Text(f"{item['name']}  {item['price']}円", size=16),
                            ft.Text(f"数量: {item['qty']}")
                        ],
                        spacing=10
                    )
                    for item in customer_order
                ],
                spacing=5
            ),
            ft.Divider(height=20),
            # 支払情報はここに配置
            order_payment_info,
            ft.Divider(height=20),
            ft.Text("注文パネル", size=18, weight="bold"),
            ft.Row(
                controls=[
                    ft.ElevatedButton("FF1", on_click=lambda e: show_category_view("FF1")),
                    ft.ElevatedButton("なまもの", on_click=lambda e: show_category_view("なまもの")),
                    ft.ElevatedButton("コロッケ", on_click=lambda e: show_category_view("コロッケ類")),
                    ft.ElevatedButton("常温", on_click=lambda e: show_category_view("常温")),
                    ft.ElevatedButton("中華まん", on_click=lambda e: show_category_view("中華まん")),
                    ft.ElevatedButton("サラダ", on_click=lambda e: show_category_view("サラダ")),
                    ft.ElevatedButton("おにぎり", on_click=lambda e: show_category_view("おにぎり")),
                    ft.ElevatedButton("飲み物", on_click=lambda e: show_category_view("飲み物"))
                ],
                spacing=10
            )
        ]
    )
    order_info = ft.Container(
        bgcolor="white",
        padding=10,
        content=order_info_content
    )

    def update_quantity(index, new_value):
        if new_value < 1:
            new_value = 1
        processed_orders[index]["qty"] = new_value
        update_right_panel()

    # --- update_right_panel 関数内の変更 ---
    def update_right_panel():
        nonlocal operator_total
        order_list.controls.clear()
        operator_total = 0
        for i, item in enumerate(processed_orders):
            total_item = item["price"] * item["qty"]
            operator_total += total_item
            # 既存の処理（各行の生成）
            raw_path = os.path.join("assets", "images", item["image"])
            image_path = raw_path.replace("\\", "/")
            order_list.controls.append(
                ft.Row(
                    controls=[
                        ft.Image(src=image_path, width=40, height=40, fit="contain"),
                        ft.Text(item["name"]),
                        ft.Text(f"{item['price']}円"),
                        ft.IconButton(icon=ft.Icons.REMOVE, on_click=lambda e, i=i: update_quantity(i, processed_orders[i]["qty"] - 1)),
                        ft.Text(f"{item['qty']}"),
                        ft.IconButton(icon=ft.Icons.ADD, on_click=lambda e, i=i: update_quantity(i, processed_orders[i]["qty"] + 1)),
                        ft.Text(f"計: {total_item}円"),
                        ft.IconButton(icon=ft.Icons.DELETE, on_click=lambda e, i=i: delete_order(i))
                    ],
                    spacing=10
                )
            )
        total_display.value = f"商品合計: {operator_total}円"
        # 支払情報の表示を、注文内容が一致したときだけ行う
        order_payment_info.visible = is_orders_matching(customer_order, processed_orders)
        page.update()

    def delete_order(index):
        del processed_orders[index]
        update_right_panel()

    def add_order(e, order):
        nonlocal operator_total
        for proc in processed_orders:
            if proc["name"] == order["name"]:
                proc["qty"] += 1
                break
        else:
            new_order = order.copy()
            new_order["qty"] = 1
            processed_orders.append(new_order)
        play_sound("click.mp3")
        update_right_panel()

    # show_category_view を新たな View として実装
    def show_category_view(category: str):
        play_sound("click3.mp3")
        conn = sqlite3.connect("flet_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, image FROM line_list WHERE genre = ?", (category,))
        items = [{"name": row[0], "price": row[1], "image": row[2]} for row in cursor.fetchall()]
        conn.close()

        controls = []
        if items:
            for item in items:
                # 画像はプロジェクト内の assets/images フォルダに配置
                image_path = os.path.join("assets", "images", item["image"])
                controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Image(src=image_path, width=80, height=80, fit="contain"),
                                ft.Text(item["name"], size=14, weight="bold"),
                                ft.Text(f"{item['price']}円", size=12),
                                ft.IconButton(
                                    icon=ft.Icons.ADD,
                                    on_click=lambda e, order=item: (add_order(e, order), page.views.pop(), page.go("/"))
                                )
                            ],
                            alignment="center"
                        ),
                        width=120,
                        padding=5,
                        margin=5,
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=5,
                        border=ft.border.all(1, ft.Colors.GREY_300)
                    )
                )
        else:
            controls.append(ft.Text("該当する商品はありません。"))

        category_view = ft.View(
            route="/" + category,
            controls=[
                ft.AppBar(
                    title=ft.Text(f"{category} 一覧"),
                    bgcolor=ft.Colors.GREY_200,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: (page.views.pop(), page.go("/"))
                    )
                ),
                ft.Container(
                    content=ft.GridView(
                        expand=True,
                        runs_count=4,
                        spacing=10,
                        run_spacing=10,
                        controls=controls
                    ),
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10
                )
            ],
            horizontal_alignment="center",
            vertical_alignment="start"
        )
        page.views.append(category_view)
        page.go(category_view.route)

    # ----- 修正: coin_stack の定義（背景色なし、サイズ固定も指定しない） -----
    coin_stack_controls = []  # コインの画像を格納するリスト
    coin_stack = ft.Container(
        alignment=ft.alignment.top_right
    )
    # ----- 追加: お客が怒ったかを判定するフラグ(初期はFalse) -----
    customer_angry_triggered = False

    # ----- 修正: 右上に積むコイン画像用の更新関数 -----
    def update_coin_stack():
        # 追加順の反転せず、追加された順番そのままで下から上に積む（最初のコインが一番下）
        coin_stack.content = ft.Column(
            controls=coin_stack_controls,
            spacing=-65,  # オフセットはお好みで調整
            alignment=ft.MainAxisAlignment.END
        )
        page.update()

    # コイン画像タップ時の処理
    def coin_click(e, coin):
        nonlocal numeric_input, customer_angry_triggered
        global global_lives
        numeric_input += coin["value"]
        numeric_display.value = f"{numeric_input} 円"
        coin_stack_controls.append(
            ft.Image(
                src=os.path.join("assets", "coins", f"{coin['value']}yentumu.png").replace("\\", "/"),
                width=80,
                height=80,
                fit="contain"
            )
        )
        update_coin_stack()
        play_sound("coin.mp3")
        
        # お釣りが23枚を超え、まだ怒り処理が未実行の場合
        if not customer_angry_triggered and len(coin_stack_controls) > 23:
            customer_angry_triggered = True
            global_lives -= 1
            update_life_icons()
            
            # angry 状態のGIF（oikari2.gif と killyou.gif）を表示
            top_stack.controls = [
                ft.Container(
                    alignment=ft.Alignment(-0.4, -0.4),
                    content=ft.Image(
                        src="assets/gifs/oikari2.gif",
                        width=450,
                        height=350,
                        fit="contain"
                    )
                ),
                ft.Container(
                    alignment=ft.Alignment(0, -0.4),
                    content=ft.Image(
                        src="assets/gifs/killyou.gif",
                        width=359,
                        height=350,
                        fit="contain"
                    )
                )
            ]
            page.update()
            
            # 1秒後に punch.mp3 と grass.mp3 を再生し、その直後に画面全体で punch.gif を表示
            def show_punch():
                top_stack.controls = [
                    ft.Container(
                        expand=True,
                        alignment=ft.alignment.center,
                        content=ft.Image(
                            src="assets/gifs/punch.gif",
                            width=page.window_width,
                            height=page.window_height,
                            fit="contain"
                        )
                    )
                ]
                page.update()
                if global_lives <= 0:
                    threading.Timer(2, game_over).start()
                else:
                    threading.Timer(2, lambda: main_game(page)).start()
            
            def play_sounds_and_show_punch():
                play_sound("punch.mp3")
                play_sound("grass.mp3")
                show_punch()
            
            threading.Timer(1, play_sounds_and_show_punch).start()

    # 入力クリア用ボタンの処理
    def clear_coin(e):
        nonlocal numeric_input
        numeric_input = 0
        numeric_display.value = f"{numeric_input} 円"
        play_sound("click.mp3")
        page.update()

    # 釣りなしボタンの処理（numeric_input を 0 にリセット）
    def zero_change(e):
        nonlocal numeric_input
        numeric_input = 0
        numeric_display.value = "0 円"
        play_sound("click.mp3")
        page.update()

    # コイン画像ボタンの定義（assets/coins フォルダ内の画像を利用）
    coins = [
        {"value": 1, "img": "1yen.png"},
        {"value": 5, "img": "5yen.png"},
        {"value": 10, "img": "10yen.png"},
        {"value": 50, "img": "50yen.png"},
        {"value": 100, "img": "100yen.png"},
        {"value": 500, "img": "500yen.png"},
        {"value": 1000, "img": "1000yen.png"},
        {"value": 5000, "img": "5000yen.png"},
    ]

    coin_keys = ft.Column([
        ft.Row(
            controls=[
                ft.GestureDetector(
                    content=ft.Image(
                        src=os.path.join("assets", "coins", coin["img"]).replace("\\", "/"),
                        width=40,
                        height=40,
                        fit="contain"
                    ),
                    on_tap=lambda e, coin=coin: coin_click(e, coin)
                )
                for coin in coins
            ],
            wrap=True,
            spacing=5,
        ),
        ft.ElevatedButton("Clear", on_click=clear_coin, width=80),
        ft.ElevatedButton("釣りなし", on_click=zero_change, width=80)  # 釣りなしボタンを追加
    ])

    def game_over():
        global global_score, global_lives
        final_score = global_score  # 累積した global_score をそのまま最終スコアとして使用
        change_display.value = f"ゲームオーバ！ 最終スコア: {final_score} 円"
        page.update()
        record_ranking(final_score)
        # 3秒後にゲームリセットしてホーム画面へ戻る処理
        def restart():
            global global_lives, global_score
            global_lives = 3
            global_score = 0
            print("Game over. Restarting...")
            home_view(page)
            print("Game over. Restarting...")
        threading.Timer(3, restart).start()

    answered = False  # この問題で既に回答済みかチェックするフラグ

    # 会計処理（calculate_change）内：お釣りが0円の場合も正しく判定
    def calculate_change(e):
        nonlocal numeric_input, simulated_payment, order_sum, operator_total, answered
        global global_score, global_lives
        if answered:
            return  # 既に回答済みなら何もしない
        answered = True
        calc_button.disabled = True
        page.update()

        play_sound("cash.mp3")
        correct_change = simulated_payment - order_sum

        order_match = is_orders_matching(customer_order, processed_orders)
        error_occurred = False

        if not order_match:
            global_lives -= 1
            change_display.value = f"注文ミス！ 残りライフ: {global_lives}"
            error_occurred = True
            # ライフが減少したとき、上部GIFを gif2.gif に変更
            top_gif.src = "assets/gifs/oikari2.gif"
            top_gif.width = 450
            top_gif.height = 350
        elif numeric_input != correct_change:
            global_lives -= 1
            change_display.value = f"支払いミス！ 正しいお釣りは {correct_change} 円です。 残りライフ: {global_lives}"
            error_occurred = True
            # ライフが減少したとき、上部GIFを gif2.gif に変更
            top_gif.src = "assets/gifs/oikari2.gif"
            top_gif.width = 450
            top_gif.height = 350
        else:
            play_sound("correct.mp3")
            change_display.value = f"正解！ お釣り: {numeric_input} 円"
            global_score += operator_total
            page.update()
            # 正解の場合は2秒後に次の注文へ
            threading.Timer(2, lambda: main_game(page)).start()
            return

        # ライフ表示の更新
        update_life_icons()
        page.update()
        if global_lives <= 0:
            game_over()
        else:
            # 誤答だがライフが残っている場合も2秒後に次の注文へ
            threading.Timer(2, lambda: main_game(page)).start()

    calc_button = ft.ElevatedButton("会計", on_click=calculate_change)
    input_info = ft.Column(
        controls=[
            ft.Text("入力内容", size=20, weight="bold", color="blue"),
            ft.Divider(height=10),
            order_list_container,
            total_display,
            ft.Divider(height=20),
            numeric_display,  # 現在の合計金額を表示
            coin_keys,       # コイン画像ボタン
            calc_button,
            change_display
        ]
    )
    # 入力情報部分も白背景でラップする
    input_info_container = ft.Container(
        bgcolor="white",
        padding=10,
        content=input_info
    )

    # 画面全体の背景を茶色にするため、下部領域を包むコンテナは bgcolor="brown"
    main_content = ft.Container(
        bgcolor="brown",
        padding=10,
        content=ft.Row(
            controls=[
                ft.Container(content=order_info, expand=True, padding=10),
                ft.VerticalDivider(width=1),
                ft.Container(content=input_info_container, expand=True, padding=10)
            ]
        )
    )

    # 全体を下寄せにするため、Column で包みます
    main_view = ft.View(
        route="/",
        controls=[
            ft.Stack(
                controls=[
                    # 下部の主要コンテンツ（Column）の配置
                    ft.Column(
                        expand=True,
                        alignment=ft.MainAxisAlignment.END,  # 下寄せ
                        controls=[
                            ft.Container(
                                expand=True,
                                alignment=ft.Alignment(-0.4, -0.4),
                                content=top_stack,
                                bgcolor=ft.Colors.ORANGE_100
                            ),
                            main_content
                        ]
                    ),
                    # ライフ表示（左上）
                    ft.Container(
                        alignment=ft.alignment.top_left,
                        content=life_container,
                        bgcolor=ft.Colors.ORANGE_100  # 必要に応じて
                    ),
                    # 右上に追加：コイン積み上げ用専用パネル（背景なし）
                    coin_stack
                ]
            )
        ]
    )
    page.views.append(main_view)
    page.go("/")

# --------------------
# エントリーポイント（起動時はホーム画面を表示）
def main(page: ft.Page):
    # ウィンドウサイズを固定設定　デスクトップアプリとして起動した場合のみに適応される。
    #
    page.window_width = 1920
    page.window_height = 1080
    page.window_resizable = False
    page.window_min_width = 1920
    page.window_min_height = 1080
    page.window_max_width = 1920
    page.window_max_height = 1080

    home_view(page)
    page.bgcolor = ft.Colors.ORANGE_100
ft.app(target=main, assets_dir="assets")
