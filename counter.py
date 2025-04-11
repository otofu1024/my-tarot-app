import json

cards = ["big_cards", "takara-tarot-cups", "takara-tarot-swords", "takara-tarot-wands", "takara-tarot-PENTACLES"]
data1 = []

for card in cards:
    with open(f"cards_meaning/{card}.json", "r", encoding="utf-8") as f:
        data1 += json.load(f)

print(len(data1))

with open("cards_meaning/all_cards.json", "r", encoding="utf-8") as f:
    data2 = json.load(f)
print(len(data2))