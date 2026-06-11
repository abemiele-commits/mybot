# 🤖 Telegram AI-Ассистент на Claude

Полнофункциональный бот с памятью, личностью и поддержкой медиафайлов.

## Возможности
- 💬 Отвечает на любые вопросы (помнит контекст до 20 сообщений)
- 🖼️ Анализирует изображения
- 📄 Читает PDF и текстовые файлы
- 🎭 Имеет личность (настраивается в `SYSTEM_PROMPT`)

---

## Быстрый старт

### 1. Получи токены

**Telegram:**
1. Открой [@BotFather](https://t.me/BotFather)
2. Напиши `/newbot` → придумай имя → получи токен

**Anthropic:**
1. Зайди на [console.anthropic.com](https://console.anthropic.com)
2. API Keys → Create Key → скопируй

### 2. Установи зависимости

```bash
pip install -r requirements.txt
```

### 3. Задай переменные окружения

```bash
# Linux/Mac
export TELEGRAM_TOKEN="твой_токен"
export ANTHROPIC_API_KEY="твой_ключ"

# Windows (PowerShell)
$env:TELEGRAM_TOKEN="твой_токен"
$env:ANTHROPIC_API_KEY="твой_ключ"
```

Или создай файл `.env` (скопируй `.env.example`) и используй `python-dotenv`.

### 4. Запусти

```bash
python bot.py
```

---

## Кастомизация

Открой `bot.py` и отредактируй `SYSTEM_PROMPT` — это личность бота.
Можешь сделать его кем угодно: репетитором, юмористом, строгим ментором.

---

## Деплой в облако (бесплатно)

### Railway.app
1. Залей код на GitHub
2. Зайди на [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Добавь переменные окружения в настройках
4. Готово — бот работает 24/7!

### Render.com
1. Создай Web Service → выбери репозиторий
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python bot.py`
4. Добавь переменные окружения → Deploy

---

## Команды бота

| Команда | Действие |
|---------|----------|
| `/start` | Приветствие и инструкция |
| `/clear` | Очистить память диалога |
| `/help` | Список возможностей |
