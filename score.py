import sqlite3
import time

DB_PATH = "flet_app.db"

def initialize_scores_db(db_path: str = DB_PATH):
    """
    スコア記録用テーブルが存在しなければ作成する
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()
'''
def initialize_ranking_db(db_path: str = DB_PATH):
    """
    既存の ranking テーブルがある場合は削除して再作成する（※運用環境では注意）
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # 既存の ranking テーブルを削除（これにより timestamp カラムも再作成される）
    c.execute("DROP TABLE IF EXISTS ranking")
    c.execute("""
        CREATE TABLE IF NOT EXISTS ranking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()
'''
def calculate_score(correct: bool, time_taken: float, base_score: int = 100) -> int:
    """
    正解なら、回答時間に応じたスコア (例: base_score から時間のペナルティを引く)
    正解でない場合は 0 を返す
    """
    if not correct:
        return 0
    # 例として、回答時間が長いほどスコアは低くなる
    penalty = int(time_taken)
    score = max(10, base_score - penalty)
    return score

def record_score(score: int, db_path: str = DB_PATH):
    """
    スコアと現在時刻を DB に記録する
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    c.execute("INSERT INTO scores (score, timestamp) VALUES (?, ?)", (score, timestamp))
    conn.commit()
    conn.close()

def record_ranking(score: int, db_path: str = DB_PATH):
    """
    ゲーム終了時の最終スコアをランキングテーブルに記録する
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    c.execute("INSERT INTO ranking (score, timestamp) VALUES (?, ?)", (score, timestamp))
    conn.commit()
    conn.close()

def get_rankings(limit: int = 10, db_path: str = DB_PATH):
    """
    ランキング上位のエントリを取得する
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT score, timestamp FROM ranking ORDER BY score DESC LIMIT ?", (limit,))
    rankings = c.fetchall()
    conn.close()
    return rankings