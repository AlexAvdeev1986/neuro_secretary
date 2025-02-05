# neuro_secretary
 neuro_secretary

Создайте виртуальное окружение
python -m venv venv

Активируйте виртуальное окружение

source venv/bin/activate

Шаг 1. Установка необходимых инструментов
youtube-dl или yt-dlp
Эти утилиты позволяют скачивать видео с различных платформ (YouTube, Vimeo и др.). Рекомендуется использовать yt-dlp – более активно поддерживаемый форк youtube-dl.

Используйте yt-dlp (или youtube-dl) для загрузки видео по его URL. Например, чтобы скачать видео с YouTube:
Пример команды:
bash
Копировать
Редактировать

yt-dlp https://www.youtube.com/watch?v=пример_идентификатора

ffmpeg
ffmpeg – мощный инструмент для обработки мультимедийных файлов, который позволит извлечь аудио из видео.
онвертация видео в аудио с помощью ffmpeg
После загрузки видео (например, получился файл video.mp4) можно извлечь аудиодорожку и сохранить её в нужном формате (например, MP3).
Пример команды для конвертации:
bash
Копировать
Редактировать

ffmpeg -i input_video.mp4 -vn -ar 44100 -ac 2 -b:a 192k output_audio.wav


# Установка yt-dlp (через pip)
pip install yt-dlp

# Установка ffmpeg (в Ubuntu)
sudo dnf update
sudo dnf install ffmpeg


1. Установка необходимых библиотек
Перед запуском кода установите необходимые библиотеки. Выполните в терминале следующие команды:

pip install python-dotenv

pip install openai python-telegram-bot whisper noisereduce numpy soundfile scipy pydub

Установите зависимости:
Выполните команду:

pip install noisereduce pydub numpy scipy openai git+https://github.com/openai/whisper.git


pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu


