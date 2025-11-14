import sqlite3

# Connect to the database
conn = sqlite3.connect('fitnessapp.db', check_same_thread=False)
c = conn.cursor()


# ---------------------------
# BMI, BMR, Body Fat
# ---------------------------
def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI given weight (kg) and height (cm)."""
    return round(weight_kg / ((height_cm / 100) ** 2), 2)


def calculate_bmr(weight_kg, height_cm, age, gender):
    """Calculate BMR using Mifflin-St Jeor Equation."""
    if gender.lower() == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(bmr, 2)


def calculate_body_fat(bmi, age, gender, waist_cm, hip_cm):
    """Estimate body fat percentage using BMI, age, gender, waist, and hip measurements, using Deurenberg formula."""
    if gender.lower() == 'male':
        body_fat = 1.20 * bmi + 0.23 * age - 16.2
    else:
        body_fat = 1.20 * bmi + 0.23 * age - 5.4
    # Optionally, adjust with waist-hip ratio for more accuracy
    if waist_cm and hip_cm:
        whr = waist_cm / hip_cm
        body_fat += (whr - 0.5) * 10  # simple adjustment
    return round(body_fat, 2)


# ---------------------------
# Average Calorie Burn
# ---------------------------
def calculate_avg_burn(user):
    """Calculate the average calories burned from the last 7 exercise logs for a user."""
    user_id = user['id']
    c.execute("""
        SELECT calories FROM logs
        WHERE user_id = ? AND type = 'Exercise'
        ORDER BY timestamp DESC
        LIMIT 7
    """, (user_id,))
    rows = c.fetchall()
    if not rows:
        # Fallback to BMR-based estimate using activity level
        bmr = user['bmr']
        activity_level = user['activity_level']
        
        # Activity multipliers
        activity_multipliers = {
            'Low': 1.2,
            'Medium': 1.55,
            'High': 1.9
        }
        
        multiplier = activity_multipliers.get(activity_level, 1.2)
        # TDEE minus BMR gives approximate activity burn
        tdee = bmr * multiplier
        estimated_activity_burn = tdee - bmr
        
        return round(estimated_activity_burn, 2)
    
    avg_calorie_burn = sum([row[0] for row in rows]) / len(rows)
    return round(avg_calorie_burn, 2)
