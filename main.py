import google.generativeai as genai
import os
import random
import json
import traceback

with open("cards_meaning/big_cards.json", mode = "r", encoding="utf-8") as f:
    cards_meaning = json.load(f)

def get_api_key():
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY is None:
        print("エラー: 環境変数 'GOOGLE_API_KEY' が設定されていません。")
        print("システムに環境変数を設定するか、コード内で直接APIキーを指定してください。")
        exit()

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"APIキーの設定でエラーが発生しました: {e}")
        exit()

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        print(f"モデルの初期化中にエラーが発生しました: {e}")
        exit()

    return model

def select_card(cards, num):
    place = ["meaning_up", "meaning_rev"]
    card = []
    for i in range(num):
        card += [[random.choice(place), random.choice(cards)]]
        cards.remove(card[i][1])
    return card

def meaning(mean):
    """タロットカードの意味を取得する"""
    meaning = {
        "meaning_up": "正位置",
        "meaning_rev": "逆位置"
    }
    return meaning[mean]

def create_prompt(question=None):
    """Gemini APIに送るプロンプトを作成する"""
    five_counts = ["現在の状況、状態", "障害、原因", "現状維持で予想される傾向", "問題解決のための対策", "最終結果"]
    prompt = "あなたは経験豊富なタロット占い師です。\n以下のタロットカードの結果に基づいて、相談内容について占ってください。\n\n"
    selects = select_card(cards_meaning, len(five_counts))

    if question:
        prompt += f"相談内容: {question}\n\n"
    else:
        prompt += "相談内容: (指定なし。全体的な運勢やアドバイス)\n\n"

    prompt += "--- 出たカード ---\n"

    for i in range(len(five_counts)):
        card_position = selects[i][0]
        card_details = selects[i][1]
        prompt += f"『{five_counts[i]}』を示す位置には{card_position}の『{card_details['name']}』。意味は{card_details[card_position]}\n"
    
    prompt += "-----------------\n\n"

    prompt += "上記のカードの配置とそれぞれの意味（正位置・逆位置を含む）を考慮し、具体的で洞察に満ちた、優しい言葉でアドバイスをお願いします。単にカードの意味を並べるだけでなく、カード同士の関連性も読み解き、相談者が前向きになれるような解釈をしてください。"
    return prompt

if __name__ == "__main__":
    model = get_api_key() # APIキーの取得とモデルの初期化
    if model: # モデルの初期化が成功した場合のみ実行
        print("タロット占いを開始します。")

        # 相談内容の入力
        question = input("占いたい内容を入力してください (例: 恋愛運、仕事運、全体運など。入力なしでEnterも可): ")
        if not question.strip(): # 入力が空かスペースのみの場合
            question = None # Noneを設定して「指定なし」とする

        print("カードを選び、プロンプトを作成しています...")
        # プロンプト作成
        prompt_text = create_prompt(question)

        if prompt_text:
            # ★★★ デバッグ用プリントを追加 ★★★
            print("\n--- generate_contentに渡すプロンプトの型と内容 (確認用) ---")
            print(f"Type: {type(prompt_text)}")
            print("--- Prompt Content ---")
            print(prompt_text)
            print("----------------------")
            print("-------------------------------------------------------------")

            print("Geminiに応答を生成してもらっています...")
            try:
                # Gemini API呼び出し
                response = model.generate_content(prompt_text)
                print("\n--- Geminiからの占い結果 ---")
                print(response.text)
                print("--------------------------")
            except Exception as e:
                # ★★★ traceback を出力するように修正 ★★★
                print(f"\n!!! Geminiからの応答生成中にエラーが発生しました: {e} !!!")
                print("--- トレースバック情報 ---")
                traceback.print_exc() # ★ 詳細なエラー箇所を出力
                print("------------------------")
        else:
            # create_promptがNoneを返した場合 (例: カード選択失敗時)
            print("プロンプトの作成に失敗しました。カードの枚数などを確認してください。")

    else:
        print("モデルの初期化に失敗したため、プログラムを終了します。")
