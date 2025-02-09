import math
import random

def calculate_payment(bill_amount: int, error_rate: float = 0.3, max_payment: int = None) -> int:
    """
    bill_amount に対して、実際の支払い額をシミュレートする。
    error_rate の確率で bill_amount ピッタリの支払いを除外し、候補の中から選択する。
    max_payment が指定されている場合、支払い額は max_payment 以下に限定する。
    """
    candidates = set()
    # (1) ピッタリ支払う
    candidates.add(bill_amount)
    
    # (2) 10円単位の丸め (上・下)
    if bill_amount % 10 != 0:
        candidates.add(((bill_amount + 9) // 10) * 10)
        candidates.add((bill_amount // 10) * 10)
    
    # (3) 5円単位の調整 (±5円)
    if bill_amount % 5 != 0:
        candidates.add(bill_amount + (5 - bill_amount % 5))
        candidates.add(bill_amount - (bill_amount % 5))
    
    # (4) 100円単位の丸め (上・下)
    if bill_amount % 100 != 0:
        candidates.add(((bill_amount + 99) // 100) * 100)
        candidates.add((bill_amount // 100) * 100)
    
    # (5) 大きな紙幣の候補
    if bill_amount < 1000:
        candidates.add(1000)
    if bill_amount < 10000:
        candidates.add(10000)
    
    # (6) わずかな加算の候補
    candidates.add(bill_amount + 5)
    candidates.add(bill_amount + 10)
    candidates.add(bill_amount + 100)
    
    # 支払額は bill_amount 以上であること
    valid_candidates = [amt for amt in candidates if amt >= bill_amount]
    
    # max_payment が指定されている場合、支払額は max_payment 以下に限定
    if max_payment is not None:
        valid_candidates = [amt for amt in valid_candidates if amt <= max_payment]
        if not valid_candidates:
            valid_candidates = [bill_amount]
    
    # 一定の確率 error_rate でピッタリ支払いを除外する
    if bill_amount in valid_candidates and random.random() < error_rate:
        valid_candidates = [amt for amt in valid_candidates if amt != bill_amount]
        if not valid_candidates:
            valid_candidates = [bill_amount]
    
    # お釣りとなる硬貨・紙幣の枚数を求めるヘルパー関数
    def coin_count(amount: int) -> int:
        denominations = [10000, 5000, 1000, 500, 100, 50, 10, 5, 1]
        count = 0
        remaining = amount
        for d in denominations:
            count += remaining // d
            remaining %= d
        return count
    
    # 候補のスコアは (支払額 - bill_amount) のお釣り枚数で評価
    def score(amount: int) -> int:
        change = amount - bill_amount
        return coin_count(change)
    
    # コイン枚数(score)と余分な金額の小さい順にソートする
    valid_candidates.sort(key=lambda x: (score(x), x - bill_amount))
    best_score = score(valid_candidates[0])
    best_candidates = [amt for amt in valid_candidates if score(amt) == best_score]
    
    chosen = random.choice(best_candidates)
    return chosen

# テスト用のメインコード
if __name__ == "__main__":
    bill = 862
    customer_total = bill + 200
    payment = calculate_payment(bill, error_rate=0.3, max_payment=customer_total)
    print(f"Bill: {bill}, Chosen Payment: {payment}")