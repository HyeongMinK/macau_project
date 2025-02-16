import streamlit as st
import random
import time
from openai import OpenAI  # New interface
import os
from streamlit_mic_recorder import mic_recorder
import io
import whisper
import tempfile
from pydub import AudioSegment
import re

# Set up your OpenAI API key (using environment variable or Streamlit secrets)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Load the Whisper model
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("small")

model = load_whisper_model()

if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False

if 'output' not in st.session_state:
    st.session_state.output = False

if 'tts_audio_data' not in st.session_state:
    st.session_state.tts_audio_data = False


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

# Hardcoded lesson texts for each step
step_texts = {
    0: """#### Step 1: Blackjack Basic Rules
**Objective:**  
Beat the dealer by having a hand value closer to 21 without exceeding it.

**Card Values:**  
- **A (Ace):** Can count as 1 or 11 (choose whichever is more advantageous).  
- **2-10:** Count as their face value.  
- **J, Q, K:** Each counts as 10.

*Example:*  
If you have an Ace and a 7, your total can be either 8 or 18.
""",
    1: """#### Step 2: Betting Methods
**How to Place a Bet:**  
- **Minimum Bet:** Typically starts from \$500 to \$1000.  
- **When to Bet:** Place your bet before the dealer deals the cards.
- **Additional Options:**  
  - **Double Down:** Double your bet in exchange for receiving one extra card and then standing.
  - **Split:** If you have two cards of the same value, you can split them into two hands (with an additional bet equal to your original bet).

*Tip:*  
Proper betting can help manage risk and maximize potential gains.
""",
    2: """#### Step 3: Gameplay
**Game Flow:**  
1. **Initial Deal:** The dealer gives two cards to each player and two to themselves (one card is usually hidden).  
2. **Player's Turn:**  
   - **Hit:** Request another card to improve your hand.  
   - **Stand:** End your turn and keep your current hand.
3. **Dealer's Turn:** The dealer reveals their hidden card and must keep drawing until their hand value reaches at least 17.
4. **Outcome:**  
   - If your hand exceeds 21, you Bust (lose automatically).  
   - If neither busts, the hand closest to 21 wins.
""",
    3: """#### Step 4: Probability & Strategy
**Key Strategies:**  
- **Basic Strategy:**  
  Follow a set of guidelines that recommend the best action (Hit, Stand, Double Down, or Split) for every possible combination of your hand and the dealer's visible card.
- **Card Counting (Hi-Lo System):**  
  A method to estimate the ratio of high cards to low cards remaining in the deck, which can guide your decisions on betting and playing.
- **Advanced Analysis:**  
  Use probability analysis to determine optimal moves and manage risk effectively.

*Remember:*  
While strategy can improve your odds, Blackjack still involves an element of chance.
""",
    4: """#### Step 5: Responsible Gambling  
Before you start the practice game, it's important to understand responsible gambling principles.  

**✅ Responsible Gambling Guidelines:**  
- **Set Limits:** Decide in advance how much time and money you are willing to spend.  
- **Play for Fun:** Treat blackjack as entertainment, not a way to make money.  
- **Know When to Stop:** If you are feeling frustrated or chasing losses, take a break.  
- **Avoid Impulsiveness:** Never gamble under stress, pressure, or influence of alcohol.  
- **Seek Help if Needed:** If gambling starts to feel like a problem, reach out to support organizations.  

🔹 **Remember:** The goal of this simulation is to learn, not to develop gambling habits.
""",
    5: """#### Step 6: Practice Mode
**Simulation Mode:**  
Now, the AI will act as the dealer. Try playing a simulated game.

**Instructions:**  
- Type **'Hit'** if you want another card.
- Type **'Stand'** if you want to hold your current hand.
- You can also ask additional questions (e.g., "Why did my hand bust?" or "Should I hit on 16?").

*Practice Tip:*  
Experiment with different actions and ask questions to understand the outcomes better.
"""
}

