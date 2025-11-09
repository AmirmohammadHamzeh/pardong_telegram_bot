# 🤖 Pardong Telegram Bot

> **A lightweight Telegram frontend** for [Pardong](https://github.com/AmirmohammadHamzeh/pardong) — a FastAPI-based shared expense manager.  
> This bot allows users to interact with the Pardong backend directly from Telegram, enabling easy expense tracking and group payments — all via chat.

---

## 📋 Table of Contents
- [About the Project](#-about-the-project)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 💡 About the Project

**Pardong Telegram Bot** is the Telegram interface for the main [Pardong](https://github.com/AmirmohammadHamzeh/pardong) project —  
a modern expense-splitting system designed for students, roommates, and friends who share costs.

The bot communicates with the Pardong backend’s RESTful APIs to:
- Register and authenticate users  
- Create and manage shared purchases  
- Track payments  
- Display settlement statuses  

Built with **Python** and **python-telegram-bot**, and easily deployable with Docker using **polling** (no webhook or SSL required).

---

## ✨ Features

✅ Seamless integration with the Pardong FastAPI backend  
✅ Polling-based Telegram bot (no external hosting needed)  
✅ Dockerized setup for instant deployment  
✅ Simple `.env` configuration for the bot token and API URL  
✅ Clean, modular Python code  

---

## 🧰 Tech Stack

**Language:** Python  
**Library:** python-telegram-bot  
**Backend:** [Pardong (FastAPI)](https://github.com/AmirmohammadHamzeh/pardong)  
**Deployment:** Docker  

---

## ⚙️ Installation
### 🐳 Dockerized Setup

> Run the bot using Docker — no Python installation required.

```bash
# 1️⃣ Clone the repository
git clone https://github.com/yourusername/pardong-telegram-bot.git

# 2️⃣ Navigate into the project folder
cd pardong-telegram-bot

# 3️⃣ Build the Docker image
docker build -t pardong-telegram-bot .

# 4️⃣ Run the bot container
docker run -d \
  --name pardong-bot \
  --env BOT_TOKEN=your_bot_token_here \
  --env API_URL=https://your-pardong-backend-url.com \
  pardong-telegram-bot

# 5️⃣ View logs
docker logs -f pardong-bot
```
### .env.example

```
BOT_TOKEN=your_telegram_bot_token
API_URL=https://your-pardong-backend-url.com
REDIS_HOST=your_redis_host
REDIS_PORT=6379
```
### ⚠️ Important:

	•Rename .env.example to .env and fill in your own values.

	•Do not commit .env to GitHub.

---

## 🚀 Usage

### Once running:
	•Open Telegram and start a chat with your bot
	•Register or log in (the bot talks to the Pardong backend)
	•Manage your shared expenses directly from Telegram



---
## 🖼 Screenshots

Coming soon…
(You can add Telegram chat screenshots or Docker logs screenshots here.)

---

## 🤝 Contributing

Contributions, bug reports, and ideas are always welcome!

### To contribute:
	1.Fork the project
	2.Create a new branch (git checkout -b feature-name)
	3.Make your changes
	4.Commit and push
	5.Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License — feel free to use, modify, and distribute.

---

## 📬 Contact

Author: Amir Mohammad Hamzeh
📧 Email: amirmohammadhamzeh@outlook.com
🌐 GitHub: AmirMohammadHamzeh
🧩 Main Project: [Pardong (FastAPI Backend)](https://github.com/AmirmohammadHamzeh/pardong)
