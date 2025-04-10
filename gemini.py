import google.generativeai as genai
import os

# --- APIキーの設定 ---
# 環境変数 "GOOGLE_API_KEY" から値を取得
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# 環境変数が設定されているか確認
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

prompt ="宇宙人にとって理想の朝ごはんを教えてください。"

print("Geminiに応答を生成してもらっています...")
try:
    response = model.generate_content(prompt)
    print("\n--- Geminiからの応答 ---")
    print(response.text)
    print("------------------------")
except Exception as e:
    print(f"Geminiからの応答生成中にエラーが発生しました: {e}")