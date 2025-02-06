import flet as ft

def main(page: ft.Page):
    page.title = "レジ打ちゲーム"
    page.padding = 10

    # 左側: 注文情報セクション
    left_column = ft.Column(
        controls=[
            ft.Text("注文内容", size=20, weight="bold", color="blue"),
            ft.Divider(height=10),
            ft.Column([
                ft.Text("からあげクン    248円"),
                ft.Text("コロッケ       108円"),
                ft.Text("サラダ         522円"),
            ], spacing=5),
            ft.Divider(height=20),
            ft.Text("合計金額       878円", size=16),
            ft.Text("お支払い金額  1000円", size=16),
        ],
    )

    # 右側: 入力情報セクション
    right_column = ft.Column(
        controls=[
            ft.Text("入力内容", size=20, weight="bold", color="blue"),
            ft.Divider(height=10),
            ft.Text("からあげクン", size=16),
            ft.Text("お釣り: 122円", size=16, color="green"),
            ft.Divider(height=20),
            # 数字キー
            ft.GridView(
                controls=[
                    ft.ElevatedButton(str(i)) for i in range(1, 10)
                ] + [
                    ft.ElevatedButton("0"),
                    ft.ElevatedButton("."),
                    ft.ElevatedButton("×"),
                ],
                runs_count=3,
                max_extent=80,
                spacing=5,
                run_spacing=5,
            ),
            ft.Divider(height=20),
            # ボタン
            ft.Row([
                ft.Image(src="bag_icon.png", width=40, height=40),
                ft.Image(src="fly_icon.png", width=40, height=40),
                ft.ElevatedButton("会計", bgcolor="orange", color="white", width=120),
            ]),
        ],
    )

    # ページレイアウト
    page.add(
        ft.Row(
            controls=[
                ft.Container(content=left_column, width=400, border=ft.border.all(1)),
                ft.VerticalDivider(width=10),
                ft.Container(content=right_column, width=300, border=ft.border.all(1)),
            ]
        )
    )

ft.app(target=main)
