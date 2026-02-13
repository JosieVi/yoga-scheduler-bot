# Yoga Scheduler Bot 🧘‍♂️

A Telegram bot designed to automate group yoga scheduling and individual plank challenge tracking. Built with a focus on time-zone synchronization, data visualization, and automated quality assurance.

## 🎯 Project Goal

The bot addresses the complexity of coordinating international groups by managing seamless UTC-to-local time conversions. Beyond scheduling, it features an interactive Plank Challenge module that tracks user performance, generates progress analytics, and fosters group motivation.

---

## 💡 Features

- **Timezone Personalization:** Automatically converts UTC slots to user's local time based on their configuration.
- **Dynamic Calendar:** Date selection for the current week (4x2 grid) for quick scheduling.
- **Automatic Multi-City Calculation:** Displays how the selected time looks in Helsinki, London, New York, and other configured cities.
- **Interactive Group Gathering:**
  - "I'm in" and "Can't make it" buttons with anti-spam protection.
  - Automatic session confirmation when `MIN_PARTICIPANTS` (configured in `config.py`) is reached.
  - Random yoga joke reward once the group is gathered.
- **Plank Challenge:** 
  - Interactive timer with adjustable duration (+/- 5s and 10s).
  - Weekly and monthly progress statistics.
  - Automatic progress graph generation using Matplotlib.
- **Access Control:** `AccessMiddleware` restricts interaction to registered users listed in `users_yoga.json` or `users_plank.json`.
- **Administration:** Secure `/shutdown` command available only to the first user in the yoga whitelist.

---

## 🖼 DEMO

![demo-scheduler-bot](https://github.com/user-attachments/assets/6870777e-435a-494d-9a94-2d8a87dbce2e)

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

## 📂 Project Structure & Architecture  

This project follows a modular architecture inspired by the MVC (Model-View-Controller) pattern. This separation of concerns ensures that the business logic, data management, and user interface are independent, making the bot highly scalable and easy to test.

The codebase is organized as follows:
```text
schedule-bot/
├── main.py               # Entry point: Initializes the bot, dispatcher, and routers
├── config.py             # Configuration: Centralized constants, settings, and UI strings
├── states.py             # FSM: Finite State Machine definitions for user flows
├── middlewares.py        # Middleware: Global request processing and access control
├── utils.py              # Helpers: Timezone conversions, validation, and formatting
├── db/                   # MODEL: Data Access Layer
│   └── database.py       # Asynchronous SQLite management for persistence
├── handlers/             # CONTROLLER: Request Handling
│   ├── yoga.py           # Logic for /yoga flow and attendance tracking
│   └── plank.py          # Logic for /plank, /progress, and /graph commands
├── views/                # VIEW: UI Components
│   ├── yoga.py           # Presentation layer for Yoga (keyboards, menus)
│   └── plank.py          # Presentation layer for Plank (keyboards and graph generation)
├── tests/                # Quality Assurance: Automated unit tests for DB, Utils, and Views
├── users_yoga.json       # User metadata for Yoga (Login → UTC offset)
├── users_plank.json      # User metadata for Plank (Login → UTC offset)
└── requirements.txt      # Project dependencies
```

### Architecture Pattern: MVC
Model (`db/`): Manages the data and logic of the SQLite database. It doesn't know about the bot's interface.

View (`views/`): Responsible for how the data is presented to the user (inline keyboards and Matplotlib graphs).

Controller (`handlers/`): Acts as the brain. It processes user input from the bot, interacts with the Model, and selects a View to render the response.

---

## 📦 Installing Dependencies

The project uses the `requirements.txt` file to manage libraries. Before running, execute the command:

```bash
pip install -r requirements.txt

```

---

## 🚀 How to Run the Project

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
## 🚀 CI/CD & Deployment
This project implements a full automated lifecycle using GitHub Actions. Every push to the `main` branch triggers a pipeline that ensures code quality and updates the production server.

**Pipeline workflow:**

- **Linter (`flake8`)**: scans code for syntax errors and basic PEP8 issues.
- **Tests (`pytest`)**: runs asynchronous tests for database operations and core business logic.
- **Automated deploy**: if tests pass, the code is pulled to the Google Cloud (GCP) instance and the system service is restarted.

### 🛠 Server Setup & Installation

1. **System dependencies**

   The bot requires Python 3.10+ and a virtual environment:

   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv
   ```

2. **Service configuration (`systemd`)**

   To keep the bot online 24/7 and restart it automatically on crashes or reboots:

   ```bash
   # Create the service file
   sudo nano /etc/systemd/system/yoga_scheduler_bot.service

   # Apply changes and start the bot
   sudo systemctl daemon-reload
   sudo systemctl enable yoga_scheduler_bot.service
   sudo systemctl start yoga_scheduler_bot.service
   ```

### 💻 Management Cheat Sheet

#### Production server operations

- **Check bot status**: `sudo systemctl status yoga_scheduler_bot`
- **View live logs**: `sudo journalctl -u yoga_scheduler_bot -f`
- **Manual restart**: `sudo systemctl restart yoga_scheduler_bot`
- **Last 50 log lines**: `sudo journalctl -u yoga_scheduler_bot -n 50 --no-pager`

#### Local development & testing

- **Run all tests**: `pytest tests/`
- **Update requirements**: `pip freeze > requirements.txt`
- **Code style check**: `flake8 .`

---

## 🧪 Quality Assurance & Testing
This project employs a comprehensive testing strategy to ensure reliability, data integrity, and a seamless user experience. As part of the CI/CD pipeline, all tests must pass before any code is deployed to the production server.

### Test categories

- **Unit testing**: individual functions and constants in isolation (e.g. time formatting, configuration values).
- **Integration testing**: interaction between the application logic and the SQLite database using a temporary test database.
- **Asynchronous testing**: async/await logic covered with `pytest-asyncio` to ensure non-blocking DB operations.

### Key test suites

- `tests/test_config.py` – validates configuration constants, command lists and text resources.
- `tests/test_utils.py` – time formatting, timezone conversion, markdown escaping, user validation and `to_seconds` conversion.
- `tests/test_database.py` – SQLite lifecycle: init, insert, delete, stats and detailed history.
- `tests/test_views.py` – generation of plank progress graph from prepared data points.

### 🛠 How to run tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests with a short summary
pytest tests/ -v
```

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

## 🛠 Tech Stack

- **Language:** Python 3.10+
- **Framework:** [aiogram 3.x](https://docs.aiogram.dev/) (Asynchronous Telegram Bot API)
- **Database:** `aiosqlite` (Asynchronous SQLite) for plank history.
- **Data Formats:** `JSON` for user configuration and time offsets.
- **Visualization:** `Matplotlib` for progress graphs.
- **Environment:** `python-dotenv` for secret management.

---

## ⚠️ Notes

- **Security:** The bot responds to the `/shutdown` command only from the first user in `users_yoga.json`.
- **Lowercase:** All logins in user configuration files must be in lowercase for correct search.
- **Time Offset:** The current version uses static numbers. When switching to daylight saving time/winter time, values in user configuration files need to be updated manually.
- **Configuration:** All constants and text resources can be easily modified in `config.py` without changing `main.py`.

---

**Have a productive workout!** 🧘‍♂️💪
