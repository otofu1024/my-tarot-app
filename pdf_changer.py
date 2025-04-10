import pypdf
import re
import json
import os

def extract_text_from_pdf(pdf_path):
    """PDFファイルから全ページのテキストを抽出して返す"""
    try:
        reader = pypdf.PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n" # ページ間に改行を入れる
        return full_text
    except Exception as e:
        print(f"エラー: PDFファイルの読み込み中にエラーが発生しました: {e}")
        return None

def parse_tarot_text(text):
    """抽出したテキストを解析し、タロットカード情報のリストを返す"""
    cards = []
    current_card = None
    lines = text.splitlines() # テキストを行ごとに分割

    for line in lines:
        line = line.strip() # 各行の前後の空白を除去

        if not line: # 空行はスキップ
            continue

        # 【カード名】 の行を検出
        match_name = re.match(r"^【(.+?)】$", line)
        if match_name:
            # もし処理中のカードがあれば、それをリストに追加
            if current_card:
                # 意味が空の場合も考慮
                if "meaning_up" not in current_card: current_card["meaning_up"] = ""
                if "meaning_rev" not in current_card: current_card["meaning_rev"] = ""
                cards.append(current_card)
            # 新しいカード情報の開始
            current_card = {"name": match_name.group(1).strip()}
            continue

        # 正位置： の行を検出
        # re.IGNORECASE を使うと '正位置:' と '正位置：' の両方に対応可能 (全角・半角コロン)
        match_up = re.match(r"^正位置：(.*)$", line, re.IGNORECASE)
        if match_up and current_card is not None:
            # すでに意味が設定されている場合は追記（複数行対応）
            if "meaning_up" in current_card and current_card["meaning_up"]:
                current_card["meaning_up"] += " " + match_up.group(1).strip()
            else:
                current_card["meaning_up"] = match_up.group(1).strip()
            continue

        # 逆位置： の行を検出
        match_rev = re.match(r"^逆位置：(.*)$", line, re.IGNORECASE)
        if match_rev and current_card is not None:
            # すでに意味が設定されている場合は追記（複数行対応）
            if "meaning_rev" in current_card and current_card["meaning_rev"]:
                current_card["meaning_rev"] += " " + match_rev.group(1).strip()
            else:
                current_card["meaning_rev"] = match_rev.group(1).strip()
            continue

        # カード名、正位置、逆位置以外の行
        # (例: ⾺⿅にされるのが怖い)
        # current_card が存在し、まだ逆位置の意味が設定されていなければ、
        # 逆位置の意味の一部として追記する、などの処理も可能だが、
        # 今回は厳密に "正位置：" "逆位置：" で始まる行のみを抽出する。

    # ループ終了後、最後のカード情報をリストに追加
    if current_card:
        if "meaning_up" not in current_card: current_card["meaning_up"] = ""
        if "meaning_rev" not in current_card: current_card["meaning_rev"] = ""
        cards.append(current_card)

    return cards

def save_to_json(data, json_path):
    """データをJSONファイルとして保存する"""
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            # ensure_ascii=False で日本語をそのまま出力
            # indent=4 で見やすいようにインデントを付ける
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"エラー: JSONファイルへの書き込み中にエラーが発生しました: {e}")
        return False
    
pdf_file_path = ["takara-tarot-wands", "takara-tarot-cups", "takara-tarot-swords", "takara-tarot-PENTACLES"]

# --- メイン処理 ---
for i in pdf_file_path:
    if __name__ == "__main__":
        # ↓↓↓ このファイル名を実際のPDFファイル名に置き換えてください ↓↓↓
        pdf_file_path = f"{i}.pdf"
        # ↓↓↓ 出力するJSONファイル名 ↓↓↓
        json_file_path = f"{i}.json"

        # PDFファイルが存在するか確認
        if not os.path.exists(pdf_file_path):
            print(f"エラー: 指定されたPDFファイルが見つかりません: {pdf_file_path}")
            print("コード内の 'pdf_file_path' を正しいファイル名に変更してください。")
        else:
            print(f"PDFファイル '{pdf_file_path}' からテキストを抽出中...")
            pdf_text = extract_text_from_pdf(pdf_file_path)

            if pdf_text:
                print("テキストの解析中...")
                tarot_data_list = parse_tarot_text(pdf_text)

                if tarot_data_list:
                    print(f"{len(tarot_data_list)} 件のカードデータを抽出しました。")
                    print(f"データを '{json_file_path}' に保存中...")
                    if save_to_json(tarot_data_list, json_file_path):
                        print("JSONファイルへの保存が完了しました。")
                    else:
                        print("JSONファイルへの保存に失敗しました。")
                else:
                    print("エラー: テキストからカードデータを抽出できませんでした。")
                    print("PDF内のテキスト形式が想定と異なっている可能性があります。")
                    print("例: 【カード名】、改行、'正位置：...'、改行、'逆位置：...' の形式か確認してください。")
            else:
                print("エラー: PDFからテキストを抽出できませんでした。ファイルが破損しているか、テキスト情報が含まれていない可能性があります。")