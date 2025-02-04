import os
import logging
import hashlib
from dotenv import load_dotenv
import openai
import whisper
import noisereduce as nr
import soundfile as sf
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Настройка логгера
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Конфигурация моделей
WHISPER_MODEL = whisper.load_model("base")  # Однократная загрузка модели
GPT_MODEL = "gpt-4-turbo-preview"
MAX_AUDIO_DURATION = 60 * 60 * 2  # 2 часа

def clean_audio(input_file: str, output_file: str) -> None:
    """Очистка аудио от шумов с обработкой исключений"""
    try:
        data, rate = sf.read(input_file)
        if len(data) == 0:
            raise ValueError("Пустой аудиофайл")
            
        reduced_noise = nr.reduce_noise(y=data, sr=rate)
        sf.write(output_file, reduced_noise, rate)
    except Exception as e:
        logger.error(f"Ошибка очистки аудио: {e}")
        raise

def transcribe_audio(audio_file: str) -> str:
    """Транскрибация аудио с проверкой длительности"""
    try:
        info = sf.info(audio_file)
        if info.duration > MAX_AUDIO_DURATION:
            raise ValueError(f"Аудио слишком длинное ({info.duration}s > {MAX_AUDIO_DURATION}s)")
            
        result = WHISPER_MODEL.transcribe(audio_file)
        return result["text"]
    except Exception as e:
        logger.error(f"Ошибка транскрибации: {e}")
        raise

def analyze_text(text: str) -> str:
    """Анализ текста с обработкой ошибок API"""
    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "Проанализируй текст совещания. Выдели участников, вопросы, решения и ответственных."},
                {"role": "user", "content": text}
            ],
            temperature=0.2,
            max_tokens=3000
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Ошибка анализа текста: {e}")
        raise

def generate_protocol(analysis_result: str) -> str:
    """Генерация протокола с кэшированием"""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Генерация хеша для кэширования
    hash_object = hashlib.md5(analysis_result.encode())
    cache_file = os.path.join(cache_dir, f"{hash_object.hexdigest()}.txt")
    
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return f.read()
    
    try:
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "Создай протокол совещания на основе предоставленных данных."},
                {"role": "user", "content": analysis_result}
            ],
            temperature=0.5,
            max_tokens=3000
        )
        result = response['choices'][0]['message']['content']
        
        with open(cache_file, "w") as f:
            f.write(result)
            
        return result
    except Exception as e:
        logger.error(f"Ошибка генерации протокола: {e}")
        raise

async def handle_audio(update: Update, context) -> None:
    """Обработчик аудио с полной обработкой ошибок"""
    try:
        user = update.message.from_user
        logger.info(f"Получено аудио от {user.username} ({user.id})")
        
        file = await update.message.audio.get_file()
        file_hash = hashlib.md5(file.file_id.encode()).hexdigest()
        input_file = f"temp_{file_hash}.wav"
        
        await file.download_to_drive(input_file)
        
        # Очистка и обработка аудио
        clean_audio(input_file, input_file)
        transcript = transcribe_audio(input_file)
        
        # Анализ и генерация
        analysis = analyze_text(transcript)
        protocol = generate_protocol(analysis)
        
        # Отправка результата
        await update.message.reply_text(
            f"✅ Протокол успешно сгенерирован:\n\n{protocol}",
            parse_mode="Markdown"
        )
        
        # Очистка временных файлов
        os.remove(input_file)
        
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке файла. Пожалуйста, попробуйте позже.")

async def start(update: Update, context) -> None:
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🤖 Добро пожаловать в NeuroSecretary!\n\n"
        "Отправьте аудиофайл с записью совещания, и я сгенерирую протокол."
    )

def main() -> None:
    """Запуск приложения"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    
    application.run_polling()
    logger.info("Бот успешно запущен")

if __name__ == "__main__":
    main()