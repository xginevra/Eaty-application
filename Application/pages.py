from nicegui import ui
import pandas as pd
import plotly.express as px

from dbfile import c, insert_log, update_user, get_logs
from utils import EXERCISE_CALORIES, calculate_bmi, calculate_bmr, calculate_body_fat


# ---------------------------
# Shared home button
# ---------------------------
def home_button():
    ui.button('🏠 Home', on_click=lambda: ui.navigate.to('/')).classes('mt-2')


# ---------------------------
# Plan page
# ---------------------------
@ui.page('/plan')
def plan_page():
    home_button()
    ui.label('🎯 Your Fitness Plan').classes('text-2xl font-bold text-center mt-4')

    with ui.card().classes('w-2/3 mx-auto mt-6 p-6'):
        ui.label('Suggested Daily Routine').classes('text-lg font-semibold')
        ui.label('Meals:')
        ui.markdown('- Breakfast: Oatmeal with fruit\n- Lunch: Grilled chicken and vegetables\n- Dinner: Light salad or soup\n- Snacks: Nuts, yogurt')

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
        log_type = ui.select(['Meal', 'Exercise'], label='Log Type')
        content = ui.input('Description')

        ui.label('Satisfaction (1-10)')
        satisfaction_value = ui.label('5')
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
        activity = ui.select(['Sedentary', 'Lightly active', 'Moderately active', 'Very active'],
                             label='Activity level', value=user[9])
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