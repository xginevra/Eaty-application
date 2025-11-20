# ml_models.py

import joblib
import pandas as pd
import numpy as np

# Load the saved models and encoders
try:
    CALORIE_MODEL = joblib.load('calorie_intake_model.joblib')
    EXERCISE_MODEL = joblib.load('exercise_model.joblib')
    SEX_ENCODER = joblib.load('sex_label_encoder.joblib')
    EXERCISE_ENCODER = joblib.load('exercise_label_encoder.joblib') # New encoder
except FileNotFoundError:
    print("WARNING: One or more ML models not found. Ensure training scripts were run.")
    CALORIE_MODEL = None
    EXERCISE_MODEL = None
    SEX_ENCODER = None
    EXERCISE_ENCODER = None


def _encode_sex(gender_label):
    """Helper to encode gender safely."""
    if SEX_ENCODER is None: return 1 # Default to Male if encoder fails
    try:
        return SEX_ENCODER.transform([gender_label])[0]
    except:
        return 1 # Fallback


def get_predicted_intake_target(user, target_weight_kg, duration_weeks, avg_calorie_burn):
    """
    Predicts the required daily calorie intake using the Random Forest Regressor model.
    """
    if CALORIE_MODEL is None or SEX_ENCODER is None:
        # Simple rule-based fallback if model is missing
        tdee = user['bmr'] * (1.55 if user['activity_level'] == 'Medium' else 1.2)
        target_intake = tdee - 500 if user['goal'] == 'Lose Weight' else tdee
        return int(max(1200, target_intake))

    # --- Feature Engineering ---
    height_m = user['height_cm'] / 100.0
    start_bmi = user['weight_kg'] / (height_m ** 2)
    target_bmi = target_weight_kg / (height_m ** 2)
    
    sex_encoded = _encode_sex(user['gender'])

    # --- Create Input DataFrame for Prediction ---
    input_data = pd.DataFrame([{
        "age": user['age'],
        "sex": sex_encoded,
        "height_cm": user['height_cm'],
        "start_weight_kg": user['weight_kg'],
        "target_weight_kg": target_weight_kg,
        "duration_weeks": duration_weeks,
        "start_bmi": start_bmi,
        "target_bmi": target_bmi,
        "avg_calorie_burn": abs(avg_calorie_burn),
    }])

    # --- Prediction ---
    predicted_intake = CALORIE_MODEL.predict(input_data)[0]
    safe_intake = max(1200, predicted_intake)
    
    return int(round(safe_intake / 10.0) * 10)


def propose_exercise(user, target_weight_kg, duration_weeks, avg_calorie_burn, predicted_intake):
    """
    Predicts the suggested main exercise using the Random Forest Classifier model.
    """
    if EXERCISE_MODEL is None or EXERCISE_ENCODER is None:
        # Simple rule-based fallback if model is missing
        if predicted_intake < 1500 or user['activity_level'] == 'Low':
            return "Low-Impact Cardio (e.g., Walking)"
        else:
            return "Strength Training + Interval Cardio (e.g., HIIT)"

    # --- Feature Engineering ---
    height_m = user['height_cm'] / 100.0
    start_bmi = user['weight_kg'] / (height_m ** 2)
    target_bmi = target_weight_kg / (height_m ** 2)
    
    sex_encoded = _encode_sex(user['gender'])

    # --- Create Input DataFrame for Prediction ---
    input_data = pd.DataFrame([{
        "age": user['age'],
        "sex": sex_encoded,
        "height_cm": user['height_cm'],
        "start_weight_kg": user['weight_kg'],
        "target_weight_kg": target_weight_kg,
        "duration_weeks": duration_weeks,
        "start_bmi": start_bmi,
        "target_bmi": target_bmi,
        # Crucially, include the prediction from the first model
        "avg_calorie_intake": predicted_intake, 
        "avg_calorie_burn": abs(avg_calorie_burn),
    }])

    # --- Prediction ---
    exercise_encoded = EXERCISE_MODEL.predict(input_data)[0]
    
    # Decode the result
    return EXERCISE_ENCODER.inverse_transform([exercise_encoded])[0]