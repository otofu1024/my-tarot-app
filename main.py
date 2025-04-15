import google.generativeai as genai
import os
import random
import json
import traceback

# タロットカードの情報を読み込み
with open("cards_meaning/all_cards.json", mode="r", encoding="utf-8") as f:
    cards_meaning = json.load(f)

def setup_gemini_model():
    """APIキーを取得し、Geminiモデルを初期化する"""
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        print("エラー: 環境変数 'GOOGLE_API_KEY' が設定されていません。")
        return None

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        return genai.GenerativeModel("gemini-1.5-pro")
    except Exception as e:
        print(f"Gemini APIの初期化でエラー: {e}")
        return None

def select_card(cards, num):
    """指定された枚数のカードをランダムに選択する"""
    cards_copy = cards.copy()  # 元のリストを変更しないようにコピー
    positions = ["meaning_up", "meaning_rev"]
    selected_cards = []
    
    for _ in range(min(num, len(cards_copy))):
        card_details = random.choice(cards_copy)
        position = random.choice(positions)
        selected_cards.append([position, card_details])
        cards_copy.remove(card_details)
    
    return selected_cards

def create_interactive_tarot(model, question):
    """対話形式のタロット占いを行う"""
    positions = ["現在の状況、状態", "障害、原因", "現状維持で予想される傾向", "問題解決のための対策", "最終結果"]
    

    print("カードを選んでいます...")
    selected_cards = select_card(cards_meaning, len(positions))
    
    print(f"\n========== タロット占い：{question if question else '全体運'} ==========\n")
    print("これからカードを1枚ずつ解説していきます。あなたの反応を伺いながら進めていきますね。\n")
    
    # カードごとの対話を保存するコンテキスト
    dialogue_context = []
    posit = {"meaning_up": "正位置",
             "meaning_rev": "逆位置"}
    
    # 各カードごとに対話形式で解釈
    for i, (card_position, card_details) in enumerate(selected_cards):
        position_name = positions[i]
        card_name = card_details['name']
        card_meaning = card_details[card_position]
        
        print(f"\n----- 「{position_name}」のカード -----")
        print(f"『{card_name}』が{posit[card_position]}で出ました。")
        print(f"このカードの意味: {card_meaning}\n")
        
        # AIによる最初の解釈
        prompt = f"""
あなたは対話形式で占いを進める経験豊富なタロット占い師です。
相談内容：{question if question else '全体的な運勢'}
現在、「{position_name}」を示す位置に{card_position}の「{card_name}」が出ています。
意味：{card_meaning}

このカードについて、相談者に問いかけるように優しく解説し、
「このカードはあなたの現状に当てはまりますか？」といった質問を投げかけてください。
回答は200字以内でお願いします。
"""

        try:
            response = model.generate_content(prompt)
            print(f"占い師: {response.text}\n")
            
            # Userがyキーを押すまでループ
            while True:
                user_response = input("あなたの反応を入力してください (終了するにはEnterだけ): ")
                if user_response.strip() == '':
                    print("次のカードに移りますね。")
                    break
                else:
                    pass
            
            
                # 対話を記録
                dialogue_context.append({
                    "position": position_name,
                    "card": card_name,
                    "position_type": card_position,
                    "meaning": card_meaning,
                    "ai_comment": response.text,
                    "user_response": user_response
                })
            
                # ユーザーの反応を踏まえたAIの解釈
                follow_up_prompt = f"""
相談者の反応：「{user_response}」

相談者の反応を踏まえて、「{position_name}」のカード「{card_name}」({card_position})についての
より個人化された解釈を提供してください。相談者の具体的な状況に寄り添った内容にしてください。
回答は200字以内でお願いします。
"""
                follow_up_response = model.generate_content(follow_up_prompt)
                print(f"\n占い師: {follow_up_response.text}")
            
                dialogue_context[-1]["ai_follow_up"] = follow_up_response.text
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            traceback.print_exc()
    
    # 全カードの解釈が終わった後に総合的な解釈を提供
    print("\n\n===== すべてのカードの解釈が終わりました =====")
    print("最終的な総合解釈を生成しています...\n")
    
    # 総合解釈用のプロンプトを作成
    final_prompt = f"相談内容：{question if question else '全体的な運勢やアドバイス'}\n\n"
    final_prompt += "この占いで出たカードと相談者との対話の内容:\n"
    
    for dialogue in dialogue_context:
        final_prompt += f"""
位置: {dialogue['position']}
カード: {dialogue['card']} ({dialogue['position_type']})
カードの意味: {dialogue['meaning']}
相談者の反応: {dialogue['user_response']}
"""
    
    final_prompt += """
上記の一連のカードと対話の内容を踏まえて、カード同士の関連性も考慮した総合的な解釈とアドバイスを提供してください。
相談者が前向きになれるような、具体的で洞察に満ちた優しいメッセージにしてください。
"""
    
    try:
        final_response = model.generate_content(final_prompt)
        print("\n----- 総合的な解釈 -----")
        print(final_response.text)
        print("-------------------------")
        return True
    except Exception as e:
        print(f"総合解釈の生成中にエラーが発生しました: {e}")
        traceback.print_exc()
        return False

def main():
    """メインプログラム"""
    # モデルの初期化
    model = setup_gemini_model()
    if not model:
        print("モデルの初期化に失敗したため、プログラムを終了します。")
        return
    
    print("=== 対話式タロット占い ===")
    print("さて、今日は何を占いましょうか？")
    
    # 相談内容の入力
    question = input("占いたい内容を入力してください (例: 恋愛運、仕事運、全体運など。入力なしでEnterも可): ")
    question = question.strip() or None
    
    # 対話式タロット占いを実行
    success = create_interactive_tarot(model, question)
    
    if not success:
        print("\n占いの過程でエラーが発生しました。もう一度お試しください。")

if __name__ == "__main__":
    main()