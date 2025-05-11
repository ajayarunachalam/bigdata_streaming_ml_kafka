#! /usr/bin/env python

import json
from kafka import KafkaConsumer

KAFKA_PREDICTIONS_TOPIC = "iot_predictions"
KAFKA_BROKERS = ["localhost:9092"]

consumer = KafkaConsumer(
    KAFKA_PREDICTIONS_TOPIC,
    bootstrap_servers=KAFKA_BROKERS,
    auto_offset_reset='earliest',
    group_id='predictions-display-group',
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

print(f"Listening for predictions on topic '{KAFKA_PREDICTIONS_TOPIC}'...")
try:
    for message in consumer:
        prediction_data = message.value
        print(f"Received Prediction: {prediction_data}")
except KeyboardInterrupt:
    print("Stopping prediction consumer...")
finally:
    consumer.close()
    print("Prediction consumer closed.")