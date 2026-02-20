import os
import json
import requests
import logging
from datetime import datetime
import telegram
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY')
CITY = os.environ.get('CITY', 'Moscow')

# Загрузка расписания
def load_schedule():
    """Загружает расписание из JSON-файла"""
    try:
        with open('schedule.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки расписания: {e}")
        return {}

# Получение погоды
def get_weather():
    """Получает текущую погоду через OpenWeatherMap API"""
    if not WEATHER_API_KEY:
        return "погода временно недоступна"
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&APPID={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        
        # Определяем осадки
        weather_main = data['weather'][0]['main'].lower()
        if 'rain' in weather_main or 'drizzle' in weather_main:
            precipitation = "🌧 дождь"
        elif 'snow' in weather_main:
            precipitation = "🌨 снег"
        elif 'cloud' in weather_main:
            precipitation = "☁️ облачно"
        else:
            precipitation = "☀️ ясно"
        
        return f"{temp:.0f}°C, {precipitation}"
    except Exception as e:
        logger.error(f"Ошибка получения погоды: {e}")
        return "погода временно недоступна"

# Получение расписания на сегодня
def get_today_schedule():
    """Возвращает список предметов на сегодня"""
    schedule = load_schedule()
    
    # Определяем день недели
    weekday_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    today_idx = datetime.now().weekday()  # 0 = понедельник
    today_name = weekday_names[today_idx]
    
    return schedule.get(today_name, [])

# Форматирование сообщения с расписанием
def format_schedule_message(lessons):
    """Формирует сообщение со списком предметов"""
    if not lessons:
        return "📚 Сегодня пар нет! Можно отдыхать 😎"
    
    message = "📚 *Сегодняшние пары:*\n\n"
    for i, lesson in enumerate(lessons, 1):
        message += f"• {lesson}\n"
    
    return message

# Отправка сообщения и опроса
async def send_daily_update():
    """Основная функция отправки утреннего обновления"""
    try:
        # Инициализация бота
        bot = telegram.Bot(token=BOT_TOKEN)
        
        # Получаем погоду
        weather = get_weather()
        
        # Получаем расписание на сегодня
        lessons = get_today_schedule()
        has_lessons = len(lessons) > 0
        
        # Формируем приветствие
        greeting = f"🌅 *ДОБРОЕ УТРО, РЕБЯТА!*\n\n🌡 Погода сегодня: {weather}\n"
        
        # Добавляем расписание
        schedule_text = format_schedule_message(lessons)
        full_message = greeting + "\n" + schedule_text
        
        # Отправляем текстовое сообщение
        await bot.send_message(
            chat_id=CHAT_ID,
            text=full_message,
            parse_mode='Markdown'
        )
        logger.info("Текстовое сообщение отправлено")
        
        # Отправляем опрос в зависимости от наличия пар
        if has_lessons:
            # Опрос про пары
            poll_question = "КТО ПОЙДЕТ НА ПАРЫ?"
            poll_options = ["Точно планирую 👍", "Может быть 🤔", "Точно не планирую 👎"]
        else:
            # Опрос про газ
            poll_question = "ГАЗ коворк сегодня?"
            poll_options = ["ГАЗ 🚀", "Может быть 🤔", "ТОЧНО НЕТ ❌"]
        
        await bot.send_poll(
            chat_id=CHAT_ID,
            question=poll_question,
            options=poll_options,
            is_anonymous=False,
            allows_multiple_answers=False
        )
        logger.info("Опрос отправлен")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке: {e}")

# Запуск
if __name__ == "__main__":
    asyncio.run(send_daily_update())
