import google.generativeai as genai
import os
import random
import json
import traceback
import time

# Load tarot card information
with open("cards_meaning/all_cards.json", mode="r", encoding="utf-8") as f:
    cards_meaning = json.load(f)

def setup_gemini_model():
    """Get API key and initialize Gemini model"""
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        print("Error: Environment variable 'GOOGLE_API_KEY' is not set.")
        return None

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        print(f"Error initializing Gemini API: {e}")
        return None

def select_card(cards, num):
    """Select specified number of cards randomly"""
    cards_copy = cards.copy()  # Make a copy to avoid modifying the original list
    positions = ["meaning_up", "meaning_rev"]
    selected_cards = []
    
    for _ in range(min(num, len(cards_copy))):
        card_details = random.choice(cards_copy)
        position = random.choice(positions)
        selected_cards.append([position, card_details])
        cards_copy.remove(card_details)
    
    return selected_cards

def create_interactive_tarot(model, question):
    """Interactive tarot reading session"""
    positions = ["Current Situation", "Obstacles/Challenges", "Future Trend", "Advice", "Final Outcome"]
    
    print("Selecting cards...")
    selected_cards = select_card(cards_meaning, len(positions))
    
    print(f"\n========== Tarot Reading: {question if question else 'General Reading'} ==========\n")
    print("I'll explain each card one by one and we'll have a conversation about them.\n")
    
    # Context to store dialogues for each card
    dialogue_context = []
    posit = {"meaning_up": "Upright", 
             "meaning_rev": "Reversed"}
    
    # Interpret each card in dialogue format
    for i, (card_position, card_details) in enumerate(selected_cards):
        position_name = positions[i]
        card_name = card_details['name']
        card_meaning = card_details[card_position]
        
        print(f"\n----- Card for '{position_name}' -----")
        time.sleep(1)
        print(f"The '{card_name}' appears {posit[card_position]}.")
        print(f"Meaning of this card: {card_meaning}\n")
        
        # AI's initial interpretation
        prompt = f"""
You are an experienced tarot reader conducting an interactive reading.
Reading topic: {question if question else 'General life guidance'}
The card '{card_name}' has appeared {card_position} in the '{position_name}' position.
Meaning: {card_meaning}

Please provide a gentle explanation of this card, asking the querent a question like 
"Does this card resonate with your current situation?" or similar.
Keep your response within 200 words.
"""
        
        try:
            response = model.generate_content(prompt)
            print(f"Tarot Reader: {response.text}\n")
            
            # Wait for user's response
            user_response = input("You: ")
            
            # Record the dialogue
            dialogue_context.append({
                "position": position_name,
                "card": card_name,
                "position_type": card_position,
                "meaning": card_meaning,
                "ai_comment": response.text,
                "user_response": user_response
            })
            
            # AI's personalized interpretation based on user's response
            follow_up_prompt = f"""
User's response: "{user_response}"

Based on the user's response, provide a more personalized interpretation of the card '{card_name}' 
({card_position}) in the '{position_name}' position. Tailor your insights to the user's specific situation.
Keep your response within 200 words.
"""
            follow_up_response = model.generate_content(follow_up_prompt)
            print(f"\nTarot Reader: {follow_up_response.text}")
            print("\n(Press Enter to continue to the next card)")
            input()
            
            dialogue_context[-1]["ai_follow_up"] = follow_up_response.text
            
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
    
    # Provide a comprehensive interpretation after all cards
    print("\n\n===== All cards have been interpreted =====")
    print("Generating final comprehensive reading...\n")
    
    # Create prompt for final interpretation
    final_prompt = f"Reading topic: {question if question else 'General life guidance'}\n\n"
    final_prompt += "Cards drawn and conversations with the querent:\n"
    
    for dialogue in dialogue_context:
        final_prompt += f"""
Position: {dialogue['position']}
Card: {dialogue['card']} ({dialogue['position_type']})
Card meaning: {dialogue['meaning']}
Querent's response: {dialogue['user_response']}
"""
    
    final_prompt += """
Based on the cards and conversations above, please provide a comprehensive reading that considers 
the relationships between all cards. Offer thoughtful insights and advice that will inspire the querent 
with hope and practical guidance.
"""
    
    try:
        final_response = model.generate_content(final_prompt)
        print("\n----- Comprehensive Reading -----")
        print(final_response.text)
        print("--------------------------------")
        return True
    except Exception as e:
        print(f"Error generating comprehensive reading: {e}")
        traceback.print_exc()
        return False

def main():
    """Main program"""
    # Initialize model
    model = setup_gemini_model()
    if not model:
        print("Failed to initialize model. Exiting program.")
        return
    
    print("=== Interactive Tarot Reading ===")
    print("What would you like to explore today?")
    
    # Get query topic
    question = input("Enter your reading topic (e.g. love, career, general guidance, etc. - press Enter for general reading): ")
    question = question.strip() or None
    
    # Run interactive tarot reading
    success = create_interactive_tarot(model, question)
    
    if not success:
        print("\nAn error occurred during the reading. Please try again.")

if __name__ == "__main__":
    main()