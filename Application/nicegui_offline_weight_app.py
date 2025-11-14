from nicegui import ui, app
import sqlite3
from datetime import datetime
import math
import pandas as pd
import plotly.express as px
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

# Logs table with calories
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
# Standard calories for exercises
# ---------------------------
EXERCISE_CALORIES = {
    'Brisk Walk': 150,
    'Core Exercises': 100,
    'Yoga': 80,
    'Stretching': 50,
    'Jogging': 200,
    'Cycling': 250,
    'Swimming': 300
}

# ---------------------------
# Helper functions
# ---------------------------
def calculate_bmi(weight, height):
    return round(weight / ((height / 100) ** 2), 2)

def calculate_bmr(weight, height, age, gender):
    if gender.lower() == 'male':
        return round(88.36 + 13.4*weight + 4.8*height - 5.7*age, 2)
    else:
        return round(447.6 + 9.2*weight + 3.1*height - 4.3*age, 2)

def calculate_body_fat(gender, height, neck, waist, hip):
    if gender.lower() == 'male':
        return round(495 / (1.0324 - 0.19077*math.log10(waist - neck) + 0.15456*math.log10(height)) - 450, 2)
    else:
        return round(495 / (1.29579 - 0.35004*math.log10(waist + hip - neck) + 0.22100*math.log10(height)) - 450, 2)

