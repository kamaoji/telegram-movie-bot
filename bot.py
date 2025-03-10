import telebot
import requests
import sqlite3
from flask import Flask, request

TOKEN = "7329061875:AAHzWDlUqd3UuS5xSz5unCR1zxE3FRV6BDc"
CHANNEL_ID = "@DESIARUNGAMERS"  # Telegram चैनल का username
TMDB_API_KEY = "153c207d50b2dc4ec3f756b7143154f7"  # TMDb से API Key लें

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# SQLite Database सेटअप
conn = sqlite3.connect("movies.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS movies (id INTEGER PRIMARY KEY, name TEXT, link TEXT)")
conn.commit()

# --- Channel Join Verification ---
def is_user_joined(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- मूवी सर्च और डाउनलोड लिंक ---
def search_movie(query):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(url).json()
    
    if response["results"]:
        movie = response["results"][0]
        title = movie["title"]
        poster = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        return title, poster, f"https://www.google.com/search?q={title}+movie+download"
    return None, None, None

# --- Telegram Bot Command Handlers ---
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    
    if not is_user_joined(user_id):
        bot.send_message(user_id, f"🚀 पहले हमारे चैनल को जॉइन करें: {CHANNEL_ID}")
        return
    
    bot.send_message(user_id, "🎬 मूवी का नाम भेजें और डाउनलोड लिंक पाएं!")

@bot.message_handler(commands=["addmovie"])
def add_movie(message):
    try:
        _, name, link = message.text.split(" ", 2)
        cursor.execute("INSERT INTO movies (name, link) VALUES (?, ?)", (name, link))
        conn.commit()
        bot.send_message(message.chat.id, "✅ मूवी जोड़ी गई!")
    except:
        bot.send_message(message.chat.id, "⚠️ सही फॉर्मेट में भेजें: `/addmovie मूवी_नाम डाउनलोड_लिंक`")

@bot.message_handler(func=lambda message: True)
def search_and_send_movie(message):
    user_id = message.chat.id
    
    if not is_user_joined(user_id):
        bot.send_message(user_id, f"🚀 पहले हमारे चैनल को जॉइन करें: {CHANNEL_ID}")
        return

    query = message.text
    title, poster, link = search_movie(query)
    
    if title:
        bot.send_photo(user_id, poster, caption=f"🎥 {title}\n🔗 डाउनलोड: {link}")
    else:
        bot.send_message(user_id, "❌ मूवी नहीं मिली!")

# --- Flask Server (Render पर होस्ट करने के लिए) ---
@app.route('/')
def home():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "OK", 200

# --- बॉट स्टार्ट करें ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

