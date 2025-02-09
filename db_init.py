import sqlite3

def init_db(db_path="flet_app.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS line_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        genre TEXT NOT NULL CHECK (genre IN ('コロッケ類', 'FF1', 'なまもの', '常温', '中華まん', 'サラダ','おにぎり','飲み物')),
        image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()
    print("DB setup completed.")

def save_ranking(score,player="anonymous",db_path="flet_app.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
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
                   

if __name__ == "__main__":
    init_db()