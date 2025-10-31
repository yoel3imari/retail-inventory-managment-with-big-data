@startuml
title Simple Retail Inventory Architecture\nPOS to Power BI

skinparam nodesep 10
skinparam ranksep 15

package "Data Sources" {
  [POS Systems] as POS
  [Store Inventory] as INVENTORY
}

package "Data Pipeline" {
  [Kafka] as KAFKA
  [Spark Streaming] as SPARK
  [ClickHouse] as CH
  [MinIO] as MINIO
}

package "Machine Learning" {
  [Spark MLlib] as ML
  [Airflow] as AIRFLOW
}

package "API & Analytics" {
  [FastAPI] as API
  [Power BI] as PBI
}

package "Users" {
  [Store Managers] as MANAGERS
  [Executives] as EXECUTIVES
}

' === DATA FLOW WITH MINIO ===
POS --> KAFKA : Sales Events
INVENTORY --> KAFKA : Stock Updates

KAFKA --> SPARK : Real-time Stream
SPARK --> CH : Aggregated Data
SPARK --> MINIO : Raw Data (Parquet)

AIRFLOW --> ML : Train Models
ML --> MINIO : Save Models
ML --> CH : Predictions

MINIO --> API : Load ML Models
CH --> API : Query Data
CH --> PBI : Direct Query

API --> MANAGERS : Mobile App
PBI --> EXECUTIVES : Dashboards

note right of MINIO
**Data Lake**
- Raw data storage
- ML model registry
- Historical archives
end note
@enduml