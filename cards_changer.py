import json

cards = ["big_cards", "takara-tarot-cups", "takara-tarot-swords", "takara-tarot-wands", "takara-tarot-PENTACLES"]
data = []

for card in cards:
    with open(f"cards_meaning/{card}.json", "r", encoding="utf-8") as f:
        data += json.load(f)

with open("cards_meaning/all_cards.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(data)
print(type(data))