import os
import json
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ApplicationBuilder, CallbackContext, ConversationHandler
from ai21 import AI21Client
from ai21.models.chat import ChatMessage, ResponseFormat
from fuzzywuzzy import fuzz
import requests
import tempfile

# Logging for easier debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace these with your actual tokens
TELEGRAM_TOKEN = '7352332267:AAF6JBCZ5VDWKeJfkQef5vp3zIQf0irMS1k'
DEEPGRAM_API_KEY = '9ca7f77b121f98da70e324e8047b62d55f699cd6'
DEEPGRAM_URL = 'https://api.deepgram.com/v1/listen'
LANGUAGE = 'ru'  # Russian language for transcription

# State for feedback conversation
FEEDBACK = 1

# AI21 setup
api_key_ai21 = "oUDVUnhMyoIGWRBamuRRReO1g3HDQcLe"
client = AI21Client(api_key=api_key_ai21)

# Initialize SQLite database for FAQ
def init_db():
    conn = sqlite3.connect('faq.db')
    cursor = conn.cursor()

    # Create the FAQ table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    ''')

    # Read FAQ data from the JSON file
    with open('faq.json', 'r', encoding='utf-8') as f:
        faq_entries = json.load(f)

    # Insert FAQ entries into the database
    faq_data = [(entry['question'], entry['answer']) for entry in faq_entries]
    cursor.executemany('INSERT INTO faq (question, answer) VALUES (?, ?)', faq_data)

    conn.commit()
    conn.close()

# Send a message with HTML formatting
async def send_message(update, text):
    await update.message.reply_text(text, parse_mode='HTML')

# Check if the message is similar to an FAQ question using fuzzy matching
def find_answer_in_faq_fuzzy(user_message):
    conn = sqlite3.connect('faq.db')
    cursor = conn.cursor()

    cursor.execute("SELECT question, answer FROM faq")
    results = cursor.fetchall()

    best_match = None
    highest_ratio = 0

    # Compare input message with FAQ questions using fuzzywuzzy
    for question, answer in results:
        ratio = fuzz.ratio(user_message.lower(), question.lower())
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = answer

    conn.close()

    # Return the answer if the similarity is higher than 45%
    if highest_ratio > 45:
        return best_match
    return None

# Transcribe the audio using Deepgram
async def transcribe_audio(audio_file_path):
    try:
        with open(audio_file_path, 'rb') as audio:
            audio_data = audio.read()

        headers = {
            'Authorization': f'Token {DEEPGRAM_API_KEY}',
            'Content-Type': 'audio/ogg'
        }
        params = {
            'language': LANGUAGE
        }

        # Sending the request to Deepgram API
        response = requests.post(DEEPGRAM_URL, headers=headers, params=params, data=audio_data)

        if response.status_code == 200:
            json_response = response.json()
            logger.info(f"Deepgram API response: {json_response}")
            return json_response['results']['channels'][0]['alternatives'][0]['transcript']
        else:
            logger.error(f"Deepgram API error: {response.status_code}, {response.text}")
            return None  # Return None if transcription fails
    except Exception as e:
        logger.error(f"Error during audio transcription: {str(e)}")
        return None

# Handle voice messages (audio transcription)
async def handle_voice(update: Update, context):
    try:
        file = await update.message.voice.get_file()

        # Download the file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
            temp_audio_path = temp_audio_file.name
            await file.download_to_drive(temp_audio_file.name)

        # Transcribe audio to text
        transcribed_text = await transcribe_audio(temp_audio_path)
        os.remove(temp_audio_path)

        if transcribed_text:
            logger.info(f"Transcribed text: {transcribed_text}")

            # First check if "такси" or "еда" is in the transcribed text
            if "такси" in transcribed_text.lower() or "еда" in transcribed_text.lower():
                await send_web_app(update, context, transcribed_text)
            else:
                # Check FAQ for a match
                faq_answer = find_answer_in_faq_fuzzy(transcribed_text)
                if faq_answer:
                    await send_message(update, faq_answer)
                else:
                    # No FAQ match, send to AI21 (LLM)
                    response_text = get_ai21_response(transcribed_text)
                    await send_message(update, response_text)
        else:
            await update.message.reply_text("Sorry, I couldn't transcribe the audio. Please try again.")
    except Exception as e:
        logger.error(f"Error handling voice message: {str(e)}")
        await update.message.reply_text("An error occurred while processing the voice message. Please try again.")  # Error handling

