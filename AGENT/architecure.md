┌─────────────────────────────────────────────────────────────┐
│                    RETAIL STORES (POS)                       │
├─────────────────────────────────────────────────────────────┤
│  Store 1    │  Store 2    │  Store 3    │  ... Store N     │
│  Location   │  Location   │  Location   │  Locations       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Events Generated:
                            │ • Sales transactions
                            │ • Product scans
                            │ • Returns/refunds
                            │ • Price changes
                            │ • Shelf stock counts
                            │ • Customer foot traffic
                            ▼
```

---

### **Layer 2: Event Streaming (Apache Kafka)**
```
┌─────────────────────────────────────────────────────────────┐
│                      KAFKA TOPICS                            │
├─────────────────────────────────────────────────────────────┤
│  📦 sales-transactions    │  Real-time sales data           │
│  📊 inventory-updates     │  Stock level changes            │
│  🔔 restock-alerts        │  Low stock notifications        │
│  💰 price-changes         │  Pricing updates                │
│  👥 customer-events       │  Foot traffic, basket size      │
│  🚚 supplier-shipments    │  Incoming deliveries            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

---

### **Layer 3: Real-Time Processing (Spark Streaming + MLlib)**
```
┌─────────────────────────────────────────────────────────────┐
│              SPARK STRUCTURED STREAMING                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Stream Processor:                                           │
│  ├─ Consume from Kafka topics                               │
│  ├─ Data validation & cleansing                             │
│  ├─ Real-time aggregations (5-min windows)                  │
│  ├─ Join streams (sales + inventory + pricing)              │
│  └─ Anomaly detection (unusual sales spikes/drops)          │
│                                                              │
│  Real-Time Metrics:                                          │
│  • Sales velocity per product/store                         │
│  • Current stock levels                                     │
│  • Stock-out risk score                                     │
│  • Revenue per hour/store                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
```

---

### **Layer 4: Storage Layer**
```
┌──────────────────────────┐    ┌──────────────────────────┐
│      MINIO (Data Lake)   │    │   CLICKHOUSE (OLAP DB)   │
├──────────────────────────┤    ├──────────────────────────┤
│                          │    │                          │
│ 📁 Raw Data:             │    │ 📊 Aggregated Tables:    │
│  • Transaction logs      │    │  • daily_sales_summary   │
│  • Inventory snapshots   │    │  • inventory_by_store    │
│  • Parquet files         │    │  • product_performance   │
│                          │    │  • customer_analytics    │
│ 🤖 ML Assets:            │    │  • stock_movements       │
│  • Trained models        │    │  • reorder_predictions   │
│  • Feature pipelines     │    │  • ml_forecast_results   │
│  • Model versions        │    │                          │
│                          │    │ ⚡ Optimized for:        │
│ 📂 Historical Data:      │    │  • Power BI queries      │
│  • Years of sales data   │    │  • DirectQuery mode      │
│  • Seasonal patterns     │    │  • Materialized views    │
│                          │    │  • Pre-aggregated data   │
│                          │    │                          │
└──────────────────────────┘    └──────────────────────────┘
                │                              │
                └──────────┬───────────────────┘
                           ▼
```

---

