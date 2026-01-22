import os
import logging
from telebot import TeleBot, types
import threading
import time
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация бота
BOT_TOKEN = '8460003790:AAEgZ2FUSEAJ9IPysnC6eB9B9TaY5Hhg1Qo'
ADMIN_ID = 5780499255

# Пути для хранения данных
DATA_DIR = Path(__file__).parent / 'bot_data'
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / 'support_bot.db'

# Инициализация бота
bot = TeleBot(BOT_TOKEN)


class Database:
    """Класс для работы с базой данных SQLite"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица вопросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_text TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                answered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица ответов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                admin_id INTEGER,
                answer_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
        ''')

        # Таблица состояний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                state TEXT,
                data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_user(self, user_id, username, first_name, last_name):
        """Сохранение/обновление пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))

        conn.commit()
        conn.close()

    def save_question(self, user_id, question_text):
        """Сохранение вопроса"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO questions (user_id, question_text)
            VALUES (?, ?)
        ''', (user_id, question_text))

        question_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return question_id

    def save_answer(self, question_id, admin_id, answer_text):
        """Сохранение ответа"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO answers (question_id, admin_id, answer_text)
            VALUES (?, ?, ?)
        ''', (question_id, admin_id, answer_text))

        # Обновляем статус вопроса
        cursor.execute('''
            UPDATE questions 
            SET status = 'answered', answered_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (question_id,))

        conn.commit()
        conn.close()

    def get_user_state(self, user_id):
        """Получение состояния пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT state, data FROM user_states WHERE user_id = ?
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {'state': result[0], 'data': json.loads(result[1]) if result[1] else {}}
        return None

    def set_user_state(self, user_id, state, data=None):
        """Установка состояния пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data_json = json.dumps(data) if data else None

        cursor.execute('''
            INSERT OR REPLACE INTO user_states (user_id, state, data)
            VALUES (?, ?, ?)
        ''', (user_id, state, data_json))

        conn.commit()
        conn.close()

    def clear_user_state(self, user_id):
        """Очистка состояния пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM user_states WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def get_stats(self):
        """Получение статистики"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM questions')
        total_questions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questions WHERE status = 'pending'")
        pending_questions = cursor.fetchone()[0]

        conn.close()

        return {
            'total_users': total_users,
            'total_questions': total_questions,
            'pending_questions': pending_questions
        }


# Инициализация базы данных
db = Database(DB_PATH)

# Словари для хранения состояний (для обратной совместимости)
user_states = {}
user_questions = {}
admin_responses = {}


def run_bot():
    """Запуск бота в отдельном потоке"""
    logger.info("Запуск Telegram бота...")
    bot.polling(none_stop=True, interval=1)


@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    # Сохраняем пользователя в БД
    db.save_user(user_id, username, first_name, last_name)

    welcome_text = f"Привет, {username}! 👋\nЯ - бот поддержки проекта 'Мои достижения'!\nПомогу тебе получить ответ на твой вопрос!"

    # Создаем клавиатуру
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('📝 Новое сообщение'))
    keyboard.add(types.KeyboardButton('❓ Частые вопросы'))
    keyboard.add(types.KeyboardButton('ℹ️ О проекте'))

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=keyboard
    )

    # Очищаем состояние пользователя
    db.clear_user_state(user_id)

    # Для обратной совместимости
    user_states.pop(user_id, None)

    logger.info(f"Новый пользователь: {user_id} ({username})")


