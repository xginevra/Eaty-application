from nicegui import ui
import pandas as pd
import sqlite3
from datetime import datetime
from dbfile import insert_user, update_user, insert_log, get_logs, insert_weight, get_weight_history
import plotly.express as px

# ----------------------------------------
# Database
# ----------------------------------------
conn = sqlite3.connect('fitnessapp.db', check_same_thread=False)
c = conn.cursor()


def get_latest_user():
    c.execute('SELECT * FROM users ORDER BY created_at DESC LIMIT 1')
    row = c.fetchone()
    if not row:
        return None
    col_names = [desc[0] for desc in c.description]
    return dict(zip(col_names, row))


# ----------------------------------------
# Calculations
# ----------------------------------------
def calculate_bmi(weight, height):
    return round(weight / ((height / 100) ** 2), 2)


def calculate_bmr(weight, height, age, gender):
    if gender.lower() == 'male':
        return round(10 * weight + 6.25 * height - 5 * age + 5, 2)
    else:
        return round(10 * weight + 6.25 * height - 5 * age - 161, 2)


def calculate_body_fat(bmi, age, gender):
    if gender.lower() == 'male':
        return round(1.20 * bmi + 0.23 * age - 16.2, 2)
    else:
        return round(1.20 * bmi + 0.23 * age - 5.4, 2)


# ----------------------------------------
# Global styling
# ----------------------------------------
CARD = 'p-6 rounded-xl shadow-lg bg-white border border-emerald-100'
WIDE_CARD = 'p-6 rounded-xl shadow-lg bg-white w-full border border-emerald-100'
BTN = 'bg-emerald-600 text-white px-6 py-2 rounded-lg hover:bg-emerald-700 transition-colors'
BTN_SECONDARY = 'bg-white text-emerald-600 px-6 py-2 rounded-lg hover:bg-emerald-50 border-2 border-emerald-600 transition-colors'
TITLE = 'text-3xl font-bold mb-6 text-emerald-900'
SECTION_TITLE = 'text-xl font-bold mb-3 text-emerald-800'
PAGE_BG = 'bg-gradient-to-br from-emerald-50 to-teal-50 min-h-screen'


# ----------------------------------------
# Top Navigation Bar
# ----------------------------------------
def navbar():
    with ui.header().classes('bg-gradient-to-r from-emerald-600 to-teal-600 shadow-lg items-center px-6 py-3'):
        ui.label("🥗 Eaty").classes('text-2xl font-bold text-white')
        ui.space()
        ui.button("Home", on_click=lambda: ui.navigate.to('/')).classes('mx-2 text-white hover:bg-emerald-700 rounded-lg px-4 py-2')
        ui.button("Add Log", on_click=lambda: ui.navigate.to('/add-log')).classes('mx-2 text-white hover:bg-emerald-700 rounded-lg px-4 py-2')
        ui.button("My Data", on_click=lambda: ui.navigate.to('/change-data')).classes('mx-2 text-white hover:bg-emerald-700 rounded-lg px-4 py-2')