### **Layer 5: Orchestration (Apache Airflow)**
```
┌─────────────────────────────────────────────────────────────┐
│                    AIRFLOW DAG WORKFLOWS                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔄 Daily ETL Pipeline (8:00 AM):                           │
│    └─ Extract previous day sales                            │
│    └─ Transform and aggregate                               │
│    └─ Load into ClickHouse feature store                    │
│    └─ Refresh Power BI datasets                             │
│                                                              │
│  🧪 Feature Engineering (9:00 AM):                          │
│    └─ Calculate rolling averages (7, 30, 90 days)          │
│    └─ Seasonality features (holidays, weekends)            │
│    └─ Store-specific patterns                               │
│    └─ Product category trends                               │
│                                                              │
│  🤖 Model Training (Weekly - Sunday 2:00 AM):              │
│    └─ Train demand forecasting models                       │
│    └─ Train stock optimization models                       │
│    └─ Hyperparameter tuning                                 │
│    └─ Model evaluation & versioning                         │
│    └─ Deploy best model to production                       │
│                                                              │
│  📈 Batch Predictions (Daily 10:00 AM):                     │
│    └─ Generate 7-day demand forecasts                       │
│    └─ Calculate optimal reorder points                      │
│    └─ Identify slow-moving inventory                        │
│    └─ Write predictions to ClickHouse                       │
│    └─ Trigger Power BI dataset refresh                      │
│                                                              │
│  🔍 Data Quality Checks (Hourly):                           │
│    └─ Validate incoming data                                │
│    └─ Check for missing stores                              │
│    └─ Detect data anomalies                                 │
│                                                              │
│  📊 Power BI Data Preparation (Every 15 mins):             │
│    └─ Create aggregated views for dashboards               │
│    └─ Update materialized views in ClickHouse              │
│    └─ Optimize query performance                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

---

### **Layer 6: Machine Learning (Spark MLlib)**
```
┌─────────────────────────────────────────────────────────────┐
│                    ML MODELS & ANALYTICS                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🎯 Demand Forecasting Model:                               │
│    Algorithm: Gradient Boosted Trees (GBT)                  │
│    Features:                                                 │
│    • Historical sales (7, 14, 30, 90 days)                  │
│    • Day of week, month, season                             │
│    • Promotions & discounts                                 │
│    • Weather data (temperature, rain)                       │
│    • Local events & holidays                                │
│    • Product category & brand                               │
│    Output: Predicted sales per product/store (next 7 days)  │
│                                                              │
│  📦 Stock Optimization Model:                               │
│    Algorithm: Linear Regression + Business Rules            │
│    Features:                                                 │
│    • Forecasted demand                                      │
│    • Current inventory levels                               │
│    • Lead time from suppliers                               │
│    • Storage capacity constraints                           │
│    • Product shelf life                                     │
│    Output: Optimal reorder quantity & timing                │
│                                                              │
│  🚨 Anomaly Detection Model:                                │
│    Algorithm: Isolation Forest                              │
│    Detects:                                                  │
│    • Sudden sales drops (supply issues?)                    │
│    • Unexpected spikes (viral products)                     │
│    • Inventory discrepancies (theft/damage)                 │
│    • Pricing errors                                         │
│                                                              │
│  🔄 Slow-Moving Inventory Classifier:                       │
│    Algorithm: Random Forest Classification                  │
│    Predicts:                                                 │
│    • Products at risk of expiration                         │
│    • Items to markdown/promote                              │
│    • Seasonal items to clear                                │
│                                                              │
│  🎁 Product Recommendation (Cross-sell):                    │
│    Algorithm: ALS (Alternating Least Squares)               │
│    • Basket analysis                                         │
│    • Product affinity scoring                               │
│    • Store-level recommendations                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
```

---

### **Layer 7: Analytics & Visualization (Power BI)**
```
┌─────────────────────────────────────────────────────────────┐
│                    POWER BI ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔌 Data Connections:                                        │
│    ┌──────────────────────────────────────┐                │
│    │  ClickHouse ODBC/JDBC Connector      │                │
│    │  • DirectQuery mode (real-time)      │                │
│    │  • Import mode (scheduled refresh)   │                │
│    └──────────────────────────────────────┘                │
│                                                              │
│  📊 Power BI Service (Cloud):                               │
│    ├─ Published Reports                                     │
│    ├─ Scheduled Dataset Refreshes (every 15 min)           │
│    ├─ Power BI Gateway (on-premise connector)              │
│    └─ Row-Level Security (RLS) by store/region             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   POWER BI DASHBOARDS                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📈 EXECUTIVE DASHBOARD                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  KPI Cards:                                         │    │
│  │  💰 Total Revenue: $2.4M (↑ 12% vs last week)     │    │
│  │  📦 Stock Value: $1.8M                             │    │
│  │  ⚠️  Stock-Outs Today: 23 items                    │    │
│  │  📊 Inventory Turnover: 8.2x                       │    │
│  │                                                     │    │
│  │  Charts:                                            │    │
│  │  • Revenue by Region (Map Visual)                  │    │
│  │  • Sales Trend (Line Chart - last 90 days)        │    │
│  │  • Top 10 Products (Bar Chart)                     │    │
│  │  • Store Performance Matrix (Heatmap)              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  🏪 STORE MANAGER DASHBOARD                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Real-Time Metrics (Auto-refresh every 15 min):    │    │
│  │  • Current Inventory Levels by Category            │    │
│  │  • Low Stock Alerts (Red indicators)               │    │
│  │  • Today's Sales vs Target (Gauge)                 │    │
│  │                                                     │    │
│  │  ML Predictions Section:                           │    │
│  │  📊 7-Day Demand Forecast (Line + Confidence)      │    │
│  │  🎯 Recommended Reorders (Table with quantities)   │    │
│  │  ⚡ Stock-Out Risk Score (Traffic light)           │    │
│  │                                                     │    │
│  │  Interactive Filters:                               │    │
│  │  • Date Range Slider                               │    │
│  │  • Product Category Dropdown                        │    │
│  │  • Store Location Slicer                           │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  📦 INVENTORY ANALYST DASHBOARD                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Deep Dive Analytics:                               │    │
│  │  • Inventory Aging Analysis (Column Chart)         │    │
│  │  • Slow-Moving Items (Table with risk scores)      │    │
│  │  • Overstock vs Understock (Scatter Plot)          │    │
│  │  • Supplier Performance (KPI Cards)                │    │
│  │  • ABC Analysis (Products by value contribution)   │    │
│  │                                                     │    │
│  │  Predictive Analytics:                              │    │
│  │  • Demand vs Forecast Accuracy (Line Chart)        │    │
│  │  • Reorder Point Optimization (Table)              │    │
│  │  • Seasonal Pattern Visualization                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  🤖 ML MODEL PERFORMANCE DASHBOARD                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Model Metrics:                                     │    │
│  │  • Forecast Accuracy: MAPE, RMSE (by product)      │    │
│  │  • Model Drift Detection (Time series)             │    │
│  │  • Prediction vs Actual Sales (Scatter Plot)       │    │
│  │  • Feature Importance (Bar Chart)                  │    │
│  │  • Model Confidence Intervals                      │    │
│  │                                                     │    │
│  │  Business Impact:                                   │    │
│  │  • Cost Savings from Optimization                  │    │
│  │  • Stock-Outs Prevented                            │    │
│  │  • Overstock Reduction                             │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  🔔 ALERTS & NOTIFICATIONS DASHBOARD                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Critical Alerts (Real-Time):                       │    │
│  │  🚨 Urgent: 15 products below safety stock          │    │
│  │  ⚠️  Warning: 8 stores with high overstock          │    │
│  │  📈 Opportunity: 5 products showing viral trends    │    │
│  │                                                     │    │
│  │  Alert Table with Actions:                         │    │
│  │  | Priority | Store | Product | Issue | Action |   │    │
│  │  |----------|-------|---------|-------|---------|   │    │
│  │  | High     | #047  | SKU123  | Stock | Reorder |   │    │
│  │                                                     │    │
│  │  Power BI Alerts Configuration:                    │    │
│  │  • Email notifications on threshold breach         │    │
│  │  • Mobile app push notifications                   │    │
│  │  • Teams/Slack integration                         │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  POWER BI FEATURES UTILIZED                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🎯 Advanced Features:                                       │
│    • DirectQuery: Real-time data from ClickHouse            │
│    • Automatic Page Refresh: Every 15 minutes               │
│    • Row-Level Security (RLS): Store managers see only      │
│      their stores, regional managers see their region       │
│    • Drillthrough: Click product → see detailed analytics   │
│    • Bookmarks: Save custom views and filters               │
│    • What-If Parameters: Scenario planning                  │
│                                                              │
│  📱 Mobile Optimization:                                     │
│    • Mobile layouts for store managers on-the-go           │
│    • Touch-optimized visuals                               │
│    • Offline mode with last cached data                     │
│                                                              │
│  🔗 Integration:                                            │
│    • Embed reports in internal web apps                     │
│    • Export to PowerPoint for presentations                │
│    • Schedule email reports (PDF/Excel)                    │
│    • Power Automate flows for alert workflows              │
│                                                              │
│  🎨 Custom Visuals (from AppSource):                        │
│    • Advanced KPI cards                                     │
│    • Sankey diagrams for inventory flow                    │
│    • Heatmap calendars for seasonal patterns               │
│    • Forecast charts with confidence intervals             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Data Flow (End-to-End)
```
1. TRANSACTION OCCURS
   Customer buys product at Store #47
   ↓
   
2. EVENT PUBLISHED
   POS system → Kafka topic "sales-transactions"
   {product_id: "SKU123", quantity: 2, store_id: 47, timestamp: ...}
   ↓
   
3. REAL-TIME PROCESSING
   Spark Streaming consumes event
   • Updates running inventory count
   • Checks stock levels
   • Calculates sales velocity
   ↓
   
4. STORAGE
   • Raw event → MinIO (Parquet)
   • Aggregated metrics → ClickHouse
   • Materialized views updated for Power BI
   ↓
   
5. POWER BI REAL-TIME UPDATE
   DirectQuery mode fetches latest data
   • Store manager's dashboard updates automatically
   • Current stock level shows: 13 units remaining
   ↓
   
6. DAILY BATCH PROCESSING (Next Day - 8:00 AM)
   Airflow triggers:
   • Feature extraction job
   • Enriches with historical patterns
   • Refreshes Power BI datasets
   ↓
   
7. ML PREDICTION (10:00 AM)
   • Load demand forecast model from MinIO
   • Predict next 7 days sales for SKU123 at Store #47
   • Calculate optimal reorder point
   • Write predictions to ClickHouse
   ↓
   
8. POWER BI VISUALIZATION
   Store Manager Dashboard shows:
   • Current stock: 13 units
   • 7-day forecast: 45 units needed
   • Recommendation: ORDER 50 units
   • Stock-out risk: 85% (RED alert)
   ↓
   
9. ALERTING
   Power BI Data Alert triggers:
   • Email sent to store manager
   • Mobile notification on Power BI app
   • Teams message to procurement team
   ↓
   
10. ACTION TAKEN
    Store manager reviews recommendation in Power BI
    • Drills through to see historical trends
    • Approves reorder from dashboard
    • Purchase order generated
```