@bot.message_handler(func=lambda message: message.text == '📝 Новое сообщение')
def handle_new_message(message):
    """Обработка кнопки 'Новое сообщение'"""
    user_id = message.from_user.id

    # Сохраняем состояние в БД
    db.set_user_state(user_id, 'waiting_for_question')

    # Для обратной совместимости
    user_states[user_id] = 'waiting_for_question'

    bot.send_message(
        message.chat.id,
        "Напишите ваш вопрос или сообщение для поддержки:",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(func=lambda message: message.text == '❓ Частые вопросы')
def handle_faq(message):
    """Обработка кнопки 'Частые вопросы'"""
    faq_text = """
    ❓ *Частые вопросы:*

    *1. Как зарегистрироваться?*
    Нажмите кнопку "Начать бесплатно" на главной странице.

    *2. Как добавить достижение?*
    В личном кабинете нажмите "+ Добавить достижение".

    *3. Как связаться с поддержкой?*
    Используйте кнопку "📝 Новое сообщение".

    *4. Можно ли удалить профиль?*
    Да, в настройках профиля есть эта опция.

    *5. Бесплатно ли использование?*
    Да, все основные функции бесплатны.
    """

    bot.send_message(
        message.chat.id,
        faq_text,
        parse_mode='Markdown'
    )


@bot.message_handler(func=lambda message: message.text == 'ℹ️ О проекте')
def handle_about(message):
    """Обработка кнопки 'О проекте'"""
    about_text = """
    *О проекте "Мои достижения":*

    🎓 *Цель:* Создание цифрового портфолио для учащихся.

    📊 *Возможности:*
    • Добавление достижений и наград
    • Отслеживание прогресса
    • Создание классов и групп
    • Генерация отчетов

    🌐 *Сайт:* [Мои достижения 444](https://ваш-сайт.ru)

    📞 *Поддержка:* @ваш_bot_поддержки
    """

    bot.send_message(
        message.chat.id,
        about_text,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


@bot.message_handler(func=lambda message: db.get_user_state(message.from_user.id) and
                                          db.get_user_state(message.from_user.id)['state'] == 'waiting_for_question')
def handle_question_input(message):
    """Обработка ввода вопроса пользователем"""
    user_id = message.from_user.id
    question_text = message.text

    # Сохраняем вопрос в БД
    question_id = db.save_question(user_id, question_text)

    # Сохраняем в памяти для обратной совместимости
    user_questions[user_id] = {
        'text': question_text,
        'username': message.from_user.username or message.from_user.first_name,
        'user_id': user_id,
        'question_id': question_id
    }

    # Сохраняем состояние в БД
    db.set_user_state(user_id, 'confirm_question', {
        'question_id': question_id,
        'question_text': question_text
    })

    # Для обратной совместимости
    user_states[user_id] = 'confirm_question'

    # Создаем inline-клавиатуру для подтверждения
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✅ Да, отправить", callback_data=f"confirm_question_{question_id}"),
        types.InlineKeyboardButton("✏️ Изменить", callback_data=f"edit_question_{user_id}")
    )

    bot.send_message(
        message.chat.id,
        f"*Ваш вопрос:*\n{question_text}\n\nОтправить вопрос поддержке?",
        parse_mode='Markdown',
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_question_'))
def handle_question_confirmation(call):
    """Подтверждение отправки вопроса админу"""
    question_id = int(call.data.split('_')[-1])
    user_id = call.from_user.id

    # Получаем данные из БД или памяти
    user_state = db.get_user_state(user_id)
    if user_state and user_state['data'].get('question_id') == question_id:
        question_text = user_state['data'].get('question_text', '')
        username = call.from_user.username or call.from_user.first_name
    elif user_id in user_questions:
        # Для обратной совместимости
        question_data = user_questions[user_id]
        question_text = question_data['text']
        username = question_data['username']
    else:
        bot.answer_callback_query(call.id, "❌ Вопрос не найден.")
        return

    # Отправляем вопрос админу
    admin_message = f"❓ *Новый вопрос от пользователя*\n\n"
    admin_message += f"👤 *Пользователь:* @{username} (ID: {user_id})\n"
    admin_message += f"📝 *Вопрос:*\n{question_text}\n\n"
    admin_message += f"🔢 *ID вопроса:* #{question_id}"

    # Создаем inline-клавиатуру для ответа
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("📨 Ответить", callback_data=f"answer_user_{question_id}")
    )

    try:
        bot.send_message(
            ADMIN_ID,
            admin_message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

        # Уведомляем пользователя
        bot.answer_callback_query(call.id, "✅ Вопрос отправлен поддержке!")
        bot.edit_message_text(
            "✅ Ваш вопрос отправлен поддержке. Мы ответим вам в ближайшее время!",
            call.message.chat.id,
            call.message.message_id
        )

        # Возвращаем основную клавиатуру
        keyboard_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard_main.add(types.KeyboardButton('📝 Новое сообщение'))
        keyboard_main.add(types.KeyboardButton('❓ Частые вопросы'))
        keyboard_main.add(types.KeyboardButton('ℹ️ О проекте'))

        bot.send_message(
            user_id,
            "Чем еще могу помочь?",
            reply_markup=keyboard_main
        )

        # Очищаем состояния
        db.clear_user_state(user_id)
        if user_id in user_states:
            user_states.pop(user_id)
        if user_id in user_questions:
            user_questions.pop(user_id)

        logger.info(f"Вопрос #{question_id} от {user_id} отправлен админу")

    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка отправки. Попробуйте позже.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('answer_user_'))
def handle_answer_button(call):
    """Админ нажал кнопку 'Ответить'"""
    question_id = int(call.data.split('_')[-1])
    admin_id = call.from_user.id

    # Получаем информацию о вопросе
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, question_text FROM questions WHERE id = ?', (question_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        target_user_id, question_text = result

        # Сохраняем состояние админа в БД
        db.set_user_state(admin_id, 'admin_waiting_response', {
            'question_id': question_id,
            'target_user_id': target_user_id,
            'question_text': question_text
        })

        # Для обратной совместимости
        admin_responses[admin_id] = {
            'target_user_id': target_user_id,
            'question_id': question_id,
            'question_text': question_text
        }
        user_states[admin_id] = 'admin_waiting_response'

        bot.send_message(
            admin_id,
            f"💬 Введите ответ для пользователя (вопрос: \"{question_text[:50]}...\"):",
            reply_markup=types.ForceReply(selective=True)
        )

        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, "❌ Вопрос не найден.")


