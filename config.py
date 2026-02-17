"""Central configuration for the Yoga & Plank bot."""

# --- Database ---
DB_NAME = "yoga_community.db"

# --- Yoga Configuration ---
MIN_PARTICIPANTS = 2  # Minimum participants needed to confirm a yoga session
DEFAULT_SLOTS_UTC = [
    "16:00",
    "16:30",
    "17:00",
    "17:30",
    "18:00",
]  # Available time slots in UTC

YOGA_JOKES = [
    "I work out… so I can eat more later 🍕",
    "My favorite exercise is walking to the fridge 🚶‍♂️",
    "I don’t sweat, I sparkle ✨💦",
    "Gym time: 10% exercise, 90% selfies 🤳",
    "I started running… then I stopped and rested 😅",
    "Yoga is just fancy stretching with calm music 🎶",
    "I lift weights… mostly my own body 🏋️‍♂️",
    "My warm-up is already a workout 😮‍💨",
    "Exercise? I thought you said extra fries 🍟",
    "I run because walking sounds boring 🏃",
    "After leg day, stairs become my enemy 😭",
    "My body says yes, my muscles say no 🙃",
    "I go to the gym to see what not to do 😄",
    "Plank time feels longer than a movie 🎬",
    "I bend so slow, even my thoughts wait 🧘",
    "I train hard… for five minutes 😌",
    "Sport is fun, especially when it’s over 🎉",
    "I count reps like this: one, two, enough 😆",
    "My fitness goal: survive the workout 💀",
    "I stretch because my body makes weird sounds 🤔",
    "Running outside means free air and free pain 😂",
    "I do yoga to lie on the mat and breathe 🌬️",
    "My muscles wake up angry the next day 😠",
    "I train so my clothes still like me 👕",
    "Exercise is my way to balance pizza 🍕⚖️",
    "I move fast… in my dreams 😴",
    "Gym mirrors always lie 🪞",
    "I don’t skip leg day. I just forget 😇",
    "Stretching: when you fight your own body 🤼",
    "I rest between sets like a pro 😎",
    "I run slow, but with style 😏",
    "My trainer says smile. My face disagrees 😬",
    "Yoga pants give me confidence, not skills 😂",
    "I do squats to sit better later 🪑",
    "Sport teaches patience… and pain 😄",
    "I lift weights so gravity knows I’m strong 🌍",
    "My body is fit… fit for a nap 😴",
    "I exercise to feel tired in a new way 🤷",
    "Sweat now, shower later 🚿",
    "I run to escape my problems. They run faster 😆",
    "Gym music makes me stronger… a little 🎧",
    "I stretch and hope for the best 🤞",
    "My balance is good. The floor just moves 🤔",
    "I train because sitting all day is boring 🪑",
    "One more rep? Let me think… no 😄",
    "Yoga helps me find peace… and snacks later 🧘🍪",
    "I exercise so my body doesn’t forget me 😅",
    "Running is easy. Stopping is hard 😮‍💨",
    "I sweat like a hero 💪",
    "Workout done. Reward time! 🍫",
    "I train today so I can complain tomorrow 😜",
    "My muscles need coffee too ☕",
]

# --- Yoga Messages & Texts ---
YOGA_TEXT_USERNAME_REQUIRED = "❌ Set a Username in Telegram!"

YOGA_TEXT_PLANNING_TITLE = "📅 **Planning a session**\nChoose a day:"
YOGA_TEXT_TIME_TITLE = "📅 **{date}**\nChoose time:"

YOGA_TEXT_SESSION_SUMMARY = (
    "🧘 **Yoga {date}** (base UTC {utc_time})\n\n{times}\n\nShall we confirm?"
)

YOGA_TEXT_WINDOW_CLOSED = "Window closed"
YOGA_TEXT_MESSAGE_DELETED = "Message deleted or hidden"
YOGA_TEXT_PLANNING_CANCELLED = "Planning cancelled"

YOGA_TEXT_ALREADY_GOING = "You are already on the list! 😉"
YOGA_TEXT_ALREADY_NOT_GOING = "You have already marked that you won't come."

YOGA_TEXT_STATUS_SECTION = "✅ Who is going: {going}\n❌ Can't make it: {not_going}"

YOGA_TEXT_SESSION_CONFIRMED = (
    "🎉 **Session confirmed!** (gathered {count}/{min_participants})\n"
    "---\n\n"
    "✨ _{joke}_"
)

YOGA_TEXT_SESSION_NEED_MORE = "⏳ Need at least {needed} more people to confirm."

# --- Yoga Buttons ---
YOGA_BTN_BACK_TO_DATES = "⬅️ Back to dates"
YOGA_BTN_IM_IN = "🙋‍♂️ I'm in"
YOGA_BTN_NOT_GOING = "🏃‍♂️ Not going"
YOGA_BTN_DELETE = "❌ Delete"