---

## 📊 Power BI Data Model Structure
```
┌─────────────────────────────────────────────────────────────┐
│                    STAR SCHEMA DESIGN                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  FACT TABLES (from ClickHouse):                             │
│  ┌──────────────────────────────┐                          │
│  │  fact_sales                   │                          │
│  │  • sale_id (PK)               │                          │
│  │  • date_key (FK)              │                          │
│  │  • product_key (FK)           │                          │
│  │  • store_key (FK)             │                          │
│  │  • quantity                   │                          │
│  │  • revenue                    │                          │
│  │  • cost                       │                          │
│  │  • profit                     │                          │
│  └──────────────────────────────┘                          │
│                                                              │
│  ┌──────────────────────────────┐                          │
│  │  fact_inventory               │                          │
│  │  • inventory_id (PK)          │                          │
│  │  • date_key (FK)              │                          │
│  │  • product_key (FK)           │                          │
│  │  • store_key (FK)             │                          │
│  │  • quantity_on_hand           │                          │
│  │  • reorder_point              │                          │
│  │  • safety_stock               │                          │
│  └──────────────────────────────┘                          │
│                                                              │
│  ┌──────────────────────────────┐                          │
│  │  fact_ml_predictions          │                          │
│  │  • prediction_id (PK)         │                          │
│  │  • date_key (FK)              │                          │
│  │  • product_key (FK)           │                          │
│  │  • store_key (FK)             │                          │
│  │  • predicted_demand           │                          │
│  │  • confidence_low             │                          │
│  │  • confidence_high            │                          │
│  │  • stock_out_risk_score       │                          │
│  └──────────────────────────────┘                          │
│                                                              │
│  DIMENSION TABLES:                                           │
│  ┌──────────────────────────────┐                          │
│  │  dim_date                     │                          │
│  │  • date_key (PK)              │                          │
│  │  • full_date                  │                          │
│  │  • day_of_week                │                          │
│  │  • month                      │                          │
│  │  • quarter                    │                          │
│  │  • year                       │                          │
│  │  • is_holiday                 │                          │
│  │  • is_weekend                 │                          │
│  └──────────────────────────────┘                          │
│                                                              │
│  ┌──────────────────────────────┐                          │
│  │  dim_product                  │                          │
│  │  • product_key (PK)           │                          │
│  │  • sku                        │                          │
│  │  • product_name               │                          │
│  │  • category                   │                          │
│  │  • sub_category               │                          │
│  │  • brand                      │                          │
│  │  • supplier                   │                          │
│  │  • unit_cost                  │                          │
│  │  • shelf_life_days            │                          │
│  └──────────────────────────────┘                          │
│                                                              │
│  ┌──────────────────────────────┐                          │
│  │  dim_store                    │                          │
│  │  • store_key (PK)             │                          │
│  │  • store_id                   │                          │
│  │  • store_name                 │                          │
│  │  • city                       │                          │
│  │  • region                     │                          │
│  │  • country                    │                          │
│  │  • square_footage             │                          │
│  │  • store_type                 │                          │
│  └──────────────────────────────┘                          │
│                                                              │
│  RELATIONSHIPS:                                              │
│  • One-to-Many from dimensions to facts                     │
│  • Bi-directional filtering where needed                    │
│  • Row-Level Security on dim_store                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Power BI Security & Governance
```
┌─────────────────────────────────────────────────────────────┐
│                  SECURITY ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Row-Level Security (RLS) Rules:                            │
│  ┌──────────────────────────────────────────────────┐      │
│  │  Role: Store Manager                              │      │
│  │  DAX Filter:                                      │      │
│  │  [Store].[store_id] = USERPRINCIPALNAME()        │      │
│  │  → Can only see their assigned store              │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  Role: Regional Manager                           │      │
│  │  DAX Filter:                                      │      │
│  │  [Store].[region] = LOOKUPVALUE(...)             │      │
│  │  → Can see all stores in their region             │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  Role: Executive                                  │      │
│  │  No filter → Full access to all data              │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  Authentication:                                             │
│  • Azure AD integration                                     │
│  • Single Sign-On (SSO)                                     │
│  • Multi-Factor Authentication (MFA)                        │
│                                                              │
│  Data Refresh Security:                                     │
│  • Power BI Gateway with service account                   │
│  • ClickHouse connection credentials in Azure Key Vault    │
│  • Encrypted connections (TLS/SSL)                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Business Use Cases with Power BI

