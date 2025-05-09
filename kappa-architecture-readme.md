# Kappa Architecture Implementation with Python, Kafka and Scikit-learn

This project demonstrates an end-to-end implementation of Kappa Architecture using Python, Kafka, and Scikit-learn for IoT sensor data processing and anomaly detection.

## Overview

Kappa Architecture is a simplification of Lambda Architecture where all data processing is done through a single stream processing path, rather than maintaining separate batch and speed layers. This implementation showcases:

- **Single Source of Truth**: All raw and processed data originates from Kafka topics
- **Stream Processing**: Python scripts simulate stream processors for feature extraction and model training
- **Real-time Predictions**: Continuous consumption of raw data with real-time inference

## Project Scenario

We simulate an IoT environment where sensors send temperature and humidity readings. The system predicts "power consumption anomalies" based on these readings.

## Components

1. **Kafka**: Message broker running in Docker
2. **Data Producer** (`producer.py`): Simulates IoT sensors sending data to `iot_raw_data` topic
3. **Training Pipeline** (`training_pipeline.py`): 
   - Consumes data from `iot_raw_data`
   - Performs feature engineering
   - Trains a Scikit-learn model
   - Saves the model
4. **Inference Pipeline** (`inference_pipeline.py`):
   - Consumes real-time data from `iot_raw_data`
   - Applies the same feature engineering
   - Makes predictions using the trained model
   - Sends predictions to `iot_predictions` topic
5. **Prediction Consumer** (`consumer_predictions.py`): Displays predictions from the `iot_predictions` topic

## Setup Instructions

### 1. Start Kafka using Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.3.2
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.3.2
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "29092:29092" # For external access if needed from outside docker network
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9093,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true" # For simplicity in example
```

Start Kafka:
```bash
docker-compose up -d
```

### 2. Install Required Python Packages

Create a `requirements.txt` file:
```
kafka-python
scikit-learn
pandas
numpy
joblib
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Example

Open 4 terminal windows/tabs and run the following commands in sequence:

### Terminal 1: Data Producer
```bash
python producer.py
```
This will generate a stream of simulated IoT data.

### Terminal 2: Training Pipeline
```bash
python training_pipeline.py
```
This will collect data, train a model, and save it as `iot_anomaly_model.pkl`.

### Terminal 3: Inference Pipeline
```bash
python inference_pipeline.py
```
This will process new messages in real-time and generate predictions.

### Terminal 4: Prediction Consumer
```bash
python consumer_predictions.py
```
This will display the predictions made by the inference pipeline.

## Stopping the Example

1. Press `Ctrl+C` in each terminal to stop the running scripts
2. Stop Kafka and Zookeeper with:
   ```bash
   docker-compose down
   ```

## Key Concepts Demonstrated

- **Data Source**: `iot_raw_data` Kafka topic serves as the single source for both training and inference
- **Stream Processing**: Both training data preparation and real-time inference consume from the same stream
- **Retraining/Reprocessing**: Model retraining can be done by re-running the training pipeline on the same data source

## Kappa Architecture Illustrated:
- **Data Source**: iot_raw_data Kafka topic is the single source for both training data preparation and real-time inference.
- **Stream Processing**:
training_pipeline.py reads from the stream, "processes" it (collects and transforms), and trains a model. This is the "batch" part of Kappa, but it's sourced from the stream.
inference_pipeline.py reads from the stream, processes individual messages, and applies the model in near real-time.
- **Retraining/Reprocessing**:
To retrain the model with more data, you'd simply re-run training_pipeline.py. It will read from iot_raw_data again (from earliest offset within its consumer group, or up to a certain point if you manage offsets more carefully).
If your feature engineering logic changes, you update it in both training_pipeline.py and inference_pipeline.py, retrain, and redeploy. The new inference pipeline will then use the updated logic on new incoming data.

## Potential Improvements

- Replace Python scripts with robust stream processing frameworks like Apache Spark Streaming, Apache Flink, or Kafka Streams
- Implement a feature store to ensure consistency in feature engineering
- Add model versioning using tools like MLflow
- Use Avro/Protobuf with Schema Registry for data validation
- Implement state management for complex features (e.g., rolling averages)
- Add monitoring for Kafka, stream processing jobs, and model performance
- Implement robust error handling with Dead Letter Queues (DLQs)
- Containerize applications for deployment with Kubernetes/YARN

## File Structure

```
kappa-architecture-example/
├── docker-compose.yml
├── requirements.txt
├── producer.py
├── training_pipeline.py
├── inference_pipeline.py
├── consumer_predictions.py
└── iot_anomaly_model.pkl (generated during execution)
```
