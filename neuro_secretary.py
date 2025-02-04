import os
from dotenv import load_dotenv
import openai
import whisper
import noisereduce as nr
import soundfile as sf
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Загрузка переменных окружения из файла .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

WHISPER_MODEL = "base"  # Модель Whisper (base, small, medium, large)
GPT_MODEL = "gpt-4-turbo-preview"  # Модель GPT-4 Turbo

# Функция для очистки аудио от шумов
def clean_audio(input_file, output_file):
    # Загрузка аудио
    data, rate = sf.read(input_file)
    # Удаление шумов
    reduced_noise = nr.reduce_noise(y=data, sr=rate)
    # Сохранение очищенного аудио
    sf.write(output_file, reduced_noise, rate)

# Функция для распознавания речи с помощью Whisper
def transcribe_audio(audio_file):
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(audio_file)
    return result["text"]

# Функция для анализа текста с помощью GPT-4 Turbo
def analyze_text(text):
    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": "Проанализируй текст совещания. Выдели участников, вопросы, решения и ответственных."},
            {"role": "user", "content": text}
        ],
        temperature=0.2  # Низкая температура для точного анализа
    )
    return response['choices'][0]['message']['content']

# Функция для генерации протокола с помощью GPT-4 Turbo
def generate_protocol(analysis_result):
    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": "Создай протокол совещания на основе предоставленных данных."},
            {"role": "user", "content": analysis_result}
        ],
        temperature=0.5  # Умеренная температура для гибкости
    )
    return response['choices'][0]['message']['content']

# Обработчик сообщений в Telegram-боте
async def handle_audio(update: Update, context):
    # Получение аудиофайла от пользователя
    file = await update.message.audio.get_file()
    await file.download_to_drive("input_audio.wav")

    # Очистка аудио
    clean_audio("input_audio.wav", "cleaned_audio.wav")

    # Распознавание речи
    transcript = transcribe_audio("cleaned_audio.wav")

    # Анализ текста
    analysis_result = analyze_text(transcript)

    # Генерация протокола
    protocol = generate_protocol(analysis_result)

    # Отправка протокола пользователю
    await update.message.reply_text(protocol)

# Запуск Telegram-бота
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.run_polling()

if __name__ == "__main__":
    main()
