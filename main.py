import google.generativeai as genai
import os
import random
import json

with open("cards_meaning/big_cards.json", mode = "r", encoding="utf-8") as f:
    cards_meaning = json.load(f)

def select_card(cards):
    place = ["正位置", "逆位置"]
    card = []
    for i in range(5):
        card += [[random.choice(place), random.choice(cards)]]
        cards.remove(card[i][1])
    return card

def create_prompt(selects, question=None):
    """Gemini APIに送るプロンプトを作成する"""
    prompt = "あなたは経験豊富なタロット占い師です。\n以下のタロットカードの結果に基づいて、相談内容について占ってください。\n\n"

    if question:
        prompt += f"相談内容: {question}\n\n"
    else:
        prompt += "相談内容: (指定なし。全体的な運勢やアドバイス)\n\n"

    prompt += "--- 出たカード ---\n"
    
    prompt += "-----------------\n\n"

    prompt += "上記のカードの配置とそれぞれの意味（正位置・逆位置を含む）を考慮し、具体的で洞察に満ちた、優しい言葉でアドバイスをお願いします。単にカードの意味を並べるだけでなく、カード同士の関連性も読み解き、相談者が前向きになれるような解釈をしてください。"
    return prompt

print(select_card(cards_meaning))

