@startuml
title Business Value Chain

rectangle "INPUT" {
  (Store Sales) as SALES
  (Inventory Data) as STOCK
}

rectangle "PROCESS" {
  (Real-time Pipeline) as PIPELINE
  (ML Predictions) as PREDICT
}

rectangle "OUTPUT" {
  (Power BI Dashboards) as DASH
  (Manager Alerts) as ALERTS
}

rectangle "IMPACT" {
  (No Stock-outs) as STOCKOUT
  (Less Overstock) as OVERSTOCK
  (Happy Customers) as CUSTOMERS
}

SALES -> PIPELINE
STOCK -> PIPELINE
PIPELINE -> PREDICT
PREDICT -> DASH
PREDICT -> ALERTS
DASH -> STOCKOUT
ALERTS -> OVERSTOCK
STOCKOUT -> CUSTOMERS
OVERSTOCK -> CUSTOMERS

note on link  
  Automated intelligence
  drives business results
end note
@enduml