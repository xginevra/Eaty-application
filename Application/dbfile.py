import sqlite3
from datetime import datetime

# ---------------------------
# Database setup
# ---------------------------
conn = sqlite3.connect('fitnessapp.db', check_same_thread=False)
c = conn.cursor()

# Users table
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    gender TEXT,
    height_cm REAL,
    weight_kg REAL,
    target_weight_kg REAL,
    goal_duration_weeks INTEGER DEFAULT 12,
    neck_cm REAL,
    waist_cm REAL,
    hip_cm REAL,
    activity_level TEXT,
    goal TEXT,
    bmi REAL,
    bmr REAL,
    body_fat REAL,
    created_at TEXT
)''')

# Logs table
c.execute('''CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    content TEXT,
    satisfaction INTEGER,
    calories REAL DEFAULT 0,
    timestamp TEXT
)''')
conn.commit()


# ---------------------------
# CRUD helper functions
# ---------------------------
def insert_user(data):
    """Insert a new user and return the user_id."""
    c.execute('''INSERT INTO users (
                     name, age, gender, height_cm, weight_kg, target_weight_kg,
                     goal_duration_weeks, neck_cm, waist_cm, hip_cm, activity_level, goal,
                     bmi, bmr, body_fat, created_at
                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        data['name'],
        data['age'],
        data['gender'],
        data['height_cm'],
        data['weight_kg'],
        data.get('target_weight_kg', data['weight_kg'] - 5),      # fallback if not provided
        data.get('goal_duration_weeks', 12),                     # default 12 weeks
        data['neck_cm'],
        data['waist_cm'],
        data.get('hip_cm'),
        data['activity_level'],
        data['goal'],
        data['bmi'],
        data['bmr'],
        data['body_fat'],
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    return c.lastrowid


def update_user(user_id, data):
    """Update an existing user’s data."""
    c.execute('''UPDATE users SET
                     name=?, age=?, gender=?, height_cm=?, weight_kg=?, target_weight_kg=?,
                     goal_duration_weeks=?, neck_cm=?, waist_cm=?, hip_cm=?,
                     activity_level=?, goal=?, bmi=?, bmr=?, body_fat=?, created_at=?
                 WHERE id=?''', (
        data['name'],
        data['age'],
        data['gender'],
        data['height_cm'],
        data['weight_kg'],
        data.get('target_weight_kg', data['weight_kg'] - 5),
        data.get('goal_duration_weeks', 12),
        data['neck_cm'],
        data['waist_cm'],
        data.get('hip_cm'),
        data['activity_level'],
        data['goal'],
        data['bmi'],
        data['bmr'],
        data['body_fat'],
        datetime.utcnow().isoformat(),
        user_id
    ))
    conn.commit()


def insert_log(user_id, log_type, content, satisfaction, calories=0):
    c.execute('''INSERT INTO logs (user_id, type, content, satisfaction, calories, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (user_id, log_type, content, satisfaction, calories, datetime.utcnow().isoformat()))
    conn.commit()


def get_logs():
    c.execute('SELECT * FROM logs ORDER BY timestamp DESC')
    rows = c.fetchall()
    col_names = [desc[0] for desc in c.description]
    return [dict(zip(col_names, row)) for row in rows]

# ---------------------------
# Weight progress table
# ---------------------------
c.execute('''CREATE TABLE IF NOT EXISTS weight_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    weight REAL,
    recorded_at TEXT
)''')
conn.commit()


def insert_weight(user_id, weight):
    c.execute('''INSERT INTO weight_progress (user_id, weight, recorded_at)
                 VALUES (?, ?, ?)''', (user_id, weight, datetime.utcnow().isoformat()))
    conn.commit()


def get_weight_history(user_id):
    c.execute('''SELECT date(recorded_at) as day, weight FROM weight_progress
                 WHERE user_id = ? ORDER BY recorded_at''', (user_id,))
    rows = c.fetchall()
    return [{'Day': row[0], 'Weight': row[1]} for row in rows]