# Hardcoded lesson texts for each step
step_texts = {
    0: """Welcome to Step 1 of your Blackjack learning journey! Before we dive into strategy and gameplay, let’s start with the basic rules of the game. Blackjack is a card game where your goal is to beat the dealer by having a hand value closer to 21 without exceeding it. It’s a simple objective, but there are key rules you need to understand first. Each card has a specific value. Number cards, from 2 to 10, are worth their face value. and Face cards, which are Jack, Queen, and King, are all worth 10 points each. lastly, Aces are unique because they can be counted as either 1 or 11, depending on what benefits your hand the most. For example, if you’re dealt an Ace and a 7, your total could be either 8 or 18, giving you some flexibility in your decisions. The game starts when both you and the dealer receive two cards. The dealer keeps one card hidden, so you don’t know their full hand yet. From there, it’s all about making smart choices based on what you have and what the dealer might have.
Now that we’ve covered the basics, let’s move on to the next step—understanding how betting works in Blackjack.
""",
    1: """Now that we understand the basic rules of Blackjack, let's talk about betting methods.
Before the game begins, every player must place a bet. In most casinos, the minimum bet is typically $500 or $1000, though this can vary depending on the table. This bet must be placed before the dealer starts dealing the cards, so it's important to decide how much you're willing to wager before the game begins. Once the initial bet is placed, the game begins. However, during the round, there are a few additional betting options you might consider. First is Double Down. If you're confident in your hand, you have the option to double your original bet in exchange for receiving one more card before you must stand. This move can be risky, but it is often used when players believe they have a strong chance of winning. The second option is Split. If your first two cards have the same value, such as a pair of 8s or a pair of Kings, you can split them into two separate hands. To do this, you must place an additional bet equal to your original wager. After splitting, each hand will be played separately, giving you a chance to win twice—but also doubling the risk.
""",
    2: """In Blackjack, the game begins with the initial deal. Each player, including the dealer, receives two cards. However, while the players can see both of their own cards, the dealer keeps one card hidden, known as the hole card.
Once the cards are dealt, it is the player’s turn. Players must decide whether to take additional cards or keep their current hand. If a player chooses to Hit, they receive another card in an attempt to improve their total. This can be beneficial when their hand is far from 21. Alternatively, if they believe their current total is strong enough, they may choose to Stand, ending their turn without drawing more cards.
After all players have completed their turns, the dealer’s turn begins. The dealer reveals their hidden card and follows a fixed rule—they must continue drawing cards until their hand reaches at least 17. If their total is 17 or higher, they must stand.
Finally, the game determines the outcome. If a player's total exceeds 21 at any point, they automatically lose, known as a bust. If neither the player nor the dealer busts, the winner is the one with a hand closest to 21. If both have the same total, the round ends in a tie, or a push, and the player’s bet is returned.
Understanding when to Hit or Stand is crucial for success in Blackjack, and as we move forward, we will explore strategies to help you make better decisions during gameplay.
""",
    3: """In Blackjack, understanding probability and strategy can significantly improve your chances of winning. The most essential tool is Basic Strategy, which provides the optimal move for every hand combination based on statistical analysis. It tells you when to Hit, Stand, Double Down, or Split to maximize your odds of success. Another technique is Card Counting, particularly the Hi-Lo System, which helps track the ratio of high to low-value cards in the deck. When more high-value cards remain, the player has an advantage, making it a good time to increase bets. However, while legal, casinos discourage card counting and may intervene if they suspect it. Lastly, Advanced Analysis involves using probability models to refine decision-making beyond basic strategy. While no method guarantees a win, applying these strategies can help you play smarter and reduce the house edge. Now, let's move on to the next step and put these concepts into practice!
""",
    4: """Welcome to Step 5 of your Blackjack learning journey. Before we begin practice mode, let’s take a moment to talk about responsible gambling.
Blackjack is a game of both skill and chance, but it should always remain a form of entertainment. Set a limit on your time and budget before you start, and never chase losses. The house always has an edge, so focus on making smart decisions rather than expecting to win every hand.
It's also important to be aware of your emotions while playing. If you feel frustrated or tempted to keep going despite losses, take a break. And remember, never gamble under pressure or the influence of alcohol.
If gambling ever feels like more than just a game, seek support. There are resources available to help.
With that in mind, let’s move on to Practice Mode and apply what you’ve learned in a controlled environment!
""",
    5: """Now, it's time to put everything you've learned into practice! In this simulation mode, the AI will act as the dealer, and you’ll play a round of Blackjack just like in a real game.
During your turn, you have two main options: Hit to take another card or Stand to keep your current hand. The goal remains the same—get as close to 21 as possible without going over. If you're unsure about a move, feel free to ask questions like, ‘Should I hit on 16?’ or ‘Why did my hand bust?’
This practice session is a great opportunity to experiment with different decisions and refine your strategy. Let’s see how well you can play!
"""
}



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

