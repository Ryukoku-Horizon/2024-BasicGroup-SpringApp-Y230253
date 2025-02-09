import csv
import sqlite3

def import_csv_to_db(csv_path="line_list.csv", db_path="flet_app.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open(csv_path, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # CSVの各カラムは "name", "price", "genre", "image" であることを前提とする
            cursor.execute("""
            INSERT INTO line_list (name, price, genre, image)
            VALUES (?, ?, ?, ?)
            """, (row['name'], int(row['price']), row['genre'], row['image']))
    conn.commit()
    conn.close()
    print("CSVからDBへのインポートが完了しました。")
    
if __name__ == "__main__":
    import_csv_to_db()