# --- Plank Configuration ---
PLANK_MIN_SECONDS = 10
PLANK_INITIAL_SECONDS = 60

PLANK_MOTIVATION = [
    "Great effort! Keep pushing your limits! 💪",
    "You're getting stronger every day! 🎯",
    "Consistency is key! Come back tomorrow! 🔥",
    "Amazing performance! 🏆",
    "Great effort! Keep your breath calm, 🧘",
    "Strong body, calm mind, always, 💪",
    "You are doing really great today, 🌿",
    "Balance improves with every practice, ⚖️",
    "Breathe in calm, breathe out stress, 🌬️",
    "Slow moves bring strong results, 🧠",
    "Your focus is getting better, ✨",
    "Every pose makes you stronger, 🧍",
    "Nice control, keep breathing smoothly, 😌",
    "Your body trusts you more, 🤍",
    "Small progress is still progress, 🌱",
    "You showed up, that matters, 🙌",
    "Calm breath, steady movement, good, 🧘",
    "Your balance is improving today, ⭐",
    "Gentle practice brings deep strength, 💫",
    "You are moving with purpose, 🎯",
    "Strong legs, relaxed shoulders, nice, 💪",
    "Your patience grows with practice, 🕊️",
    "Feel the stretch, enjoy it, 😊",
    "Mind and body work together, 🧠💪",
    "You are fully present now, 🌼",
    "Each breath supports your movement, 🌬️",
    "Your practice looks calm today, 😌",
    "Nice flow, keep it smooth, 🌊",
    "You are building inner strength, 🔥",
    "Soft face, strong body, perfect, 🙂",
    "Stay steady, stay kind, 🧘",
    "Your focus is really strong, 🎯",
    "Good balance comes with time, ⏳",
    "You are learning with every pose, 📘",
    "Breath leads, body follows, 🌬️",
    "Calm effort brings best results, 🌿",
    "You are doing enough today, 🤍",
    "Nice stretch, stay relaxed, 😄",
    "Your body feels your care, 💖",
    "Slow practice builds deep power, 💪",
    "You look calm and focused, ✨",
    "Every breath makes you steadier, 🕊️",
    "Good energy flows through you, 🌈",
    "Practice complete, well done, 🙏",
]

# --- Plank Messages & Texts ---
PLANK_TEXT_USERNAME_REQUIRED = "❌ Set a Username in Telegram!"

PLANK_TEXT_CHALLENGE_TITLE = "💪 **Plank Challenge**\n{user_name}, adjust your result:"

PLANK_TEXT_DELETE_SUCCESS = "Result deleted 🗑"
PLANK_TEXT_DELETE_NONE = "No record to delete."
PLANK_TEXT_DELETE_ERROR = "Window closed or no record to delete."

PLANK_TEXT_TOO_FAST = "Too fast! Wait {seconds}s"

PLANK_TEXT_PLANK_COMPLETED = (
    "🏆 **Plank Completed!**\n\n"
    "👤 **User:** {user_name}\n"
    "⏱ **Result:** {result}\n"
    "📅 **Date:** {date}\n\n"
    "_{note}_"
)

PLANK_TEXT_STATS_HEADER = "📊 **Your Plank Statistics**\n\n"
PLANK_TEXT_STATS_WEEK_TITLE = "🗓 **Week (7 days):**\n"
PLANK_TEXT_STATS_MONTH_TITLE = "📅 **Month (30 days):**\n"
PLANK_TEXT_STATS_TAGLINE = "<i>The more you do, the easier it gets!</i> 💪"

PLANK_TEXT_NO_DATA = "No data yet"
PLANK_TEXT_DETAILS_HEADER = "📝 **Attempt History (30 days):**\n\n"

PLANK_TEXT_GRAPH_NO_DATA = "No data for graph yet! Complete at least one plank."
PLANK_TEXT_GRAPH_CAPTION = "📈 Your Progress Graph"
PLANK_TEXT_GRAPH_ERROR = "Error creating graph."

# --- Plank Buttons ---
PLANK_BTN_DELETE = "❌ Delete"
PLANK_BTN_BACK = "⬅️ Back"
PLANK_BTN_CONFIRM = "✅ Confirm"
PLANK_BTN_DETAILS = "📝 Details (Log)"
PLANK_BTN_HIDE = "⬆️ Hide"

# --- Bot Commands ---
BOT_COMMANDS = [
    ("plank", "⏱ New plank record"),
    ("yoga", "🧘‍♀️ Schedule a session"),
    ("progress", "📊 My statistics"),
    ("graph", "📈 Progress graph"),
]

# --- Logging ---
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
