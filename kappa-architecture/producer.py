#! /usr/bin/env python

import json
import time
import random
from kafka import KafkaProducer
import uuid

KAFKA_TOPIC = "iot_raw_data"
KAFKA_BROKERS = ["localhost:9092"]

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all' # Ensure messages are written
)

print(f"Starting IoT data producer for topic '{KAFKA_TOPIC}'...")
try:
    while True:
        device_id = f"device_{random.randint(1, 5)}"
        temperature = round(random.uniform(15.0, 35.0), 2)
        humidity = round(random.uniform(30.0, 70.0), 2)

        # Simple logic for synthetic anomaly target
        # Anomalies more likely with very high temp/humidity or very low
        anomaly_chance = 0.05
        if temperature > 32 or humidity > 65 or temperature < 18 or humidity < 35:
            anomaly_chance = 0.3 # Higher chance if values are extreme

        is_anomaly = 1 if random.random() < anomaly_chance else 0

        message = {
            "message_id": str(uuid.uuid4()),
            "device_id": device_id,
            "timestamp": time.time(),
            "temperature": temperature,
            "humidity": humidity,
            "power_consumption_anomaly": is_anomaly # Our target variable
        }

        producer.send(KAFKA_TOPIC, value=message)
        print(f"Sent: {message}")
        time.sleep(random.uniform(0.5, 2)) # Send data at random intervals

except KeyboardInterrupt:
    print("Stopping producer...")
finally:
    producer.flush()
    producer.close()
    print("Producer closed.")