# ----------------------------------------
# Home Page
# ----------------------------------------
@ui.page('/')
def home():
    ui.query('body').classes(PAGE_BG)
    navbar()
    user = get_latest_user()

    if not user:
        with ui.column().classes('items-center mt-20'):
            ui.label("No user found. Please add your data first.").classes(TITLE)
            ui.button("➕ Add User", on_click=lambda: ui.navigate.to('/new-user')).classes(BTN)
        return

    user_id = user['id']

    with ui.row().classes('w-full gap-6 mt-6 px-6').style('flex-wrap: nowrap;'):
        
        # -------------------------
        # LEFT COLUMN (Profile + Update Weight side by side)
        # -------------------------
        with ui.column().classes('gap-6').style('width: 50%; min-width: 600px;'):

            with ui.row().classes('gap-4 w-full').style('flex-wrap: nowrap;'):
                # --- User Summary Card (Wider) ---
                with ui.card().classes(CARD).style('flex: 1.5;'):
                    ui.label("👤 Profile").classes(SECTION_TITLE)
                    ui.label(f"{user['name']} — {user['age']} years, {user['gender']}").classes('text-gray-700 text-sm')
                    ui.label(f"📏 {user['height_cm']} cm").classes('text-gray-700 text-sm')
                    ui.label(f"⚖️ {user['weight_kg']} kg").classes('text-gray-700 text-sm')
                    ui.label(f"🏃 {user['activity_level']}").classes('text-gray-700 text-sm')
                    ui.label(f"🎯 {user['goal']}").classes('text-gray-700 text-sm')

                    ui.separator().classes('my-3 bg-emerald-200')

                    ui.label("📊 Metrics").classes('font-semibold text-emerald-800 mb-2 text-sm')
                    with ui.row().classes('gap-2 w-full'):
                        with ui.card().classes('p-2 bg-emerald-50 border border-emerald-200 rounded-lg flex-1'):
                            ui.label("BMI").classes('text-xs text-gray-600')
                            ui.label(f"{user['bmi']}").classes('text-xl font-bold text-emerald-700')
                        with ui.card().classes('p-2 bg-emerald-50 border border-emerald-200 rounded-lg flex-1'):
                            ui.label("BMR").classes('text-xs text-gray-600')
                            ui.label(f"{user['bmr']}").classes('text-xl font-bold text-emerald-700')
                        with ui.card().classes('p-2 bg-emerald-50 border border-emerald-200 rounded-lg flex-1'):
                            ui.label("Body Fat").classes('text-xs text-gray-600')
                            ui.label(f"{user['body_fat']}%").classes('text-xl font-bold text-emerald-700')

                # --- Update Weight Card ---
                with ui.card().classes(CARD).style('flex: 1;'):
                    ui.label("📉 Update Weight").classes(SECTION_TITLE)
                    new_w = ui.number("Current weight (kg)").classes('w-full')

                    def update_weight():
                        if new_w.value:
                            insert_weight(user_id, float(new_w.value))
                            bmi = calculate_bmi(new_w.value, user['height_cm'])
                            bmr = calculate_bmr(new_w.value, user['height_cm'], user['age'], user['gender'])
                            body_fat = calculate_body_fat(bmi, user['age'], user['gender'])

                            update_user(user_id, {
                                **user,
                                'weight_kg': new_w.value,
                                'bmi': bmi,
                                'bmr': bmr,
                                'body_fat': body_fat
                            })

                            ui.notify("Weight updated!", type='positive')
                            ui.navigate.to('/')

                    ui.button("Update", on_click=update_weight).classes(BTN + " mt-3 w-full")
                    
                    ui.separator().classes('my-3 bg-emerald-200')
                    
                    ui.label("💡 Quick Tips").classes('font-semibold text-emerald-800 mb-2 text-sm')
                    ui.label("• Weigh at same time daily").classes('text-xs text-gray-600')
                    ui.label("• Track weekly progress").classes('text-xs text-gray-600')
                    ui.label("• Stay consistent").classes('text-xs text-gray-600')

        # -------------------------
        # RIGHT COLUMN (Switchable Weight Chart / Recent Logs)
        # -------------------------
        with ui.column().classes('gap-6').style('width: 50%; min-width: 550px;'):

            # Switchable Card with Flip Animation
            view_state = {'current': 'chart'}  # Track current view
            
            with ui.card().classes(WIDE_CARD).style('perspective: 1000px; min-height: 600px;'):
                
                # Toggle Buttons
                with ui.row().classes('w-full justify-center gap-4 mb-4'):
                    chart_btn = ui.button("📈 Weight Chart", on_click=lambda: switch_view('chart')).classes(BTN)
                    logs_btn = ui.button("🗒️ Recent Logs", on_click=lambda: switch_view('logs')).classes(BTN_SECONDARY)
                
                # Content Container with flip animation
                content_container = ui.column().classes('w-full').style(
                    'transition: all 0.6s ease; transform-style: preserve-3d;'
                )
                
                def render_content():
                    content_container.clear()
                    with content_container:
                        if view_state['current'] == 'chart':
                            ui.label("📈 Weight Over Time").classes(SECTION_TITLE)
                            history = get_weight_history(user_id)
                            if history:
                                df = pd.DataFrame(history)
                                fig = px.line(df, x='Day', y='Weight', markers=True)
                                fig.update_traces(line_color='#059669', marker=dict(color='#059669', size=8))
                                fig.update_layout(
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    font=dict(color='#1f2937'),
                                    height=450,
                                    margin=dict(l=40, r=40, t=20, b=40)
                                )
                                ui.plotly(fig).classes('w-full')
                            else:
                                ui.label("No weight data available yet.").classes('text-gray-500 italic')
                        else:
                            ui.label("🗒️ Recent Logs").classes(SECTION_TITLE)
                            logs = get_logs()
                            if logs:
                                df = pd.DataFrame(logs)
                                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                                ui.table(
                                    columns=[
                                        {'name': c, 'label': c.replace("_", " ").title(), 'field': c}
                                        for c in df.columns
                                    ],
                                    rows=df.to_dict('records'),
                                    pagination=10
                                ).classes('w-full')
                            else:
                                ui.label("No logs yet.").classes('text-gray-500 italic')
                
                def switch_view(view):
                    if view_state['current'] != view:
                        view_state['current'] = view
                        
                        # Update button styles
                        if view == 'chart':
                            chart_btn.classes(replace=BTN)
                            logs_btn.classes(replace=BTN_SECONDARY)
                        else:
                            chart_btn.classes(replace=BTN_SECONDARY)
                            logs_btn.classes(replace=BTN)
                        
                        # Animate flip
                        content_container.style('opacity: 0; transform: rotateY(90deg);')
                        ui.timer(0.3, lambda: [
                            render_content(),
                            content_container.style('opacity: 1; transform: rotateY(0deg);')
                        ], once=True)
                
                render_content()