### **Use Case 1: Morning Store Manager Routine**
**Scenario**: Store manager arrives at 8 AM
- Opens Power BI Mobile App
- Views overnight sales summary
- Sees 3 red alerts for low stock items
- Drills through to see 7-day forecast
- Taps "Approve Reorder" button
- Purchase order auto-generated

**Power BI Features Used**:
- Mobile layout
- Data alerts
- Drillthrough pages
- Embedded actions

---

### **Use Case 2: Regional Manager Performance Review**
**Scenario**: Monthly review meeting
- Opens Executive Dashboard on laptop
- Filters by region: "Northeast"
- Compares store performance (heatmap)
- Identifies underperforming stores
- Exports report to PowerPoint
- Shares in Teams meeting

**Power BI Features Used**:
- Slicers and filters
- Heatmap visuals
- Export to PowerPoint
- Teams integration

---

### **Use Case 3: Inventory Analyst Optimization**
**Scenario**: Quarterly inventory optimization
- Opens Inventory Analyst Dashboard
- Runs ABC analysis (80/20 rule)
- Identifies slow-moving products
- Uses What-If parameters to test reorder strategies
- Downloads detailed Excel report
- Presents recommendations to procurement

**Power BI Features Used**:
- What-If parameters
- Export to Excel
- Custom DAX measures
- Bookmarks for scenarios

