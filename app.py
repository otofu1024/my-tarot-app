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


# LLMによる解釈を生成するAPIエンドポイント (4枚のカードを使用)
@app.route('/interpret', methods=['POST'])
def interpret_cards(): # 関数名を複数形に変更
    # セッションから引いたカード情報を取得
    drawn_cards = session.get('drawn_cards', [])

    # 解釈依頼の条件を5枚に変更
    if len(drawn_cards) < 5:
        return jsonify({"error": "まだ5枚のカードが引かれていません。"}), 400

    data = request.get_json()
    user_question = data.get('question', 'これらのカードについて詳しく教えてください。') # 質問がない場合のデフォルト

    # ギリシャ十字のポジション定義
    positions = [
        "1. 現在の状況、状態",
        "2. 障害、原因",
        "3. 現状維持で予想される傾向",
        "4. 問題解決のための対策",
        "5. 最終結果"
    ]

    # Geminiに渡すプロンプトを作成 (5枚のカード情報とポジションを列挙)
    prompt_cards_info = ""
    for i, card in enumerate(drawn_cards):
        position_name = positions[i] if i < len(positions) else f"{i+1}枚目" # ポジション名を付与
        prompt_cards_info += f"{position_name}: {card['card_name']} ({card['orientation']}) - 基本的な意味: {card['meaning']}\n"

    prompt = f"""以下の5枚のタロットカードがギリシャ十字スプレッドで出ました。

{prompt_cards_info}
相談者の質問: 「{user_question}」

これらのカードとそれぞれのポジションの意味、そして相談者の質問を踏まえ、タロット占い師の視点から詳細な解釈とアドバイスを**Markdown形式**で生成してください。見出し、リスト、強調などを使って、読みやすく構成してください。カード間の関連性も考慮に入れるとより良いでしょう。"""

    # Geminiから解釈を取得 (Markdownテキストを期待)
    interpretation_markdown = generate_interpretation(prompt)

    # MarkdownをHTMLに変換
    try:
        # fenced_code: コードブロック用, nl2br: 改行を<br>に変換
        interpretation_html = markdown.markdown(interpretation_markdown, extensions=['fenced_code', 'nl2br'])
    except Exception as e:
        print(f"MarkdownのHTML変換中にエラー: {e}")
        # エラー時はプレーンテキストを<pre>タグで囲んで返す
        interpretation_html = f"<p>解釈の表示中にエラーが発生しました。</p><pre>{interpretation_markdown}</pre>"


    return jsonify({"interpretation_html": interpretation_html}) # HTMLを返すように変更


if __name__ == '__main__':
    # 仮想環境のPythonインタープリタで実行されるようにする
    # 通常、`flask run` コマンドを使用するか、
    # 実行時に `env\Scripts\python app.py` のように指定します。
    # ここでの app.run() は開発用サーバーの起動です。
    app.run(debug=True)