#! /usr/bin/env python

import json
import time
from kafka import KafkaConsumer, KafkaProducer
import pandas as pd
import joblib
import os

KAFKA_RAW_TOPIC = "iot_raw_data"
KAFKA_PREDICTIONS_TOPIC = "iot_predictions"
KAFKA_BROKERS = ["localhost:9092"]
MODEL_PATH = "iot_anomaly_model.pkl"

# --- Re-use preprocessing logic from training ---
def preprocess_data_for_inference(df):
    if 'temperature' not in df.columns or 'humidity' not in df.columns:
        print("Warning: 'temperature' or 'humidity' missing from DataFrame for inference.")
        return pd.DataFrame() # Return empty if crucial columns missing
    features = df[['temperature', 'humidity']]
    return features
# ---

if not os.path.exists(MODEL_PATH):
    print(f"Model file {MODEL_PATH} not found. Please run the training_pipeline.py first.")
    exit()

print("Loading model...")
model = joblib.load(MODEL_PATH)
print("Model loaded.")

consumer = KafkaConsumer(
    KAFKA_RAW_TOPIC,
    bootstrap_servers=KAFKA_BROKERS,
    auto_offset_reset='latest', # Process only new messages for inference
    group_id='inference-pipeline-group', # Different group ID from training
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print(f"Starting inference pipeline. Consuming from '{KAFKA_RAW_TOPIC}', producing to '{KAFKA_PREDICTIONS_TOPIC}'...")
try:
    for message in consumer:
        data = message.value
        print(f"Received for inference: {data['message_id']}")

        # Create DataFrame for preprocessing
        df_inference = pd.DataFrame([data]) # Process one message at a time
        
        # Preprocess (must be consistent with training)
        features = preprocess_data_for_inference(df_inference.copy())

        if features.empty:
            print(f"Skipping message {data['message_id']} due to preprocessing issue.")
            continue

        # Make prediction
        prediction_proba = model.predict_proba(features)[0] # Probabilities for [class_0, class_1]
        prediction = int(model.predict(features)[0]) # Class label

        output_message = {
            "original_message_id": data["message_id"],
            "device_id": data["device_id"],
            "timestamp": data["timestamp"],
            "temperature": data["temperature"],
            "humidity": data["humidity"],
            "predicted_anomaly": prediction,
            "anomaly_probability": round(float(prediction_proba[1]), 4) # Probability of being an anomaly
        }

        producer.send(KAFKA_PREDICTIONS_TOPIC, value=output_message)
        print(f"Sent prediction: {output_message}")

except KeyboardInterrupt:
    print("Stopping inference pipeline...")
finally:
    consumer.close()
    producer.flush()
    producer.close()
    print("Inference pipeline closed.")