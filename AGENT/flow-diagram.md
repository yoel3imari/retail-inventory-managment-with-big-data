@startuml
title Complete Flow with MinIO

rectangle "🏪 STORES" as STORES {
  (POS Sales)
  (Inventory Scans)
}

rectangle "🔄 PIPELINE" as PIPELINE {
  component "Kafka" as K
  component "Spark" as S
  component "ClickHouse" as C
  component "MinIO" as M
}

rectangle "🤖 INTELLIGENCE" as INTELLIGENCE {
  component "MLlib" as ML
  component "Airflow" as A
}

rectangle "📊 RESULTS" as RESULTS {
  component "FastAPI" as F
  component "Power BI" as P
}

STORES --> K : Real-time events
K --> S : Process stream
S --> C : Aggregated data
S --> M : Raw data storage

A --> ML : Train models
ML --> M : Save models
ML --> C : Write predictions

M --> F : Load models
C --> F : Query data
C --> P : Dashboards


note right of M
**MinIO = Data Lake**
• Raw data (cheap)
• ML models (versioned)
• Features (reusable)
end note
@enduml