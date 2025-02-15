import streamlit as st
import random
import time
from openai import OpenAI  # New interface
import os
import requests

# ====================
# Custom CSS for Casino-themed design
st.markdown(
    """
    <style>
    /* 배경 설정 (Unsplash의 casino 관련 이미지 사용) */
    body {
        background-image: url("https://source.unsplash.com/1600x900/?casino");
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* 제목 및 텍스트 색상 */
    h1, h2, h3 {
        color: #FFD700; /* 골드 색상 */
        text-shadow: 2px 2px 4px #000000;
    }
    p, li, span, .stMarkdown {
        color: #FFFFFF; /* 흰색 텍스트 */
    }
    /* 버튼 스타일링 */
    .stButton>button {
        background-color: #FFD700;
        color: #000000;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5em 1em;
    }
    /* 입력창 스타일링 */
    .stTextInput>div>input {
        background-color: #333333;
        color: #FFD700;
        border: 1px solid #FFD700;
        border-radius: 8px;
        padding: 0.5em;
    }
    /* Sidebar 스타일 (옵션) */
    .css-1d391kg { 
        background-color: rgba(0, 0, 0, 0.7);
    }
    </style>
    """, unsafe_allow_html=True
)

# ====================
# Initialize OpenAI client using Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Initialize session state variables
if "step" not in st.session_state:
    st.session_state.step = 0  # 0: Rules, 1: Betting, 2: Game Play, 3: Strategy, 4: Practice
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_questions" not in st.session_state:
    st.session_state.pending_questions = False
if "game_active" not in st.session_state:
    st.session_state.game_active = False
if "player_hand" not in st.session_state:
    st.session_state.player_hand = []
if "dealer_hand" not in st.session_state:
    st.session_state.dealer_hand = []
if "player_score" not in st.session_state:
    st.session_state.player_score = 0
if "dealer_score" not in st.session_state:
    st.session_state.dealer_score = 0

# ====================
# Hardcoded lesson texts for each step (casino style, Markdown formatted)
step_texts = {
    0: """## Step 1: Blackjack Basic Rules
**Objective:**  
Beat the dealer by having a hand value closer to 21 without exceeding it.

**Card Values:**  
- **A (Ace):** Counts as 1 or 11 (whichever is more beneficial).  
- **2-10:** Face value.  
- **J, Q, K:** Each counts as 10.

*Example:*  
An Ace and a 7 can total either 8 or 18.
""",
    1: """## Step 2: Betting Methods
**How to Place a Bet:**  
- **Minimum Bet:** Typically \$5 to \$10.  
- **Timing:** Place your bet before the dealer deals the cards.
- **Extra Options:**  
  - **Double Down:** Double your bet for one extra card, then stand.
  - **Split:** If you have two cards of the same value, split them into two hands (with an extra bet equal to your original bet).

*Tip:*  
Effective betting helps manage risk.
""",
    2: """## Step 3: Gameplay
**Game Flow:**  
1. **Initial Deal:** The dealer gives two cards to each player and themselves (one card is hidden).  
2. **Player's Turn:**  
   - **Hit:** Request an additional card.  
   - **Stand:** Keep your current hand.
3. **Dealer's Turn:** Reveal the hidden card and draw until reaching at least 17.
4. **Outcome:**  
   - Exceeding 21 results in a Bust (automatic loss).  
   - The hand closest to 21 wins.
""",
    3: """## Step 4: Probability & Strategy
**Strategies:**  
- **Basic Strategy:** Follow guidelines for the best move (Hit, Stand, Double Down, or Split) based on your hand and the dealer's card.
- **Card Counting (Hi-Lo):** Track the ratio of high to low cards remaining.
- **Advanced Analysis:** Use probability to determine optimal moves and manage risk.

*Note:*  
Even with strategy, luck plays a significant role.
""",
    4: """## Step 5: Practice Mode
**Practice Mode:**  
The AI will act as the dealer in a simulated game.

*Example:*  
- **Your Cards:** 10 and 6 (Total: 16)  
- **Dealer's Visible Card:** 9

**Instructions:**  
- Type **'Hit'** to take another card, or **'Stand'** to hold your hand.
- You may also ask questions (e.g., "Why did my hand bust?" or "Should I hit on 16?").

**Responsible Gambling:**  
Please gamble responsibly. This simulation is for educational purposes only.
"""
}

# ====================
# Card related functions
card_values = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6,
    '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': [1, 11]
}

def draw_card():
    return random.choice(list(card_values.keys()))

def calculate_hand(hand):
    total = 0
    aces = 0
    for card in hand:
        if card == 'A':
            aces += 1
        else:
            total += card_values[card]
    for _ in range(aces):
        if total + 11 > 21:
            total += 1
        else:
            total += 11
    return total

