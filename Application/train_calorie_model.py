# train_calorie_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Load dataset
df = pd.read_csv("weight_loss_training_data.csv")

# Encode categorical feature 'sex'
le_sex = LabelEncoder()
df["sex"] = le_sex.fit_transform(df["sex"])  # Male=1, Female=0 (typically)

# Define features and target
X = df[
    [
        "age",
        "sex",
        "height_cm",
        "start_weight_kg",
        "target_weight_kg",
        "duration_weeks",
        "start_bmi",
        "target_bmi",
        "avg_calorie_burn",
    ]
]
y = df["avg_calorie_intake"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Initialize and train model
model = RandomForestRegressor(
    n_estimators=200, random_state=42, max_depth=12, n_jobs=-1
)
model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("Calorie Intake Model Evaluation:")
print(f"  MAE: {mae:.2f}")
print(f"  R²: {r2:.3f}")

# Save model and encoder
joblib.dump(model, "calorie_intake_model.joblib")
joblib.dump(le_sex, "sex_label_encoder.joblib")

print("✅ Model saved as 'calorie_intake_model.joblib'")