# Get a response from AI21 using transcribed text or user message
def get_ai21_response(user_message):
    messages = [
        ChatMessage(role="user", content=user_message)
    ]
    response = client.chat.completions.create(
        model="jamba-1.5-large",
        messages=messages,
        documents=[],
        tools=[],
        n=1,
        max_tokens=200,  # Limit the number of tokens in the response
        temperature=0.4,
        top_p=1,
        stop=[],
        response_format=ResponseFormat(type="text")
    )
    return response.choices[0].message.content

# Handle web app for taxi or food
async def send_web_app(update: Update, context: CallbackContext, user_message: str = None):
    if user_message is None:
        # Extract user_message from the update if not provided
        user_message = update.message.text.lower()

    if "такси" in user_message:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Яндекс Такси🚕",  # Button text
                    web_app=WebAppInfo(url="https://taxi.yandex.kz/ru_kz/")  # Yandex Taxi url
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Нажми на кнопку, чтобы заказать такси.", reply_markup=reply_markup)

    elif "еда" in user_message:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Яндекс Еда🍔",  # Button text
                    web_app=WebAppInfo(url="https://eda.yandex.kz/en-kz/")  # Yandex Eda url
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Нажми на кнопку, чтобы заказать еду.", reply_markup=reply_markup)

# Handle feedback
async def ask_for_feedback(update: Update, context: CallbackContext):
    await update.message.reply_text('Пожалуйста, напишите ваш отзыв:')
    return FEEDBACK

async def receive_feedback(update: Update, context: CallbackContext):
    user_feedback = update.message.text
    user = update.message.from_user

    # Structure the feedback in a dictionary
    feedback_data = {
        "user_id": user.id,
        "username": user.username,
        "feedback": user_feedback
    }

    # Load existing feedback from the JSON file
    try:
        with open('feedback.json', 'r', encoding='utf-8') as f:
            feedback_list = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_list = []

    # Append the new feedback
    feedback_list.append(feedback_data)

    # Save the updated feedback list to the JSON file
    with open('feedback.json', 'w', encoding='utf-8') as f:
        json.dump(feedback_list, f, ensure_ascii=False, indent=4)

    # Acknowledge feedback submission
    await update.message.reply_text('Спасибо за ваш отзыв!')

    return ConversationHandler.END

# Handle text messages
async def handle_message(update: Update, context) -> None:
    user_message = update.message.text.lower()  # Ensure the message is lowercase

    if "такси" in user_message or "еда" in user_message:
        await send_web_app(update, context, user_message)  # Pass the user_message directly
    else:
        faq_answer = find_answer_in_faq_fuzzy(user_message)
        if faq_answer:
            await send_message(update, faq_answer)
        else:
            response_text = get_ai21_response(user_message)
            await send_message(update, response_text)

# Start command handler
async def start(update: Update, context):
    keyboard = [[KeyboardButton(text="📝 Написать отзыв")]]  # Feedback button in the custom keyboard
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text(
        text="Привет!👋 \nЯ — бот-помощник для приложения ЯндексGo.😊 \nМогу помочь с заказом ответив на твои вопросы, а также принять ваши отзывы и предложения. И даже могу заказать такси🚕 и еду🍔. \nНапишите свой запрос или отправьте голосовое сообщение🎤, чтобы получить помощь!",  # Opening message
        reply_markup=reply_markup
    )

# Start the Telegram bot
def start_telegram_bot():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register command and message handlers
    application.add_handler(CommandHandler('start', start))

    # Prioritize feedback first
    feedback_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('📝 Написать отзыв'), ask_for_feedback)],
        states={FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback)]},
        fallbacks=[]
    )
    application.add_handler(feedback_handler)

    # Web app handling (такси/еда)
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'(?i)такси|еда'), send_web_app))

    # Voice handling (audio transcription)
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Handle regular text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

# Main entry point
if __name__ == '__main__':
    init_db()  # Initialize the FAQ database
    start_telegram_bot()