---

### **Use Case 4: Real-Time Demand Spike**
**Scenario**: Viral product on social media
- Anomaly detection model detects spike
- Power BI alert triggered automatically
- Procurement team receives notification
- Opens dashboard, sees forecast updated
- Expedites supplier orders
- Prevents stock-out

**Power BI Features Used**:
- Data alerts
- Auto-refresh (15 min)
- Mobile notifications
- DirectQuery real-time data

---

## 📦 Data Pipeline Summary

| Component | Role | Technology | Power BI Integration |
|-----------|------|------------|---------------------|
| **POS Systems** | Generate transaction events | Retail software | Source data |
| **Kafka** | Real-time event streaming | Apache Kafka | Feeds ClickHouse |
| **Spark Streaming** | Process events in real-time | Apache Spark | Prepares aggregations |
| **MinIO** | Store raw data & ML models | S3-compatible storage | Backup/archive |
| **ClickHouse** | Fast analytical queries | Columnar database | **Primary Power BI source** |
| **Airflow** | Orchestrate batch jobs | Apache Airflow | Triggers dataset refresh |
| **MLlib** | Train & deploy ML models | Spark MLlib | Predictions visualized in Power BI |
| **Power BI** | Analytics & visualization | Microsoft Power BI | **End-user interface** |

---

## 🚀 Key Benefits with Power BI

✅ **Real-Time Dashboards**: Auto-refresh every 15 minutes via DirectQuery  
✅ **Mobile Access**: Store managers make decisions on-the-go  
✅ **Self-Service Analytics**: Users create custom reports without IT  
✅ **Enterprise Security**: Row-level security, SSO, audit logs  
✅ **Familiar Interface**: Microsoft ecosystem integration (Teams, Excel, SharePoint)  
✅ **Scalability**: Handles millions of rows with aggregated views  
✅ **Cost-Effective**: Pay-per-user licensing model  
✅ **Actionable Insights**: Alerts drive immediate business actions  

---

## 🔧 Power BI Technical Setup
```
ClickHouse Connection Setup:
1. Install Power BI Gateway (on-premise data gateway)
2. Configure ClickHouse ODBC driver
3. Create data source in Power BI Service
4. Set up scheduled refresh (every 15 minutes)
5. Configure DirectQuery for real-time tables
6. Set up row-level security roles
7. Publish reports to Power BI workspace
8. Share with appropriate user groups