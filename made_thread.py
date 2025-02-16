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

if 'des' not in st.session_state:
    st.session_state.des = True

if 'start' not in st.session_state:
    st.session_state.start = True

if 'game_init' not in st.session_state:
    st.session_state.game_init = False


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
        st.session_state.game_init = True
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
if st.session_state.start:
    if st.button("Start!"):
        st.session_state.start = False
        st.rerun()

if not st.session_state.start:
    st.markdown(step_texts[st.session_state.step])



    audio = mic_recorder(start_prompt=f"Say!", stop_prompt="Stop", format="webm", callback = state_recode)
    if audio and st.session_state.is_recording:
        transcribed_text = remove_special_characters(transcribe_audio(audio["bytes"]))
        #st.write(transcribed_text)
        st.session_state.output = gpt_call(transcribed_text)
        st.session_state.tts_audio_data=text_to_speech(client, st.session_state.output)
        st.session_state.is_recording = False
        st.session_state.des = False
        st.rerun()

    if st.session_state.step < 5:
        if st.button("Next Step"):
            st.session_state.tts_audio_data = False
            st.session_state.step += 1
            st.session_state.des = True
            st.rerun()

    if st.session_state.step == 5 and not st.session_state.game_active and not st.session_state.game_init:
        if st.button("Let's Play!"):
            blackjack_game("init")
            st.session_state.tts_audio_data = False
            st.rerun()

    if st.session_state.step == 5 and not st.session_state.game_active and st.session_state.game_init:
        if st.button("Let's Play Again!"):
            blackjack_game("init")
            st.session_state.tts_audio_data = False
            st.rerun()

    if st.session_state.des:  
        st.audio(f"{st.session_state.step}_step.mp3", format='audio/mp3', autoplay=True)

    if st.session_state.tts_audio_data:
        st.write(st.session_state.output)

    if st.session_state.tts_audio_data:
        st.audio(st.session_state.tts_audio_data, format='audio/mp3', autoplay=True)


    # If in Practice Mode and game is active, display the current card status in a nice layout
    if st.session_state.step == 5 and st.session_state.game_init:
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