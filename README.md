# Yoga Scheduler Bot 🧘‍♂️

Telegram bot for automating the scheduling of group yoga sessions and plank challenges across different time zones.

## 🎯 Project Goal

Simplify the coordination of training times for participants located in different parts of the world. The bot handles the routine of converting time from UTC to each user's local time zone, helps visually assess if a group is forming (minimum participants), and includes an interactive plank challenge tracker.

---

## 💡 Idea and Features

- **Timezone Personalization:** The bot reads the user's time zone from the configuration and shows time buttons in their local format.
- **Dynamic Calendar:** Date selection is limited to the current week (4x2 grid), minimizing unnecessary clicks.
- **Automatic Calculation:** When selecting a time, the bot instantly displays a list: how this time will look in Helsinki, London, New York, etc.
- **Interactive Group Gathering:**
  - 'I'm in' and 'Can't make it' buttons with protection against repeated clicks.
  - Automatic status 'Session confirmed' when the minimum number of participants is reached.
- **Yoga Humor:** Reward system - the bot shows a random yoga joke as soon as the group is gathered.
- **Plank Challenge:** Interactive plank timer with adjustable duration (in 5s and 10s increments) and motivational messages.
- **Access Control:** The `AccessMiddleware` ensures only registered users (from `users_yoga.json` or `users_plank.json`) can interact with the bot.
- **Administration:** The `/shutdown` command is available only to the owner (the first one in the `users_yoga.json` list).

---

## 🧩 Middlewares

The bot uses a custom middleware system to handle cross-cutting concerns:

### 🛡 AccessMiddleware

This is the primary security layer of the bot. It intercepts every incoming update (Message or CallbackQuery) and performs the following checks:

1.  **Username Presence:** Ensures the user has a Telegram username set. If not, the request is rejected with a prompt to set one.
2.  **Whitelist Validation:** Checks if the user's username (case-insensitive) exists in either `users_yoga.json` or `users_plank.json`.
3.  **Automated Responses:** If access is denied, the middleware automatically sends a message (for commands) or a pop-up alert (for button clicks) explaining the reason.

This approach keeps the handler logic clean by centralizing authorization in one place.

---

## 🛠 Tech Stack (Resources)

- **Language:** Python 3.10+
- **Library:** `aiogram 3.x` (asynchronous work with Telegram API).
- **Data Storage:** `aiosqlite` (SQLite) for plank history and `JSON` (for user configuration and UTC offsets).
- **State:** `FSM (Finite State Machine)` for remembering selected dates and plank adjustments.
- **Middleware:** `AccessMiddleware` for access control and user authentication.
- **Configuration:** `config.py` for centralized constants and text resources.

---

## 📂 Project Structure

```text
schedule-bot/
├── main.py               # Entry point, initializes bot and routers
├── config.py             # Configuration constants and all texts/buttons
├── db/
│   └── database.py       # SQLite access layer for plank history
├── handlers/             # Command and callback handlers
│   ├── yoga.py           # /yoga flow, attendance logic
│   └── plank.py          # /plank, /progress, /graph flows
├── views/
│   ├── yoga.py           # Yoga keyboards (week, time, attendance)
│   └── plank.py          # Plank keyboards and graph generators
├── middlewares.py        # AccessMiddleware and other middlewares
├── states.py             # FSM states definitions
├── utils.py              # Time, validation, markdown helpers
├── tests/                # Unit tests (utils, db, views, config)
├── users_yoga.json       # Yoga user database (login → UTC offset)
├── users_plank.json      # Plank user database (login → UTC offset)
├── requirements.txt      # Dependencies
└── README.md             # Project description
```

---

### 📦 Installing Dependencies

The project uses the `requirements.txt` file to manage libraries. Before running, execute the command:

```bash
pip install -r requirements.txt

```

---

### 🚀 How to Run the Project

1. **Clone the repository** or download the project files.
2. **Create a virtual environment** (recommended):