# ====================
# Blackjack practice simulation function (stores game state in session)
def blackjack_game(user_input):
    if st.session_state.step < 4:
        return "You must learn the basic rules before entering Practice Mode!"

    # Initialize game if not already active
    if not st.session_state.game_active:
        st.session_state.game_active = True
        st.session_state.player_hand = [draw_card(), draw_card()]
        st.session_state.dealer_hand = [draw_card(), draw_card()]
        st.session_state.player_score = calculate_hand(st.session_state.player_hand)
        st.session_state.dealer_score = calculate_hand(st.session_state.dealer_hand)
        init_message = (f"🎮 **Game Start!**\n"
                        f"🃏 Your cards: {st.session_state.player_hand} (Total {st.session_state.player_score} points)\n"
                        f"🃏 Dealer's visible card: {st.session_state.dealer_hand[0]}\n"
                        f"Type 'Hit' or 'Stand'.")
        return init_message

    # Process game actions: if user inputs "Hit" or "Stand"
    user_input_lower = user_input.strip().lower()
    if user_input_lower == "hit":
        new_card = draw_card()
        st.session_state.player_hand.append(new_card)
        st.session_state.player_score = calculate_hand(st.session_state.player_hand)
        response = (f"✨ You chose Hit!\n"
                    f"🃏 New card: {new_card}\n"
                    f"🃏 Your cards now: {st.session_state.player_hand} (Total {st.session_state.player_score} points)\n")
        if st.session_state.player_score > 21:
            response += "💥 Bust! You exceeded 21 and lost the game."
            st.session_state.game_active = False
        else:
            response += "Type 'Hit' or 'Stand' to continue."
        return response

    elif user_input_lower == "stand":
        response = "🛑 You chose Stand!\n"
        while st.session_state.dealer_score < 17:
            st.session_state.dealer_hand.append(draw_card())
            st.session_state.dealer_score = calculate_hand(st.session_state.dealer_hand)
        response += (f"🏆 Dealer's final cards: {st.session_state.dealer_hand} (Total {st.session_state.dealer_score} points)\n"
                     f"🃏 Your final cards: {st.session_state.player_hand} (Total {st.session_state.player_score} points)\n")
        if st.session_state.dealer_score > 21 or st.session_state.player_score > st.session_state.dealer_score:
            response += "🎉 You win!"
        elif st.session_state.player_score < st.session_state.dealer_score:
            response += "😢 You lose."
        else:
            response += "⚖️ It's a tie."
        st.session_state.game_active = False
        return response

    # For any other input, treat it as a game-related question (e.g., "Why did my hand bust?")
    else:
        system_prompt = f"""
You are a Blackjack tutor assisting a player during a game.
Please answer kindly!
Current game state:
- Your cards: {st.session_state.player_hand} (Score: {st.session_state.player_score})
- Dealer's visible card: {st.session_state.dealer_hand[0]}
Answer the user's question in relation to the current game.
"""
        prompt = system_prompt + "\nUser: " + user_input + "\nAnswer:"
        try:
            answer = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt}
                ]
            ).choices[0].message.content
        except Exception as e:
            answer = f"API call error: {e}"
        return answer

# ====================
# Main GPT call function (for steps other than Practice Mode)
def gpt_call(user_input):
    if st.session_state.step == 4:
        return blackjack_game(user_input)
    
    # If user types "next step", proceed to next lesson step
    if user_input.strip().lower() == "next step":
        st.session_state.step += 1
        st.session_state.pending_questions = False
        st.experimental_rerun()
        return f"🎉 **Moving to the next step!**\n\n{step_texts[st.session_state.step]}"
    
    # If user types "current step", show the current step description
    if user_input.strip().lower() == "current step":
        return step_texts[st.session_state.step]
    
    # Otherwise, treat the input as a question and call the API
    st.session_state.pending_questions = True
    system_prompt = f"""
You are an AI tutor teaching Blackjack step by step.
The user is currently at **Step {st.session_state.step}**:
{step_texts[st.session_state.step]}

Answer the user's question in a way that relates to the current Blackjack lesson.
Please answer kindly!
"""
    prompt = system_prompt + "\nUser: " + user_input + "\nAnswer:"
    try:
        ai_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt}
            ]
        ).choices[0].message.content
    except Exception as e:
        ai_response = f"API call error: {e}"
    
    st.session_state.history.append({"role": "assistant", "content": ai_response})
    return ai_response

# ====================
# Streamlit UI configuration
st.title("Blackjack AI Tutor")
st.markdown("Learn Blackjack step-by-step. Each lesson's explanation is hardcoded, and even in Practice Mode you can ask additional questions.")
st.markdown(f"### Current Step: {st.session_state.step+1}")
st.markdown(step_texts[st.session_state.step])

# If in Practice Mode and game is active, display the current card status in a nice layout
if st.session_state.step == 4 and st.session_state.game_active:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Your Hand:**")
        st.markdown(f"<h2>{' '.join(st.session_state.player_hand)}</h2>", unsafe_allow_html=True)
        st.markdown(f"**Total:** {st.session_state.player_score}")
    with col2:
        st.markdown("**Dealer's Hand:**")
        if st.session_state.game_active:
            st.markdown(f"<h2>{st.session_state.dealer_hand[0]}  ???</h2>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h2>{' '.join(st.session_state.dealer_hand)}</h2>", unsafe_allow_html=True)
        st.markdown(f"**Total:** {st.session_state.dealer_score if not st.session_state.game_active else 'Hidden'}")

# Get user input
user_input = st.text_input("Enter a question, or type 'next step' or 'current step':")

if st.button("Submit"):
    if user_input:
        output = gpt_call(user_input)
        st.write(output)