@bot.message_handler(func=lambda message: db.get_user_state(message.from_user.id) and
                                          db.get_user_state(message.from_user.id)['state'] == 'admin_waiting_response')
def handle_admin_response(message):
    """Обработка ответа от админа"""
    admin_id = message.from_user.id

    user_state = db.get_user_state(admin_id)
    if user_state:
        question_id = user_state['data'].get('question_id')
        target_user_id = user_state['data'].get('target_user_id')
        question_text = user_state['data'].get('question_text', '')
        response_text = message.text

        # Сохраняем ответ для подтверждения
        db.set_user_state(admin_id, 'admin_confirm_response', {
            'question_id': question_id,
            'target_user_id': target_user_id,
            'question_text': question_text,
            'response_text': response_text
        })

        # Для обратной совместимости
        if admin_id in admin_responses:
            admin_responses[admin_id]['response_text'] = response_text
        user_states[admin_id] = 'admin_confirm_response'

        # Создаем inline-клавиатуру для подтверждения
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Да, отправить", callback_data=f"send_response_{question_id}"),
            types.InlineKeyboardButton("✏️ Изменить", callback_data=f"edit_response_{question_id}")
        )

        bot.send_message(
            admin_id,
            f"*Ваш ответ:*\n{response_text}\n\nОтправить пользователю?",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        bot.send_message(admin_id, "❌ Ошибка. Попробуйте снова.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('send_response_'))
def handle_send_response(call):
    """Подтверждение отправки ответа пользователю"""
    question_id = int(call.data.split('_')[-1])
    admin_id = call.from_user.id

    # Получаем данные из БД
    user_state = db.get_user_state(admin_id)

    if user_state and user_state['data'].get('question_id') == question_id:
        response_text = user_state['data'].get('response_text', '')
        target_user_id = user_state['data'].get('target_user_id')
        question_text = user_state['data'].get('question_text', '')
    elif admin_id in admin_responses and admin_responses[admin_id].get('question_id') == question_id:
        # Для обратной совместимости
        response_text = admin_responses[admin_id].get('response_text', '')
        target_user_id = admin_responses[admin_id].get('target_user_id')
        question_text = admin_responses[admin_id].get('question_text', '')
    else:
        bot.answer_callback_query(call.id, "❌ Ответ не найден.")
        return

    try:
        # Сохраняем ответ в БД
        db.save_answer(question_id, admin_id, response_text)

        # Форматируем ответ в нужном формате
        user_message = (
            f"📨 Ответ от поддержки:\n\n"
            f"<i>\"{question_text}\"</i>\n\n"
            f"{response_text}\n\n"
            f"Если у вас остались вопросы, напишите нам снова."
        )

        # Отправляем ответ пользователю
        bot.send_message(
            target_user_id,
            user_message,
            parse_mode='HTML'
        )

        # Уведомляем админа
        bot.answer_callback_query(call.id, "✅ Ответ отправлен!")
        bot.edit_message_text(
            f"✅ Ответ отправлен пользователю ID: {target_user_id}",
            call.message.chat.id,
            call.message.message_id
        )

        # Очищаем состояния
        db.clear_user_state(admin_id)
        if admin_id in user_states:
            user_states.pop(admin_id)
        if admin_id in admin_responses:
            admin_responses.pop(admin_id)

        logger.info(f"Ответ от админа {admin_id} отправлен пользователю {target_user_id}")

    except Exception as e:
        logger.error(f"Ошибка отправки пользователю: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка отправки. Пользователь заблокировал бота.")


@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Обработка всех остальных сообщений"""
    if message.from_user.id == ADMIN_ID:
        # Для админа - простое эхо
        bot.send_message(
            message.chat.id,
            "Используйте кнопки для управления или отвечайте на вопросы через inline-кнопки."
        )
    else:
        # Для пользователей - возвращаем основное меню
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton('📝 Новое сообщение'))
        keyboard.add(types.KeyboardButton('❓ Частые вопросы'))
        keyboard.add(types.KeyboardButton('ℹ️ О проекте'))

        bot.send_message(
            message.chat.id,
            "Выберите действие из меню:",
            reply_markup=keyboard
        )


def start_bot():
    """Запуск бота в фоновом потоке"""
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Telegram бот запущен в фоновом режиме")


if __name__ == '__main__':
    print("=" * 50)
    print("🤖 ЗАПУСК ТЕЛЕГРАМ БОТА ПОДДЕРЖКИ")
    print("=" * 50)
    print(f"Токен бота: {BOT_TOKEN[:10]}...")
    print(f"ID администратора: {ADMIN_ID}")
    print(f"База данных: {DB_PATH}")
    print("=" * 50)

    try:
        # Запуск бота в отдельном потоке
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()

        print("✅ Бот запущен успешно!")
        print("📱 Перейдите в Telegram и найдите своего бота")
        print("⏳ Бот работает в фоновом режиме...")
        print("=" * 50)

        # Держим программу активной
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")