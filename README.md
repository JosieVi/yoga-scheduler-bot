# Yoga & Plank Scheduler Bot

A Telegram bot for scheduling group yoga sessions with timezone synchronization and tracking individual plank challenge progress.

## ✨ Features

- **Timezone Synchronization:** Converts UTC time slots to users' local times for seamless scheduling.
- **Interactive Yoga Scheduling:** Dynamic calendar, multi-city time display, and participant confirmation with anti-spam.
- **Plank Challenge Tracking:** Interactive timer, weekly/monthly statistics, and automated progress graph generation.
- **Access Control:** Restricts bot interaction to whitelisted users defined in JSON configuration files.
- **Administrator Commands:** Secure `/shutdown` command for bot management.

## 🛠 Tech Stack

- **Python:** 3.10+
- **Framework:** aiogram (Asynchronous Telegram Bot API)
- **Database:** aiosqlite (Asynchronous SQLite)
- **Data Serialization:** python-dotenv (Environment variables), JSON (User configurations)
- **Visualization:** Matplotlib (Progress graphs)
- **Testing:** pytest, pytest-asyncio
- **Linting:** Ruff

## 🖼 DEMO

![demo-scheduler-bot](https://github.com/user-attachments/assets/6870777e-435a-494d-9a94-2d8a87dbce2e)

## 🚀 Quick Start

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/schedule-bot.git
    cd schedule-bot
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  **Environment Variables (`.env`):**
    Create a `.env` file in the root directory:
    ```
    BOT_TOKEN=your_telegram_bot_token
    ```
2.  **User Configuration (`users_yoga.json`, `users_plank.json`):**
    Create `users_yoga.json` and `users_plank.json` files in the root folder. The key is the Telegram username (in lowercase), and the value is the UTC offset. The first user in `users_yoga.json` will be designated as the Administrator.
    ```json
    {
      "user_1": 2,
      "user_2": 3,
      "user_3": -5
    }
    ```

### Database

The project uses `aiosqlite` for asynchronous SQLite database operations. The database file `yoga_community.db` is automatically created, and the `plank_history` table is initialized upon the bot's first run via the `init_db()` function in `db/database.py`.

## 🧑‍💻 Development

### Running the Bot

To start the bot locally:

```bash
python main.py
```

### Linting

This project uses [Ruff](https://beta.ruff.rs/docs/) for linting to enforce code style and catch errors.

**Manual check:**

```bash
pip install ruff

ruff check .
```

**Automated pre-commit hooks**

This project includes a .pre-commit-config.yaml to automatically check code before every commit.

```bash
# 1. Install pre-commit
pip install pre-commit

# 2. Install the git hooks
pre-commit install
```

### Testing

Tests are implemented using `pytest` and `pytest-asyncio` for asynchronous code.

```bash
# Install test dependencies (if not already installed via requirements.txt)
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v
```

### Pre-commit Hooks

Pre-commit hooks are configured to automatically run linting and formatting checks before each commit.
To set up the hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks into your .git/ directory
pre-commit install
```

### CI/CD

This project implements a full automated lifecycle using GitHub Actions. Every push to the `main` branch triggers a pipeline that ensures code quality and updates the production server.

**Pipeline workflow:**

- **Linter (`flake8`)**: scans code for syntax errors and basic PEP8 issues.
- **Tests (`pytest`)**: runs asynchronous tests for database operations and core business logic.
- **Automated deploy**: if tests pass, the code is pulled to the Google Cloud (GCP) instance and the system service is restarted.

## 🛠 Server Setup & Installation

1. **System dependencies**

   The bot requires Python 3.10+ and a virtual environment:

   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv
   ```

2. **Service configuration**

### Google Cloud VM

- **Machine:** Google Cloud VM (e2-micro for Free Tier).
- **Environment:** Python 3.9+, `venv` (recommended).
- **Firewall:** Port 22 (SSH) open for IAP/Personal IP.

  ### Option A: Systemd (Recommended for Production)

  Use this method to keep the bot running 24/7, automatically restart on crashes, and launch on system boot.

  ```bash
  # Create the service file
  sudo nano /etc/systemd/system/yoga_scheduler_bot.service

  # Paste the configuration (adjust paths to match your setup):
  [Unit]
   Description=Yoga Scheduler Bot
   After=network.target

   [Service]
   # Path to your project directory
   WorkingDirectory=/home/your_user/yoga-bot
   # Path to python inside your virtual environment
   ExecStart=/home/your_user/yoga-bot/venv/bin/python main.py
   User=your_user
   Restart=always
   RestartSec=10s

   [Install]
   WantedBy=multi-user.target

  # Apply changes and start the bot
  sudo systemctl daemon-reload
  sudo systemctl enable yoga_scheduler_bot.service
  sudo systemctl start yoga_scheduler_bot.service

  # Manage

  # Check bot status
  sudo systemctl status yoga_scheduler_bot

  # View live logs
  sudo journalctl -u yoga_scheduler_bot -f

  # Manual restart
  sudo systemctl restart yoga_scheduler_bot

  # Last 50 log lines
  sudo journalctl -u yoga_scheduler_bot -n 50 --no-pager

  ```

  ### Option B: Nohup (Quick Start / Manual)

  Use this method for quick testing or if you don't have sudo privileges.

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

## 📂 Project Structure & Architecture

This project follows a modular architecture inspired by the MVC (Model-View-Controller) pattern.

- **Model (`db/`)**: Manages the data and logic of the SQLite database. It doesn't know about the bot's interface.
- **View (`views/`)**: Responsible for how the data is presented to the user (inline keyboards and Matplotlib graphs).
- **Controller (`handlers/`)**: Acts as the brain. It processes user input from the bot, interacts with the Model, and selects a View to render the response.

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

## 📝 Usage

### Yoga Sessions

- Send the `/yoga` command to initiate scheduling.
- Select a day and a convenient time slot (displayed in your local timezone).
- Use "I'm in" or "Can't make it" buttons to confirm participation.
- A session is automatically confirmed when the `MIN_PARTICIPANTS` threshold is reached.

### Plank Challenge

- Start a challenge with the `/plank` command.
- Adjust plank duration and confirm your result.
- View weekly and monthly statistics using `/progress`.
- Generate a visual progress graph with `/graph`.

## ⚠️ Notes

- **Security:** The `/shutdown` command is exclusively available to the first user listed in `users_yoga.json`.
- **Lowercase Usernames:** Ensure all usernames in `users_yoga.json` and `users_plank.json` are in lowercase for correct lookup.
- **Time Offset Management:** UTC offsets in user configuration files currently require manual updates for daylight saving time changes.
- **Customization:** Core constants and text resources can be easily modified in `config.py` without altering the main application logic.

---

**Have a productive workout!** 🧘‍♂️💪
