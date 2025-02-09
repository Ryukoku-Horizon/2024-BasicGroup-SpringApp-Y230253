import os
import flet as ft

def main(page: ft.Page):
    # カレントディレクトリを表示
    print("DEBUG: Current working directory:", os.getcwd())
    # 画像ファイルの存在チェック
    image_path = os.path.join("assets", "images", "karaage_main.png")
    if os.path.exists(image_path):
        print("DEBUG: 画像ファイルは存在します:", image_path)
    else:
        print("DEBUG: 画像ファイルが見つかりません:", image_path)
    page.add(ft.Image(src="assets/images/karaage_main.png", width=200, height=200, fit="contain"))

ft.app(target=main, assets_dir="assets")