```bash
python -m venv venv
source venv/bin/activate  # for macOS/Linux
source venv/Scripts/activate  # for Windows

```

3. **Install dependencies** from the requirements file:

```bash
pip install -r requirements.txt

```

4. **Prepare the bot**

- Create a bot via @BotFather in Telegram and get the **API TOKEN**.
- Create a `.env` file in the root folder with your token:
  ```
  BOT_TOKEN=your_token_here
  ```

5. **Configure users** (`users_yoga.json` and `users_plank.json`)

Create user configuration files in the root folder. The first user in the list will become the **Administrator**.

```json
{
  "user_1": 2,
  "user_2": 3,
  "user_3": -5
}
```

_The key is the Telegram username (in lowercase), and the value is the UTC offset._

6. **Run the bot**:

```bash
python main.py

```

---

### 🧪 Running Tests (for CI/CD)

Unit tests cover utilities, database layer and graph generation:

```bash
pytest
```

Основное:

- `tests/test_utils.py` — формат времени, конвертация, валидация пользователя.
- `tests/test_database.py` — работа с SQLite (init, insert, delete, stats, details).
- `tests/test_views.py` — генерация графика прогресса из готовых точек.

---

## 🚀 Deployment Examples

### 1. Google Cloud VM (screen/nohup вариант)

- **Machine:** Google Cloud VM (e2-micro for Free Tier).
- **Environment:** Python 3.9+, `venv` (recommended).
- **Firewall:** Port 22 (SSH) open for IAP/Personal IP.

To run the bot 24/7 even after closing the SSH session:

```bash
# Navigate to project folder
cd ~/yoga-bot

# Activate virtual environment (if used)
source venv/bin/activate

# Start in background with unbuffered logging
nohup python3 -u main.py > bot_log.txt 2>&1 &

# Check if the bot process is currently running:
ps aux | grep main.py

# Monitor real-time logs (errors, messages, interactions):
tail -f bot_log.txt
(Press Ctrl + C to exit log view)

# Update from GitHub
git reset --hard HEAD    # Discard local changes
git pull origin main     # Pull latest code

# Stop the bot process:
pkill -f main.py

# Then restart the bot using the Start command above
```

---

## 📝 Usage

### Yoga Sessions

1. Send the `/yoga` command to the bot.
2. Select a day of the week (the buttons automatically adapt to the current date).
3. Choose a convenient time slot (the time on the buttons will be shown in your local time zone).
4. The bot will post a final message featuring a calculated time list for all configured cities.
5. Click "I'm in" or "Can't make it" and wait until the required minimum number of participants is reached for the bot to share a joke!

### Plank Challenge

1. Send the `/plank` command to the bot.
2. Adjust the plank duration using the ➖ and ➕ buttons (adjusts by 5s or 10s).
3. Click ✅ Confirm to finalize your result.
4. The bot will display your result with a motivational message and local date.

### Plank Statistics & Graph

- `/progress` — shows weekly and monthly statistics:
  - total time, attempts, average and best result for 7 and 30 days;
  - button **“Details (Log)”** opens a per‑day attempt history for the last 30 days;
  - button **“Hide”** returns back to the full statistics view.
- `/graph` — sends a PNG graph of your plank progress over the last 30 days.

---

## ⚠️ Notes

- **Security:** The bot responds to the `/shutdown` command only from the first user in `users_yoga.json`.
- **Lowercase:** All logins in user configuration files must be in lowercase for correct search.
- **Time Offset:** The current version uses static numbers. When switching to daylight saving time/winter time, values in user configuration files need to be updated manually.
- **Configuration:** All constants and text resources can be easily modified in `config.py` without changing `main.py`.

---

## DEMO
![demo-scheduler-bot](https://github.com/user-attachments/assets/6870777e-435a-494d-9a94-2d8a87dbce2e)

---

**Have a productive workout!**