# ----------------------------------------
# Add User Page
# ----------------------------------------
@ui.page('/new-user')
def new_user():
    ui.query('body').classes(PAGE_BG)
    navbar()
    
    with ui.column().classes('w-full items-center mt-6 px-6'):
        ui.label("➕ Add User").classes(TITLE)

        with ui.row().classes('gap-6 w-full max-w-6xl'):
            # Left column: Personal Info
            with ui.column().classes('flex-1 gap-4'):
                with ui.card().classes(CARD):
                    ui.label('👤 Personal Information').classes(SECTION_TITLE)
                    name = ui.input('Name').classes('w-full')
                    age = ui.number('Age').classes('w-full')
                    gender = ui.select(['Male', 'Female'], label='Gender').classes('w-full')
                    
                    ui.separator().classes('my-4 bg-emerald-200')
                    ui.label('📏 Body Measurements').classes(SECTION_TITLE)
                    height = ui.number('Height (cm)').classes('w-full')
                    weight = ui.number('Weight (kg)').classes('w-full')
                    neck = ui.number('Neck (cm)').classes('w-full')
                    waist = ui.number('Waist (cm)').classes('w-full')
                    hip = ui.number('Hip (cm)').classes('w-full')

            # Right column: Activity & Goals
            with ui.column().classes('flex-1 gap-4'):
                with ui.card().classes(CARD):
                    ui.label('🎯 Activity & Goals').classes(SECTION_TITLE)
                    activity = ui.select(['Low', 'Medium', 'High'], label='Activity Level').classes('w-full')
                    goal = ui.select(['Lose Weight', 'Maintain', 'Gain Muscle'], label='Goal').classes('w-full')
                    
                    ui.separator().classes('my-4 bg-emerald-200')
                    ui.label('ℹ️ Instructions').classes(SECTION_TITLE)
                    ui.label('Fill in all information accurately. BMI, BMR, and body fat % will be calculated automatically.').classes('text-gray-600 mb-2')
                    ui.label('• Height and weight are required').classes('text-sm text-gray-500')
                    ui.label('• Body measurements help track progress').classes('text-sm text-gray-500')
                    ui.label('• Activity level affects calorie recommendations').classes('text-sm text-gray-500')

        def submit():
            bmi = calculate_bmi(weight.value, height.value)
            bmr = calculate_bmr(weight.value, height.value, age.value, gender.value)
            body_fat = calculate_body_fat(bmi, age.value, gender.value)

            data = {
                'name': name.value,
                'age': age.value,
                'gender': gender.value,
                'height_cm': height.value,
                'weight_kg': weight.value,
                'neck_cm': neck.value,
                'waist_cm': waist.value,
                'hip_cm': hip.value,
                'activity_level': activity.value,
                'goal': goal.value,
                'bmi': bmi,
                'bmr': bmr,
                'body_fat': body_fat,
            }

            user_id = insert_user(data)
            insert_weight(user_id, data['weight_kg'])
            ui.notify("User added!", type='positive')
            ui.navigate.to('/')

        with ui.row().classes('w-full max-w-6xl mt-4'):
            ui.button("💾 Save User Data", on_click=submit).classes(BTN + " w-full")


