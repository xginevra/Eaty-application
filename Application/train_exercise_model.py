# train_exercise_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load dataset
df = pd.read_csv("weight_loss_training_data.csv")

# Encode categorical features
le_sex = LabelEncoder()
df["sex"] = le_sex.fit_transform(df["sex"])  # Male=1, Female=0 (typically)

le_exercise = LabelEncoder()
df["main_exercise"] = le_exercise.fit_transform(df["main_exercise"])

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
        "avg_calorie_intake",
        "avg_calorie_burn",
    ]
]
y = df["main_exercise"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Initialize and train model
model = RandomForestClassifier(
    n_estimators=250, random_state=42, max_depth=14, n_jobs=-1
)
model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print("Exercise Model Evaluation:")
print(f"  Accuracy: {acc:.3f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=le_exercise.classes_))

# Save model and encoders
joblib.dump(model, "exercise_model.joblib")
joblib.dump(le_sex, "sex_label_encoder.joblib")  # can reuse the same one
joblib.dump(le_exercise, "exercise_label_encoder.joblib")

print("✅ Model saved as 'exercise_model.joblib'")
