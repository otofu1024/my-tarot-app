import google.generativeai as genai
import os

# --- グローバル変数 ---
model = None
api_key_configured = False

# --- 初期化関数 ---
def initialize_gemini():
    """
    Gemini APIの初期設定を行う関数。
    環境変数からAPIキーを読み込み、モデルを初期化する。
    """
    global model, api_key_configured

    if api_key_configured:
        return True # すでに初期化済み

    # 環境変数 "GOOGLE_API_KEY" から値を取得
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # 環境変数が設定されているか確認
    if GOOGLE_API_KEY is None:
        print("エラー: 環境変数 'GOOGLE_API_KEY' が設定されていません。")
        return False

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        api_key_configured = True
    except Exception as e:
        print(f"APIキーの設定でエラーが発生しました: {e}")
        return False

    try:
        # モデルを初期化 (必要に応じてモデル名を変更)
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("Geminiモデルの初期化完了。")
        return True
    except Exception as e:
        print(f"モデルの初期化中にエラーが発生しました: {e}")
        model = None # エラー時はモデルをNoneに
        return False

# --- 応答生成関数 ---
def generate_interpretation(prompt):
    """
    与えられたプロンプトに基づいてGeminiに応答を生成させる関数。
    """
    global model

    if model is None:
        print("エラー: Geminiモデルが初期化されていません。")
        if not initialize_gemini(): # 再度初期化を試みる
            return "エラー: Geminiモデルの初期化に失敗しました。"

    print("Geminiに応答を生成してもらっています...")
    try:
        response = model.generate_content(prompt)
        print("Geminiからの応答取得完了。")
        return response.text
    except Exception as e:
        print(f"Geminiからの応答生成中にエラーが発生しました: {e}")
        return f"エラー: Geminiからの応答生成中に問題が発生しました。({e})"

# --- 直接実行された場合のテストコード (オプション) ---
if __name__ == '__main__':
    if initialize_gemini():
        test_prompt = "引いたタロットカードは「太陽」の正位置です。今日の運勢について教えてください。"
        interpretation = generate_interpretation(test_prompt)
        print("\n--- テスト応答 ---")
        print(interpretation)
        print("------------------")
    else:
        print("テスト実行失敗: 初期化に失敗しました。")