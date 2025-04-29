from flask import Flask, render_template, request, jsonify, session # session をインポート
import json
import random
import os
from gemini import initialize_gemini, generate_interpretation # gemini.pyから関数をインポート
import secrets # secret_key生成用
import markdown # markdownライブラリをインポート

app = Flask(__name__)
# --- セッションのための Secret Key 設定 ---
# 環境変数から読み込むか、なければランダムな値を生成（本番環境では固定の安全なキーを設定推奨）
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))

# --- Gemini 初期化 ---
if not initialize_gemini():
    print("警告: Geminiの初期化に失敗しました。解釈機能は利用できません。")
    # 必要に応じて、ここでアプリケーションを終了させるか、警告を表示するなどの処理を追加

# --- カードデータの読み込み ---
def load_card_data(filepath):
    # スクリプトのディレクトリからの相対パスでファイルを開く
    script_dir = os.path.dirname(__file__)
    abs_file_path = os.path.join(script_dir, filepath)
    try:
        with open(abs_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {abs_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"エラー: JSONファイルの解析に失敗しました - {abs_file_path}")
        return None

all_cards_data = load_card_data('cards_meaning/all_cards.json')

@app.route('/')
def index():
    if all_cards_data is None:
        return "カードデータの読み込みに失敗しました。", 500
    return render_template('index.html')

# カードを1枚引くAPIエンドポイント (セッション管理)
@app.route('/draw_card', methods=['POST'])
def draw_card():
    if all_cards_data is None:
        return jsonify({"error": "カードデータが読み込まれていません。"}), 500

    # セッションから引いたカードのリストを取得、なければ初期化
    drawn_cards = session.get('drawn_cards', [])

    # カード枚数の上限を5枚に変更
    if len(drawn_cards) >= 5:
        return jsonify({"error": "すでに5枚のカードを引いています。", "drawn_cards": drawn_cards, "card_count": len(drawn_cards)}), 400

    # 新しいカードを引く
    card_info = random.choice(all_cards_data)
    card_name = card_info.get("name", "名前不明")
    orientation = random.choice(["正位置", "逆位置"])
    if orientation == "正位置":
        meaning = card_info.get("meaning_up", "意味が見つかりません")
    else:
        meaning = card_info.get("meaning_rev", "意味が見つかりません")

    new_card = {
        "card_name": card_name,
        "orientation": orientation,
        "meaning": meaning
    }

    # 引いたカードをセッションに追加
    drawn_cards.append(new_card)
    session['drawn_cards'] = drawn_cards # セッションを更新

    return jsonify({
        "new_card": new_card,
        "drawn_cards": drawn_cards,
        "card_count": len(drawn_cards)
    })

# 占いをリセットするAPIエンドポイント
@app.route('/reset', methods=['POST'])
def reset_session():
    session.pop('drawn_cards', None) # セッションからカード情報を削除
    return jsonify({"message": "占いをリセットしました。"})


# LLMによる解釈を生成するAPIエンドポイント (個別カード解釈と最終解釈に対応)
@app.route('/interpret', methods=['POST'])
def interpret_cards():
    drawn_cards = session.get('drawn_cards', [])
    if not drawn_cards:
        return jsonify({"error": "カードがまだ引かれていません。"}), 400

    data = request.get_json()
    user_question = data.get('question', '特に質問はありません。')
    interpretation_type = data.get('type', 'final') # 'single', 'feedback', 'final'
    card_index = data.get('card_index', -1) # 'single', 'feedback' で使用
    user_feedback = data.get('feedback', '') # ★キー名を 'user_feedback' から 'feedback' に変更
    # 'feedback' と 'final' で使用する対話履歴 (各カードごとのターンの配列)
    card_interactions = data.get('card_interactions', [])

    # ギリシャ十字のポジション定義
    positions = [
        "1. 現在の状況、状態", "2. 障害、原因", "3. 現状維持で予想される傾向",
        "4. 問題解決のための対策", "5. 最終結果"
    ]

    prompt = ""
    if interpretation_type == 'single' and 0 <= card_index < len(drawn_cards):
        # --- 個別カード解釈用プロンプト (変更なし) ---
        target_card = drawn_cards[card_index]
        position_name = positions[card_index] if card_index < len(positions) else f"{card_index+1}枚目"
        prompt_context = ""
        if card_index > 0:
            prompt_context += "これまでのカード:\n"
            for i in range(card_index):
                prev_card = drawn_cards[i]
                prev_pos_name = positions[i] if i < len(positions) else f"{i+1}枚目"
                prompt_context += f"- {prev_pos_name}: {prev_card['card_name']} ({prev_card['orientation']})\n"
            prompt_context += "\n"
        prompt = f"""タロット占いの{card_index+1}枚目（{position_name}）として以下のカードが出ました。
カード: {target_card['card_name']} ({target_card['orientation']})
基本的な意味: {target_card['meaning']}

{prompt_context}相談者の質問: 「{user_question}」

このカードが{position_name}の位置に出た意味について、タロット占い師の視点から**200字以内で簡潔に**解説してください。可能であれば、これまでのカードとの関連性も少し触れてください。
応答はMarkdown形式（見出し、段落、リストなどを使用）で、自然な文章で記述してください。テーブル形式は使用しないでください。"""

    elif interpretation_type == 'feedback' and 0 <= card_index < len(drawn_cards) and user_feedback and card_interactions: # 'reaction' を 'feedback' に変更
        # --- AI反応生成用プロンプト (複数回の対話を考慮) ---
        target_card = drawn_cards[card_index]
        position_name = positions[card_index] if card_index < len(positions) else f"{card_index+1}枚目"

        # このカードに関する直近の対話履歴を構築
        interaction_log = ""
        for turn in card_interactions:
            if turn.get('interpretation'): # 最初の解釈
                interaction_log += f"あなたの最初の解釈: 「{turn['interpretation']}」\n"
            if turn.get('feedback'):
                interaction_log += f"相談者の反応: 「{turn['feedback']}」\n"
            if turn.get('reaction'):
                interaction_log += f"あなたの応答: 「{turn['reaction']}」\n"

        prompt = f"""タロット占いの{card_index+1}枚目（{position_name}: {target_card['card_name']} {target_card['orientation']}）について、相談者と以下の対話を行いました。
--- 対話履歴 ---
{interaction_log}
---
相談者の最新の反応: 「{user_feedback}」

タロット占い師として、これまでの流れと相談者の最新の反応を踏まえ、**共感や短い問いかけ、補足など、簡潔な言葉で**応答してください。**100字以内**でお願いします。
応答はMarkdown形式で、自然な文章で記述してください。"""

    elif interpretation_type == 'final' and len(drawn_cards) == 5 and card_interactions: # card_interactions は全カードの対話履歴の配列
        # --- 最終総合解釈用プロンプト (複数回の対話履歴を反映) ---
        prompt_cards_info = ""
        for i, card in enumerate(drawn_cards):
            position_name = positions[i] if i < len(positions) else f"{i+1}枚目"
            prompt_cards_info += f"{position_name}: {card['card_name']} ({card['orientation']}) - 基本的な意味: {card['meaning']}\n"

        prompt_interaction_summary = "これまでの対話の概要:\n"
        # card_interactions は [[card0_turn1, card0_turn2,...], [card1_turn1,...], ...] の形式を想定
        for i, card_history in enumerate(card_interactions):
            if not card_history: continue # 対話がないカードはスキップ
            position_name = positions[i] if i < len(positions) else f"{i+1}枚目"
            prompt_interaction_summary += f"--- {position_name} ({drawn_cards[i]['card_name']}) ---\n"
            for turn_num, turn in enumerate(card_history):
                if turn.get('interpretation'):
                    prompt_interaction_summary += f"あなたの解釈: {turn['interpretation'][:100]}...\n"
                if turn.get('feedback'):
                    prompt_interaction_summary += f"相談者の反応 {turn_num+1}: {turn['feedback']}\n"
                if turn.get('reaction'):
                    prompt_interaction_summary += f"あなたの応答 {turn_num+1}: {turn['reaction']}\n"
            prompt_interaction_summary += "\n"


        prompt = f"""以下の5枚のタロットカードがギリシャ十字スプレッドで出ました。

{prompt_cards_info}
相談者の質問: 「{user_question}」

{prompt_interaction_summary}
上記のカード、質問、そして**各カードに関する相談者との複数回にわたる対話全体を踏まえ**、タロット占い師の視点から**総合的な解釈と最終的なアドバイス**を生成してください。
応答はMarkdown形式で、以下のような形式で記述してください:
- 全体の概要
- 各カードと対話から読み取れることのまとめ（対話の流れも考慮）
- カード間の関連性と対話の流れについての考察
- 最終的なアドバイス

**注意:** 結果をMarkdownのテーブル形式 (`| ... | ... |`) で表示しないでください。自然な文章で記述してください。"""
    else:
        # 不正なリクエスト
        return jsonify({"error": "解釈に必要な情報が不足しているか、不正なリクエストです。"}), 400

    # --- Geminiから解釈/反応を取得 ---
    interpretation_markdown = generate_interpretation(prompt)

    # --- MarkdownをHTMLに変換 ---
    try:
        interpretation_html = markdown.markdown(interpretation_markdown, extensions=['fenced_code', 'nl2br'])
    except Exception as e:
        print(f"MarkdownのHTML変換中にエラー: {e}")
        interpretation_html = f"<p>解釈の表示中にエラーが発生しました。</p><pre>{interpretation_markdown}</pre>"

    # --- レスポンスを返す (キー名をタイプによって変更) ---
    if interpretation_type == 'feedback':
        return jsonify({"reaction_html": interpretation_html}) # フィードバックの場合は reaction_html
    else:
        return jsonify({"interpretation_html": interpretation_html}) # それ以外は interpretation_html


if __name__ == '__main__':
    # 仮想環境のPythonインタープリタで実行されるようにする
    # 通常、`flask run` コマンドを使用するか、
    # 実行時に `env\Scripts\python app.py` のように指定します。
    # ここでの app.run() は開発用サーバーの起動です。
    app.run(debug=True)