import sys
import os
import logging
import hashlib
import asyncio
from dotenv import load_dotenv
import openai
import whisper
import yt_dlp
import numpy as np
import noisereduce as nr
import soundfile as sf
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Настройка окружения
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Конфигурация
WHISPER_MODEL = "base"
GPT_MODEL = "gpt-4-turbo"
MAX_DURATION = 2 * 60 * 60  # 2 часа
AUDIO_CACHE = "audio_cache"
os.makedirs(AUDIO_CACHE, exist_ok=True)

# Настройка логгера
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AudioProcessor:
    @staticmethod
    def download_youtube_audio(url: str) -> str:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': os.path.join(AUDIO_CACHE, '%(id)s.%(ext)s'),
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info).replace(".webm", ".wav")

    @staticmethod
    def clean_audio(input_path: str) -> str:
        try:
            data, rate = sf.read(input_path)
            if len(data) == 0:
                raise ValueError("Empty audio file")
            
            reduced_noise = nr.reduce_noise(y=data, sr=rate)
            output_path = input_path.replace(".wav", "_cleaned.wav")
            sf.write(output_path, reduced_noise, rate)
            return output_path
        except Exception as e:
            logger.error(f"Audio cleaning failed: {e}")
            raise

class MeetingProcessor:
    def __init__(self):
        self.whisper = whisper.load_model(WHISPER_MODEL)
        
    def transcribe(self, audio_path: str) -> str:
        try:
            result = self.whisper.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    @staticmethod
    def analyze_text(text: str) -> str:
        try:
            response = openai.chat.completions.create(
                model=GPT_MODEL,
                messages=[{
                    "role": "system",
                    "content": """Проанализируй текст совещания. Выдели:
1. Участники (имя/роль)
2. Основные вопросы
3. Принятые решения
4. Ответственных и сроки"""
                }, {
                    "role": "user",
                    "content": text
                }],
                temperature=0.2,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            raise

    @staticmethod
    def generate_protocol(analysis: str) -> str:
        try:
            response = openai.chat.completions.create(
                model=GPT_MODEL,
                messages=[{
                    "role": "system",
                    "content": """Создай официальный протокол совещания по шаблону:
Участники: [список]
Повестка: [список вопросов]
Решения:
1. [текст] (Ответственный: [имя], Срок: [дата])
..."""
                }, {
                    "role": "user",
                    "content": analysis
                }],
                temperature=0.5,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Protocol generation failed: {e}")
            raise

async def handle_audio(update: Update, context):
    try:
        user = update.message.from_user
        logger.info(f"Processing audio from {user.username}")

        # Скачивание файла
        audio_file = await update.message.audio.get_file()
        file_hash = hashlib.md5(audio_file.file_id.encode()).hexdigest()
        input_path = os.path.join(AUDIO_CACHE, f"{file_hash}.wav")
        await audio_file.download_to_drive(input_path)

        # Обработка
        cleaned_path = AudioProcessor.clean_audio(input_path)
        processor = MeetingProcessor()
        transcript = processor.transcribe(cleaned_path)
        analysis = processor.analyze_text(transcript)
        protocol = processor.generate_protocol(analysis)

        # Отправка результата
        await update.message.reply_text(f"✅ Протокол готов:\n\n{protocol}")
        
        # Очистка кэша
        os.remove(input_path)
        os.remove(cleaned_path)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await update.message.reply_text("❌ Ошибка обработки файла")

async def handle_youtube(update: Update, context):
    try:
        url = update.message.text
        if "youtube.com" not in url and "youtu.be" not in url:
            await update.message.reply_text("❌ Это не YouTube ссылка")
            return

        # Скачивание аудио
        audio_path = AudioProcessor.download_youtube_audio(url)
        
        # Обработка
        processor = MeetingProcessor()
        transcript = processor.transcribe(audio_path)
        analysis = processor.analyze_text(transcript)
        protocol = processor.generate_protocol(analysis)

        # Отправка результата
        await update.message.reply_text(f"🎥 Протокол из YouTube-видео:\n\n{protocol}")
        
        # Очистка
        os.remove(audio_path)

    except Exception as e:
        logger.error(f"YouTube error: {str(e)}")
        await update.message.reply_text("❌ Ошибка обработки YouTube видео")

async def start(update: Update, context):
    await update.message.reply_text(
        "🤖 Нейро-секретарь готов к работе!\n\n"
        "Отправьте:\n"
        "• Аудиофайл с записью совещания\n"
        "• Ссылку на YouTube видео\n\n"
        "Я сгенерирую структурированный протокол!"
    )

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube))

    # Запуск бота
    application.run_polling()
    logger.info("Бот запущен")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
