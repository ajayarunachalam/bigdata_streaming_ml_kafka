#! /usr/bin/env python

import json
import time
from kafka import KafkaConsumer
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier # Or any other model
from sklearn.metrics import accuracy_score
import joblib

KAFKA_RAW_TOPIC = "iot_raw_data"
KAFKA_BROKERS = ["localhost:9092"]
MODEL_PATH = "iot_anomaly_model.pkl"
TRAINING_DATA_COLLECTION_SIZE = 100 # Collect N messages for training

def preprocess_data(df):
    # Simple feature engineering (can be more complex)
    # For this example, we'll just use raw temp and humidity
    # In real cases: scaling, encoding, creating interaction terms, etc.
    if 'temperature' not in df.columns or 'humidity' not in df.columns:
        print("Warning: 'temperature' or 'humidity' missing from DataFrame.")
        return pd.DataFrame(), pd.Series() # Return empty if crucial columns missing

    features = df[['temperature', 'humidity']]
    if 'power_consumption_anomaly' in df.columns:
        target = df['power_consumption_anomaly']
        return features, target
    return features, pd.Series() # Return features only if target is not present (for inference)


print(f"Starting training pipeline. Will collect {TRAINING_DATA_COLLECTION_SIZE} messages for training...")

consumer = KafkaConsumer(
    KAFKA_RAW_TOPIC,
    bootstrap_servers=KAFKA_BROKERS,
    auto_offset_reset='earliest', # Start from the beginning of the topic for training
    group_id='training-pipeline-group', # Unique group ID
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    consumer_timeout_ms=10000 # Timeout if no messages for 10s
)

collected_data = []
try:
    for message in consumer:
        data = message.value
        collected_data.append(data)
        print(f"Collected message {len(collected_data)}/{TRAINING_DATA_COLLECTION_SIZE}: {data['message_id']}")
        if len(collected_data) >= TRAINING_DATA_COLLECTION_SIZE:
            break
    print(f"Collected {len(collected_data)} messages.")

except Exception as e:
    print(f"Error during message consumption for training: {e}")
finally:
    consumer.close()


if len(collected_data) < 10: # Need a minimum amount of data
    print("Not enough data collected for training. Exiting.")
    exit()

# Convert to DataFrame
df = pd.DataFrame(collected_data)

# Preprocess
X, y = preprocess_data(df.copy()) # Pass a copy to avoid modifying original df during preprocessing

if X.empty or y.empty:
    print("Preprocessing failed or resulted in empty features/target. Exiting training.")
    exit()

if len(y.unique()) < 2:
    print(f"Only one class present in the target variable after collecting {len(df)} samples. Cannot train a classifier. Exiting.")
    # This can happen if TRAINING_DATA_COLLECTION_SIZE is too small and all collected samples have the same anomaly status.
    # Try increasing TRAINING_DATA_COLLECTION_SIZE or run the producer for longer before starting this script.
    exit()

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train model
print("Training model...")
model = RandomForestClassifier(n_estimators=50, random_state=42) # Simpler model
model.fit(X_train, y_train)

# Evaluate (optional for this example, but good practice)
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"Model trained. Test Accuracy: {acc:.4f}")

# Save model
joblib.dump(model, MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")
print("Training pipeline finished.")