def insert_user(data):
    c.execute('''INSERT INTO users (name, age, gender, height_cm, weight_kg, neck_cm, waist_cm, hip_cm, activity_level, goal, bmi, bmr, body_fat, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        data['name'], data['age'], data['gender'], data['height_cm'], data['weight_kg'],
        data['neck_cm'], data['waist_cm'], data.get('hip_cm'), data['activity_level'],
        data['goal'], data['bmi'], data['bmr'], data['body_fat'], datetime.utcnow().isoformat()
    ))
    conn.commit()
    return c.lastrowid

def update_user(user_id, data):
    c.execute('''UPDATE users SET name=?, age=?, gender=?, height_cm=?, weight_kg=?, neck_cm=?, waist_cm=?, hip_cm=?,
                 activity_level=?, goal=?, bmi=?, bmr=?, body_fat=?, created_at=? WHERE id=?''', (
        data['name'], data['age'], data['gender'], data['height_cm'], data['weight_kg'],
        data['neck_cm'], data['waist_cm'], data.get('hip_cm'), data['activity_level'],
        data['goal'], data['bmi'], data['bmr'], data['body_fat'], datetime.utcnow().isoformat(), user_id
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
# UI Helper
# ---------------------------
def home_button():
    ui.button('🏠 Home', on_click=lambda: ui.navigate.to('/')).classes('mt-2')

# ---------------------------
# Main Page
# ---------------------------
@ui.page('/')
def main_page():
    home_button()
    ui.label('🏋️‍♀️ Fitness Tracker — Offline Edition').classes('text-2xl font-bold text-center mt-4')

    c.execute('SELECT * FROM users ORDER BY created_at DESC LIMIT 1')
    user = c.fetchone()

    if user:
        # Summary card
        with ui.card().classes('w-1/2 mx-auto mt-6 p-6'):
            ui.markdown(f"""
**Name:** {user[1]}  
**Age:** {user[2]}  
**Gender:** {user[3]}  
**Height:** {user[4]} cm  
**Weight:** {user[5]} kg  
**BMI:** {user[11]}  
**BMR:** {user[12]}  
**Body Fat:** {user[13]}%
            """)

        # Buttons
        ui.button('✏️ Change My Data', on_click=lambda: ui.navigate.to('/change-data')).classes('w-full bg-yellow-500 text-white mt-4')
        ui.button('➡️ Go to Plan', on_click=lambda: ui.navigate.to('/plan')).classes('w-full bg-blue-500 text-white mt-2')

        # Charts row
        with ui.row().classes('w-11/12 mx-auto mt-6 gap-4'):
            # Meals per day
            c.execute("SELECT date(timestamp) as day, COUNT(*) FROM logs WHERE type='Meal' GROUP BY day ORDER BY day")
            meal_data = c.fetchall()
            if meal_data:
                df_meals = pd.DataFrame(meal_data, columns=['Day', 'Meals'])
                fig_meals = px.bar(df_meals, x='Day', y='Meals', title='Meals Logged Per Day')
                ui.plotly(fig_meals).classes('w-1/3')

            # Weight over time
            c.execute("SELECT date(created_at) as day, weight_kg FROM users ORDER BY created_at")
            weight_data = c.fetchall()
            if weight_data:
                df_weight = pd.DataFrame(weight_data, columns=['Day', 'Weight'])
                fig_weight = px.line(df_weight, x='Day', y='Weight', markers=True, title='Weight Over Time')
                ui.plotly(fig_weight).classes('w-1/3')

            # Calories burnt chart
            c.execute("SELECT date(timestamp) as day, SUM(calories) FROM logs WHERE type='Exercise' GROUP BY day ORDER BY day")
            calories_data = c.fetchall()
            if calories_data:
                df_calories = pd.DataFrame(calories_data, columns=['Day', 'Calories'])
                fig_calories = px.line(df_calories, x='Day', y='Calories', markers=True, title='Calories Burnt Over Time')
                ui.plotly(fig_calories).classes('w-1/3')

    else:
        # Input form for new user
        with ui.card().classes('w-1/2 mx-auto mt-6 p-6'):
            name = ui.input('Name')
            age = ui.number('Age (years)')
            gender = ui.select(['Male', 'Female'], label='Gender')
            height = ui.number('Height (cm)')
            weight = ui.number('Weight (kg)')
            neck = ui.number('Neck (cm)')
            waist = ui.number('Waist (cm)')
            hip = ui.number('Hip (cm, optional)')
            activity = ui.select(['Sedentary', 'Lightly active', 'Moderately active', 'Very active'], label='Activity level')
            goal = ui.select(['Lose Weight', 'Get Fitter'], label='Goal')

            def submit_user():
                bmi = calculate_bmi(weight.value, height.value)
                bmr = calculate_bmr(weight.value, height.value, age.value, gender.value)
                body_fat = calculate_body_fat(gender.value, height.value, neck.value, waist.value, hip.value or 0)

                data = {
                    'name': name.value,
                    'age': int(age.value),
                    'gender': gender.value,
                    'height_cm': float(height.value),
                    'weight_kg': float(weight.value),
                    'neck_cm': float(neck.value),
                    'waist_cm': float(waist.value),
                    'hip_cm': float(hip.value) if hip.value else None,
                    'activity_level': activity.value,
                    'goal': goal.value,
                    'bmi': bmi,
                    'bmr': bmr,
                    'body_fat': body_fat,
                }

                insert_user(data)
                ui.notify(f'User {name.value} saved! BMI: {bmi}, BMR: {bmr}, Body Fat: {body_fat}%')
                ui.navigate.to('/plan')

            ui.button('Save & Continue', on_click=submit_user).classes('w-full bg-blue-500 text-white mt-4')

# ---------------------------
# Plan page
# ---------------------------
@ui.page('/plan')
def plan_page():
    home_button()
    ui.label('🎯 Your Fitness Plan').classes('text-2xl font-bold text-center mt-4')

    with ui.card().classes('w-2/3 mx-auto mt-6 p-6'):
        ui.label('Suggested Daily Routine').classes('text-lg font-semibold')

        # Meals
        ui.label('Meals:')
        ui.markdown('- Breakfast: Oatmeal with fruit\n- Lunch: Grilled chicken and vegetables\n- Dinner: Light salad or soup\n- Snacks: Nuts, yogurt')

        # Exercises
        ui.label('Exercises (choose what to do today):')
        exercises = ui.select(list(EXERCISE_CALORIES.keys()), label='Exercises', multiple=True)

        def save_exercises():
            selected = exercises.value
            if selected:
                for e in selected:
                    insert_log(1, 'Exercise', e, 5, EXERCISE_CALORIES[e])
                ui.notify(f"Today's exercises saved: {', '.join(selected)}")
            else:
                ui.notify("No exercises selected.")

        ui.button('Save Exercises', on_click=save_exercises).classes('w-full bg-blue-500 text-white mt-4')
        ui.button('Go to Tracker', on_click=lambda: ui.navigate.to('/tracker')).props('flat')

# ---------------------------
# Tracker page
# ---------------------------
@ui.page('/tracker')
def tracker_page():
    home_button()
    ui.label('📊 Daily Log Tracker').classes('text-2xl font-bold text-center mt-4')

    with ui.card().classes('w-2/3 mx-auto mt-6 p-6'):
        ui.label('Log Type')
        log_type = ui.select(['Meal', 'Exercise'])

        ui.label('Description')
        content = ui.input('')

        ui.label('Satisfaction (1-10)')
        satisfaction_value = ui.label('5')  # display current value
        satisfaction = ui.slider(
            min=1, max=10, value=5, step=1,
            on_change=lambda e: satisfaction_value.set_text(str(e.value))
        )


        def save_log():
            if log_type.value == 'Exercise':
                calories = EXERCISE_CALORIES.get(content.value, 0)
            else:
                calories = 0
            insert_log(1, log_type.value, content.value, satisfaction.value, calories)
            ui.notify('Log saved!')

        ui.button('Save Log', on_click=save_log).classes('w-full bg-green-500 text-white mt-4')
        ui.button('View Logs', on_click=lambda: ui.navigate.to('/logs')).props('flat')

# ---------------------------
# Change Data Page
# ---------------------------
@ui.page('/change-data')
def change_data_page():
    home_button()
    ui.label('✏️ Change My Data').classes('text-2xl font-bold text-center mt-4')

    c.execute('SELECT * FROM users ORDER BY created_at DESC LIMIT 1')
    user = c.fetchone()
    if not user:
        ui.label("No user data found.").classes('text-center mt-4')
        ui.button("Go to Main Page", on_click=lambda: ui.navigate.to('/')).classes('w-full mt-4')
        return

    with ui.card().classes('w-1/2 mx-auto mt-6 p-6'):
        name = ui.input('Name', value=user[1])
        age = ui.number('Age (years)', value=user[2])
        gender = ui.select(['Male', 'Female'], label='Gender', value=user[3])
        height = ui.number('Height (cm)', value=user[4])
        weight = ui.number('Weight (kg)', value=user[5])
        neck = ui.number('Neck (cm)', value=user[6])
        waist = ui.number('Waist (cm)', value=user[7])
        hip = ui.number('Hip (cm, optional)', value=user[8])
        activity = ui.select(['Sedentary', 'Lightly active', 'Moderately active', 'Very active'], label='Activity level', value=user[9])
        goal = ui.select(['Lose Weight', 'Get Fitter'], label='Goal', value=user[10])

        def update_user_data():
            bmi = calculate_bmi(weight.value, height.value)
            bmr = calculate_bmr(weight.value, height.value, age.value, gender.value)
            body_fat = calculate_body_fat(gender.value, height.value, neck.value, waist.value, hip.value or 0)
            data = {
                'name': name.value, 'age': int(age.value), 'gender': gender.value,
                'height_cm': float(height.value), 'weight_kg': float(weight.value),
                'neck_cm': float(neck.value), 'waist_cm': float(waist.value),
                'hip_cm': float(hip.value) if hip.value else None,
                'activity_level': activity.value, 'goal': goal.value,
                'bmi': bmi, 'bmr': bmr, 'body_fat': body_fat
            }
            update_user(user[0], data)
            ui.notify('User data updated!')
            ui.navigate.to('/plan')

        ui.button('Save Changes', on_click=update_user_data).classes('w-full bg-blue-500 text-white mt-4')


# ---------------------------
# Logs page
# ---------------------------
@ui.page('/logs')
def logs_page():
    home_button()
    ui.label('🗂️ All Logs').classes('text-2xl font-bold text-center mt-4')

    logs = get_logs()
    if not logs:
        ui.label('No logs yet.').classes('text-center mt-4')
        return

    columns = [{'field': k, 'label': k.replace('_', ' ').title()} for k in logs[0].keys()]
    ui.table(rows=logs, columns=columns).classes('w-11/12 mx-auto mt-6')

# ---------------------------
# Run app
# ---------------------------
if __name__ in {"__main__", "__mp_main__"}:
    ui.run()
