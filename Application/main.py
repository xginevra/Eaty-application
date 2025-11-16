from nicegui import ui
import pandas as pd
import sqlite3
from datetime import datetime, date
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
BTN_SECONDARY = 'bg-emerald-500 text-white px-6 py-2 rounded-lg hover:bg-emerald-600 border-2 border-emerald-600 transition-colors'
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
    
    # Add custom CSS to override NiceGUI button colors
    ui.add_head_html("""
    <style>
        .q-btn {
            background-color: #059669 !important;
            color: white !important;
        }
        .q-btn:hover {
            background-color: #047857 !important;
        }
        /* For secondary buttons (inactive state) */
        .q-btn.bg-emerald-500 {
            background-color: #10b981 !important;
        }
        .q-btn.bg-emerald-500:hover {
            background-color: #059669 !important;
        }
    </style>
    """)
    
    user = get_latest_user()

    if not user:
        with ui.column().classes('items-center mt-20'):
            ui.label("No user found. Please add your data first.").classes(TITLE)
            ui.button("➕ Add User", on_click=lambda: ui.navigate.to('/new-user')).classes(BTN)
        return

    user_id = user['id']

    with ui.row().classes('w-full gap-6 mt-6 px-6').style('flex-wrap: nowrap;'):
        
        # -------------------------
        # LEFT COLUMN (Profile + Daily Tracking side by side)
        # -------------------------
        with ui.column().classes('gap-6').style('width: 50%; min-width: 600px;'):

            with ui.row().classes('gap-4 w-full').style('flex-wrap: nowrap;'):
                # --- User Summary Card ---
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

                # --- Daily Tracking Card with Tabs ---
                with ui.card().classes(CARD).style('flex: 1;'):
                    ui.label("📊 Daily Tracking").classes(SECTION_TITLE)
                    
                    # Tabs for different tracking options
                    with ui.tabs().classes('w-full') as tabs:
                        weight_tab = ui.tab('⚖️ Weight')
                        meal_tab = ui.tab('🍽️ Meal')
                        exercise_tab = ui.tab('🏃 Exercise')
                    
                    with ui.tab_panels(tabs, value=weight_tab).classes('w-full'):
                        # Weight Update Panel
                        with ui.tab_panel(weight_tab):
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

                            ui.button("Update Weight", on_click=update_weight).classes(BTN + " mt-3 w-full")
                        
                        # Meal Logging Panel
                        with ui.tab_panel(meal_tab):
                            meal_desc = ui.input("Meal description").classes('w-full')
                            meal_cals = ui.number("Calories (intake)").classes('w-full')
                            meal_satisfaction = ui.slider(min=1, max=10, value=5).classes('w-full')
                            ui.label().bind_text_from(meal_satisfaction, 'value', 
                                                      backward=lambda v: f'Satisfaction: {v}/10').classes('text-xs text-gray-600')

                            def log_meal():
                                if meal_desc.value and meal_cals.value:
                                    insert_log(user_id, 'Meal', meal_desc.value, meal_satisfaction.value, meal_cals.value)
                                    ui.notify(f"Meal logged! +{int(meal_cals.value)} cal", type='positive')
                                    # Update today's balance
                                    update_balance()
                                    meal_desc.value = ''
                                    meal_cals.value = None
                                    meal_satisfaction.value = 5
                                else:
                                    ui.notify("Please fill in description and calories", type='warning')

                            ui.button("Log Meal", on_click=log_meal).classes(BTN + " mt-3 w-full")
                        
                        # Exercise Logging Panel
                        with ui.tab_panel(exercise_tab):
                            exercise_desc = ui.input("Exercise description").classes('w-full')
                            exercise_cals = ui.number("Calories burned").classes('w-full')
                            exercise_satisfaction = ui.slider(min=1, max=10, value=5).classes('w-full')
                            ui.label().bind_text_from(exercise_satisfaction, 'value', 
                                                       backward=lambda v: f'Intensity: {v}/10').classes('text-xs text-gray-600')

                            def log_exercise():
                                if exercise_desc.value and exercise_cals.value:
                                    # Store as negative calories to indicate burn
                                    insert_log(user_id, 'Exercise', exercise_desc.value, exercise_satisfaction.value, -exercise_cals.value)
                                    ui.notify(f"Exercise logged! -{int(exercise_cals.value)} cal", type='positive')
                                    # Update today's balance
                                    update_balance()
                                    exercise_desc.value = ''
                                    exercise_cals.value = None
                                    exercise_satisfaction.value = 5
                                else:
                                    ui.notify("Please fill in description and calories", type='warning')

                            ui.button("Log Exercise", on_click=log_exercise).classes(BTN + " mt-3 w-full")
                    
                    ui.separator().classes('my-3 bg-emerald-200')
                    
                    # Daily Calorie Summary (Container for dynamic updates)
                    ui.label("📈 Today's Balance").classes('font-semibold text-emerald-800 mb-2 text-sm')
                    balance_container = ui.row().classes('gap-2 w-full justify-between')
                    
                    def update_balance():
                        # Calculate today's totals
                        today = date.today().strftime('%Y-%m-%d')
                        logs = get_logs()
                        
                        calories_in = 0
                        calories_out = 0
                        
                        if logs:
                            df_logs = pd.DataFrame(logs)
                            df_logs['date'] = pd.to_datetime(df_logs['timestamp']).dt.date.astype(str)
                            today_logs = df_logs[df_logs['date'] == today]
                            
                            if not today_logs.empty:
                                meal_logs = today_logs[today_logs['type'] == 'Meal']
                                exercise_logs = today_logs[today_logs['type'] == 'Exercise']
                                
                                calories_in = meal_logs['calories'].sum() if not meal_logs.empty else 0
                                # Exercise calories are stored as negative, so we negate them to show positive burn
                                calories_out = -exercise_logs['calories'].sum() if not exercise_logs.empty else 0
                        
                        net_calories = calories_in - calories_out
                        
                        # Update the UI
                        balance_container.clear()
                        with balance_container:
                            with ui.card().classes('p-2 bg-green-50 border border-green-200 rounded-lg flex-1 text-center'):
                                ui.label("Intake").classes('text-xs text-gray-600')
                                ui.label(f"+{int(calories_in)}").classes('text-lg font-bold text-green-600')
                            with ui.card().classes('p-2 bg-orange-50 border border-orange-200 rounded-lg flex-1 text-center'):
                                ui.label("Burned").classes('text-xs text-gray-600')
                                ui.label(f"-{int(calories_out)}").classes('text-lg font-bold text-orange-600')
                            with ui.card().classes('p-2 bg-blue-50 border border-blue-200 rounded-lg flex-1 text-center'):
                                ui.label("Net").classes('text-xs text-gray-600')
                                ui.label(f"{int(net_calories):+}").classes('text-lg font-bold text-blue-600')
                    
                    # Initial render
                    update_balance()

        # -------------------------
        # RIGHT COLUMN (Switchable Charts / Recent Logs)
        # -------------------------
        with ui.column().classes('gap-6').style('width: 50%; min-width: 550px;'):

            # Switchable Card with Flip Animation
            view_state = {'current': 'weight'}  # Track current view
            
            with ui.card().classes(WIDE_CARD).style('perspective: 1000px; min-height: 600px;'):
                
                # Toggle Buttons
                with ui.row().classes('w-full justify-center gap-4 mb-4'):
                    weight_btn = ui.button("📈 Weight", on_click=lambda: switch_view('weight')).classes(BTN)
                    calories_btn = ui.button("🔥 Calories", on_click=lambda: switch_view('calories')).classes(BTN_SECONDARY)
                    logs_btn = ui.button("🗒️ Logs", on_click=lambda: switch_view('logs')).classes(BTN_SECONDARY)
                
                # Content Container with flip animation
                content_container = ui.column().classes('w-full').style(
                    'transition: all 0.6s ease; transform-style: preserve-3d;'
                )
                
                def render_content():
                    content_container.clear()
                    with content_container:
                        if view_state['current'] == 'weight':
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
                        
                        elif view_state['current'] == 'calories':
                            ui.label("🔥 Today's Calorie Tracking").classes(SECTION_TITLE)
                            logs = get_logs()
                            
                            today = date.today().strftime('%Y-%m-%d')
                            
                            if logs and len(logs) > 0:
                                try:
                                    df_logs = pd.DataFrame(logs)
                                    df_logs['date'] = pd.to_datetime(df_logs['timestamp']).dt.date.astype(str)
                                    
                                    # Filter for today only
                                    today_logs = df_logs[df_logs['date'] == today]
                                    
                                    if not today_logs.empty:
                                        # Sort by timestamp
                                        today_logs = today_logs.sort_values('timestamp')
                                        today_logs['time'] = pd.to_datetime(today_logs['timestamp']).dt.strftime('%H:%M')
                                        
                                        # Separate meals and exercise
                                        meals = today_logs[today_logs['type'] == 'Meal'].copy()
                                        exercises = today_logs[today_logs['type'] == 'Exercise'].copy()
                                        
                                        # Create cumulative tracking
                                        cumulative_data = []
                                        cumulative_intake = 0
                                        cumulative_burned = 0
                                        
                                        for idx, row in today_logs.iterrows():
                                            if row['type'] == 'Meal':
                                                cumulative_intake += row['calories']
                                            else:  # Exercise
                                                cumulative_burned += -row['calories']
                                            
                                            cumulative_data.append({
                                                'time': row['time'],
                                                'Intake': cumulative_intake,
                                                'Burned': cumulative_burned,
                                                'Net': cumulative_intake - cumulative_burned
                                            })
                                        
                                        if cumulative_data:
                                            df_cumulative = pd.DataFrame(cumulative_data)
                                            
                                            # Create figure
                                            fig = px.line(df_cumulative, x='time', y=['Intake', 'Burned', 'Net'],
                                                        color_discrete_map={
                                                            'Intake': '#10b981',
                                                            'Burned': '#f59e0b',
                                                            'Net': '#3b82f6'
                                                        },
                                                        markers=True)
                                            
                                            fig.update_layout(
                                                plot_bgcolor='rgba(0,0,0,0)',
                                                paper_bgcolor='rgba(0,0,0,0)',
                                                font=dict(color='#1f2937'),
                                                height=450,
                                                margin=dict(l=40, r=40, t=20, b=40),
                                                legend=dict(
                                                    orientation="h",
                                                    yanchor="bottom",
                                                    y=1.02,
                                                    xanchor="right",
                                                    x=1
                                                ),
                                                xaxis_title="Time",
                                                yaxis_title="Calories"
                                            )
                                            
                                            ui.plotly(fig).classes('w-full')
                                            
                                            # Today's summary
                                            total_intake = cumulative_intake
                                            total_burned = cumulative_burned
                                            net_today = total_intake - total_burned
                                            
                                            with ui.row().classes('gap-4 mt-4 w-full justify-around'):
                                                with ui.card().classes('p-3 bg-green-50 border border-green-200 rounded-lg'):
                                                    ui.label("Today's Intake").classes('text-xs text-gray-600')
                                                    ui.label(f"+{int(total_intake)} cal").classes('text-lg font-bold text-green-600')
                                                
                                                with ui.card().classes('p-3 bg-orange-50 border border-orange-200 rounded-lg'):
                                                    ui.label("Today's Burned").classes('text-xs text-gray-600')
                                                    ui.label(f"-{int(total_burned)} cal").classes('text-lg font-bold text-orange-600')
                                                
                                                with ui.card().classes('p-3 bg-blue-50 border border-blue-200 rounded-lg'):
                                                    ui.label("Today's Net").classes('text-xs text-gray-600')
                                                    ui.label(f"{int(net_today):+} cal").classes('text-lg font-bold text-blue-600')
                                            
                                            # Log details
                                            ui.separator().classes('my-4 bg-emerald-200')
                                            ui.label("Today's Activities").classes('font-semibold text-emerald-800 mb-2')
                                            
                                            with ui.column().classes('w-full gap-2'):
                                                for idx, row in today_logs.iterrows():
                                                    icon = '🍽️' if row['type'] == 'Meal' else '🏃'
                                                    cal_sign = '+' if row['type'] == 'Meal' else '-'
                                                    cal_color = 'text-green-600' if row['type'] == 'Meal' else 'text-orange-600'
                                                    
                                                    with ui.card().classes('p-3 bg-gray-50 border border-gray-200 rounded-lg'):
                                                        with ui.row().classes('w-full items-center justify-between'):
                                                            ui.label(f"{icon} {row['content']}").classes('font-medium')
                                                            ui.label(f"{cal_sign}{abs(int(row['calories']))} cal").classes(f'font-bold {cal_color}')
                                                        ui.label(row['time']).classes('text-xs text-gray-500')
                                        else:
                                            ui.label("No activities logged yet today.").classes('text-gray-500 italic')
                                    else:
                                        ui.label("No activities logged yet today. Start tracking!").classes('text-gray-500 italic')
                                except Exception as e:
                                    ui.label(f"Error loading calorie data: {str(e)}").classes('text-red-500')
                            else:
                                ui.label("No calorie data available yet. Start logging meals and exercises!").classes('text-gray-500 italic')
                        
                        else:  # logs view
                            ui.label("🗒️ Recent Logs").classes(SECTION_TITLE)
                            logs = get_logs()
                            if logs:
                                df = pd.DataFrame(logs)
                                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                                # Display absolute calorie values in table
                                df['calories'] = df['calories'].abs()
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
                        if view == 'weight':
                            weight_btn.classes(replace=BTN)
                            calories_btn.classes(replace=BTN_SECONDARY)
                            logs_btn.classes(replace=BTN_SECONDARY)
                        elif view == 'calories':
                            weight_btn.classes(replace=BTN_SECONDARY)
                            calories_btn.classes(replace=BTN)
                            logs_btn.classes(replace=BTN_SECONDARY)
                        else:
                            weight_btn.classes(replace=BTN_SECONDARY)
                            calories_btn.classes(replace=BTN_SECONDARY)
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
            ui.label("No user found.")
            return

    with ui.column().classes('w-full items-center mt-6 px-6'):
        ui.label("🧾 Add Log Entry").classes(TITLE)

        with ui.card().classes(CARD + " max-w-2xl w-full"):
            log_type = ui.select(['Meal', 'Exercise'], label="Log Type").classes('w-full')
            content = ui.input("Description").classes('w-full')
            satisfaction = ui.number("Satisfaction (1-10)").classes('w-full')
            calories = ui.number("Calories").classes('w-full')

            def save_log():
                if log_type.value and content.value and calories.value:
                    # If exercise, store as negative
                    cal_value = -calories.value if log_type.value == 'Exercise' else calories.value
                    insert_log(user['id'], log_type.value, content.value, satisfaction.value or 5, cal_value)
                    ui.notify("Log added!", type='positive')
                    ui.navigate.to('/')
                else:
                    ui.notify("Please fill in all required fields", type='warning')

            ui.button("💾 Save Log", on_click=save_log).classes(BTN + " mt-4 w-full")


# ----------------------------------------
ui.run(title='Eaty – Personal Fitness Companion', reload=False)