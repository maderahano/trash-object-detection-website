#!/bin/bash

source /opt/Kafka/kafka_2.11-1.0.1/
sudo bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1  --partitions 1 --topic testing