# Blackjack practice simulation function (stores game state in session)
def blackjack_game(user_input):
    if st.session_state.step < 5:
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
Current game state:
- Your cards: {st.session_state.player_hand} (Score: {st.session_state.player_score})
- Dealer's visible card: {st.session_state.dealer_hand[0]}
Answer the user's question in relation to the current game.
"""
        try:
            api_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            answer = api_response.choices[0].message.content
        except Exception as e:
            answer = f"API call error: {e}"
        return answer

# Main GPT call function (for steps other than Practice Mode)
def gpt_call(user_input):
    if st.session_state.step == 5:
        return blackjack_game(user_input)
    
    # If user types "next step", proceed to next lesson step (without checking unresolved questions)
    if user_input.strip().lower() == "next step":
        st.session_state.step += 1
        st.session_state.pending_questions = False
        return step_texts[st.session_state.step]
    
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
"""
    try:
        api_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        ai_response = api_response.choices[0].message.content
    except Exception as e:
        ai_response = f"API call error: {e}"
    
    st.session_state.history.append({"role": "assistant", "content": ai_response})
    return ai_response

def transcribe_audio(audio_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        temp_audio.write(audio_bytes)  # WebM 오디오 데이터를 임시 파일에 저장
        temp_audio.flush()
        webm_path = temp_audio.name  # WebM 파일 경로
    # Whisper에 파일 경로 전달
    result = model.transcribe(webm_path, language="en")

    # 파일 정리 (임시 파일 삭제)
    #temp_audio.close()
    #os.remove(webm_path)
    return result["text"]


def remove_special_characters(text):
    return re.sub(r"[^a-zA-Z0-9\s]", "", text)  # 알파벳, 숫자, 공백만 남김


def state_recode():
    st.session_state.is_recording = True

def text_to_speech(client, text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="echo",
        input=text,
        speed = 1.2
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio_file:
        response.stream_to_file(tmp_audio_file.name)
        tmp_file_name = tmp_audio_file.name
    
    return tmp_file_name



# Streamlit UI configuration
st.title("Blackjack AI Tutor")
st.markdown("Learn Blackjack step-by-step.")
st.markdown(step_texts[st.session_state.step])



audio = mic_recorder(start_prompt=f"Say!", stop_prompt="Stop", format="webm", callback = state_recode)
if audio and st.session_state.is_recording:
    transcribed_text = remove_special_characters(transcribe_audio(audio["bytes"]))
    #st.write(transcribed_text)
    st.session_state.output = gpt_call(transcribed_text)
    st.session_state.tts_audio_data=text_to_speech(client, """In Blackjack, understanding probability and strategy can significantly improve your chances of winning. The most essential tool is Basic Strategy, which provides the optimal move for every hand combination based on statistical analysis. It tells you when to Hit, Stand, Double Down, or Split to maximize your odds of success. Another technique is Card Counting, particularly the Hi-Lo System, which helps track the ratio of high to low-value cards in the deck. When more high-value cards remain, the player has an advantage, making it a good time to increase bets. However, while legal, casinos discourage card counting and may intervene if they suspect it. Lastly, Advanced Analysis involves using probability models to refine decision-making beyond basic strategy. While no method guarantees a win, applying these strategies can help you play smarter and reduce the house edge. Now, let's move on to the next step and put these concepts into practice!
""")
    st.session_state.is_recording = False
    st.rerun()

if st.session_state.output and st.session_state.output !='next step':
    st.write(st.session_state.output)

if st.session_state.tts_audio_data:
    st.audio(st.session_state.tts_audio_data, format='audio/mp3', autoplay=True)


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