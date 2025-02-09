Whisper от OpenAI – это мощная модель распознавания речи, и её можно использовать через терминал с помощью `whisper` или `whisper.cpp`. В зависимости от того, какой вариант вы хотите использовать, шаги немного различаются.

---

### 1. Использование `openai/whisper` (Python)
#### Установка:
```bash
pip install openai-whisper
```
Если у вас нет `ffmpeg`, установите его:
```bash
sudo dnf install ffmpeg  # для Linux
brew install ffmpeg      # для macOS
```

ffmpeg -i audio.mp4 -vn -ar 44100 -ac 2 -b:a 192k output_audio.wav

#### Использование:
Распознавание аудио:
```bash
whisper audio.mp3 --model large
```
Где:
- `audio.mp3` – ваш аудиофайл
- `--model small` – модель (`tiny`, `base`, `small`, `medium`, `large`)

Дополнительные параметры:
- `--language ru` – задаёт язык (по умолчанию определяется автоматически)
- `--task translate` – перевод на английский
- `--output_format txt` – сохраняет результат в текстовый файл

---

### 2. Использование `whisper.cpp` (быстрее, использует CPU/GPU)
Этот вариант легче и быстрее, так как написан на C++.

#### Установка:
```bash
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
```
Скачивание модели (например, `small`):
```bash
./models/download-ggml-model.sh small
```

#### Использование:
```bash
./main -m models/ggml-small.bin -f audio.mp3 -l ru
```
Где:
- `-m` – путь к модели
- `-f` – ваш аудиофайл
- `-l` – язык (например, `ru`)

Вы также можете использовать GPU:
```bash
./main -m models/ggml-small.bin -f audio.mp3 -l ru -t 8 -c 1
```
(где `-t 8` – количество потоков, `-c 1` – использование GPU)

