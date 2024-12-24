import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram import F
from rag.main import PsychoRag

# Initialize the SQLite database
conn = sqlite3.connect('conversations.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        user_id INTEGER,
        speaker TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Initialize the PsychoRag system
VECTOR_DB_PATHS = {
    "transcriptions": "/Users/dtikhanovskii/Documents/phycho_rag/data/vectorstore/transcriptions_db_2",
    "books": "/Users/dtikhanovskii/Documents/phycho_rag/data/vectorstore/books_db_2" # дальше добавить папочку с статьями!!!
}

psycho_rag = PsychoRag(vector_db_paths=VECTOR_DB_PATHS)

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize bot and dispatcher
API_TOKEN = '7178471991:AAEyGBGLo1LQMfVIj9q5rO_dlxZoam4qLzE'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(F.command('start'))
async def send_welcome(message: types.Message):
    await message.reply("Welcome to the PsychoRag chatbot. Type /end to stop the session.")

@dp.message(F.command('end'))
async def end_session(message: types.Message):
    user_id = message.from_user.id
    await message.reply("Ending session...")
    report = await psycho_rag.end_session(user_id)
    await message.reply(f"Session Summary:\n{report}")

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_input = message.text

    # Save user input to the database
    cursor.execute('INSERT INTO conversations (user_id, speaker, message) VALUES (?, ?, ?)',
                   (user_id, 'User', user_input))
    conn.commit()

    # Get assistant response
    response = await psycho_rag.ask(user_id, user_input)

    # Save assistant response to the database
    cursor.execute('INSERT INTO conversations (user_id, speaker, message) VALUES (?, ?, ?)',
                   (user_id, 'Assistant', response))
    conn.commit()

    await message.reply(response)

if __name__ == '__main__':
    # Start polling with the updated method
    dp.run_polling(bot)