# ----------------------------------------
# Change Data Page
# ----------------------------------------
@ui.page('/change-data')
def change_data():
    ui.query('body').classes(PAGE_BG)
    navbar()
    user = get_latest_user()

    if not user:
        with ui.column().classes('items-center mt-20'):
            ui.label("No user found.").classes(TITLE)
        return

    with ui.column().classes('w-full items-center mt-6 px-6'):
        ui.label("✏️ Edit User Data").classes(TITLE)

        with ui.row().classes('gap-6 w-full max-w-6xl'):
            # Left column
            with ui.column().classes('flex-1 gap-4'):
                with ui.card().classes(CARD):
                    ui.label('👤 Personal Information').classes(SECTION_TITLE)
                    name = ui.input('Name', value=user['name']).classes('w-full')
                    age = ui.number('Age', value=user['age']).classes('w-full')
                    gender = ui.select(['Male', 'Female'], value=user['gender'], label='Gender').classes('w-full')
                    
                    ui.separator().classes('my-4 bg-emerald-200')
                    ui.label('📏 Body Measurements').classes(SECTION_TITLE)
                    height = ui.number('Height (cm)', value=user['height_cm']).classes('w-full')
                    weight = ui.number('Weight (kg)', value=user['weight_kg']).classes('w-full')
                    neck = ui.number('Neck (cm)', value=user['neck_cm']).classes('w-full')
                    waist = ui.number('Waist (cm)', value=user['waist_cm']).classes('w-full')
                    hip = ui.number('Hip (cm)', value=user['hip_cm']).classes('w-full')

            # Right column
            with ui.column().classes('flex-1 gap-4'):
                with ui.card().classes(CARD):
                    ui.label('🎯 Activity & Goals').classes(SECTION_TITLE)
                    activity = ui.select(['Low', 'Medium', 'High'], value=user['activity_level'], label='Activity Level').classes('w-full')
                    goal = ui.select(['Lose Weight', 'Maintain', 'Gain Muscle'], value=user['goal'], label='Goal').classes('w-full')
                    
                    ui.separator().classes('my-4 bg-emerald-200')
                    ui.label('⚠️ Important').classes(SECTION_TITLE)
                    ui.label('Update your information carefully. Weight changes are recorded automatically.').classes('text-gray-600')

        def save():
            bmi = calculate_bmi(weight.value, height.value)
            bmr = calculate_bmr(weight.value, height.value, age.value, gender.value)
            body_fat = calculate_body_fat(bmi, age.value, gender.value)

            update_user(user['id'], {
                'name': name.value,
                'age': age.value,
                'gender': gender.value,
                'height_cm': height.value,
                'weight_kg': weight.value,
                'neck_cm': neck.value,
                'waist_cm': waist.value,
                'hip_cm': hip.value,
                'activity_level': activity.value,
                'goal': goal.value,
                'bmi': bmi,
                'bmr': bmr,
                'body_fat': body_fat
            })

            insert_weight(user['id'], weight.value)
            ui.notify("Changes saved!", type='positive')
            ui.navigate.to('/')

        with ui.row().classes('w-full max-w-6xl mt-4'):
            ui.button("💾 Save Changes", on_click=save).classes(BTN + " w-full")


# ----------------------------------------
# Add Log Page
# ----------------------------------------
@ui.page('/add-log')
def add_log():
    ui.query('body').classes(PAGE_BG)
    navbar()
    user = get_latest_user()

    if not user:
        with ui.column().classes('items-center mt-20'):
            ui.label("No user found. Add a user first.").classes(TITLE)
        return

    with ui.column().classes('w-full items-center mt-6 px-6'):
        ui.label("🧾 Add Log Entry").classes(TITLE)

        with ui.card().classes(CARD + " max-w-2xl w-full"):
            log_type = ui.select(['Meal', 'Exercise'], label="Log Type").classes('w-full')
            content = ui.input("Description").classes('w-full')
            satisfaction = ui.number("Satisfaction (1-10)").classes('w-full')
            calories = ui.number("Calories (optional)").classes('w-full')

            def save_log():
                insert_log(user['id'], log_type.value, content.value, satisfaction.value, calories.value or 0)
                ui.notify("Log added!", type='positive')
                ui.navigate.to('/')

            ui.button("💾 Save Log", on_click=save_log).classes(BTN + " mt-4 w-full")


# ----------------------------------------
ui.run(title='Eaty – Personal Fitness Companion', reload=False)