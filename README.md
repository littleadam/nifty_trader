

# **NSE Options Trading Application - Requirements Document**  
**Version:** 1.0  
**Date:** 15/4/2025
**Author:** Adam

---

## **1. Introduction**  
### **1.1 Purpose**  
This document outlines the complete requirements for a production-grade **automated options trading system** built on Zerodha Kite API, supporting **short straddle and strangle strategies** with integrated risk management.  

### **1.2 Scope**  
- Supports **NIFTY index options** trading  
- Implements **short straddle and strangle strategies**  
- Includes **real-time data streaming**, **order management**, and **risk controls**  
- Runs on **Google Colab** with automated setup  

---

## **2. Functional Requirements**  

### **2.1 Core Trading Strategies**  

#### **2.1.1 Short Straddle**  
| Requirement ID | Description |  
|---------------|------------|  
| ST-01 | Sell ATM call and put options with configurable bias (`BIAS` parameter) |  
| ST-02 | Default strike selection: Nearest to `(Spot + BIAS)` |  
| ST-03 | Quantity: Fixed `LOT_SIZE` (default: 50) |  
| ST-04 | Expiry: Current weekly or far monthly (configurable via `FAR_MONTH_INDEX`) |  

#### **2.1.2 Short Strangle**  
| Requirement ID | Description |  
|---------------|------------|  
| ST-05 | Sell OTM calls and puts at `±STRANGLE_GAP` (default: 1000 points) from spot |  
| ST-06 | Strike adjustment to maintain minimum gap if conflicts exist |  
| ST-07 | Quantity: Same as straddle (`LOT_SIZE`) |  

#### **2.1.3 Profit Booking**  
| Requirement ID | Description |  
|---------------|------------|  
| PB-01 | Modify SL to **90% of entry price** when profit reaches `PROFIT_POINTS` (default: 250 pts) |  
| PB-02 | Add 1 additional lot if `ADD_ON_PROFIT=True` (disabled by default) |  

---

### **2.2 Order Management**  

#### **2.2.1 Order Placement**  
| Requirement ID | Description |  
|---------------|------------|  
| OM-01 | **Prevent duplicate positions**: Reject orders for same strike/expiry |  
| OM-02 | **Close opposing BUY positions** before placing new SELL orders |  
| OM-03 | **Fallback mechanism**: Market order → Limit order (5% worse price) |  

#### **2.2.2 Stop-Loss**  
| Requirement ID | Description |  
|---------------|------------|  
| SL-01 | Initial SL: **50 points** (`POSITION_STOPLOSS`) |  
| SL-02 | SL order type: `ORDER_TYPE_SL` (trigger-based) |  

---

### **2.3 Risk Management**  

#### **2.3.1 Shutdown Triggers**  
| Requirement ID | Description |  
|---------------|------------|  
| RM-01 | **Profit target**: 250 points per side (`PROFIT_POINTS`) |  
| RM-02 | **Portfolio loss**: 12.5% (`SHUTDOWN_LOSS`) |  
| RM-03 | **Position SL**: 50 points breach (`POSITION_STOPLOSS`) |  
| RM-04 | **Margin utilization**: 75% (`MARGIN_UTILIZATION_LIMIT`) |  

#### **2.3.2 Circuit Breakers**  
| Requirement ID | Description |  
|---------------|------------|  
| CB-01 | Reject orders if bid-ask spread > 5% (`MAX_SPREAD_PCT`) |  
| CB-02 | Auto-reconnect if WebSocket data is stale (>60 sec) |  

---

### **2.4 Expiry Handling**  

| Requirement ID | Description |  
|---------------|------------|  
| EX-01 | **Far-month expiry**: 3rd monthly expiry (`FAR_MONTH_INDEX=3`) |  
| EX-02 | **Hedge rollover**: Close weekly hedges 1 day before expiry (`ROLLOVER_DAYS_THRESHOLD=1`) |  
| EX-03 | **Strike selection**: Premium-based for hedges (< `HEDGE_PREMIUM_THRESHOLD=20`) |  

---

### **2.5 Hedging Rules**  

| Requirement ID | Description |  
|---------------|------------|  
| HG-01 | **Fixed quantity**: 1 lot (`HEDGE_ONE_LOT=True`) |  
| HG-02 | **Strike distance**: Minimum `2×ADJACENCY_GAP` from spot |  
| HG-03 | **Expiry**: Weekly only |  

---

## **3. Non-Functional Requirements**  

### **3.1 Technical Specifications**  

| Requirement ID | Description |  
|---------------|------------|  
| NF-01 | **API**: Zerodha Kite Connect (WebSocket + REST) |  
| NF-02 | **Data**: Real-time ticks (WebSocket) + historical (Kite API) |  
| NF-03 | **Execution**: Thread-safe with Locking (`threading.Lock`) |  

### **3.2 Performance**  

| Requirement ID | Description |  
|---------------|------------|  
| PF-01 | **Rate limiting**: 1 order/sec (`rate_limit_delay=1`) |  
| PF-02 | **WebSocket token limit**: 3000 tokens (Zerodha constraint) |  

### **3.3 Reliability**  

| Requirement ID | Description |  
|---------------|------------|  
| RL-01 | **Retry logic**: 3 attempts for API calls (exponential backoff) |  
| RL-02 | **Data validation**: Reject stale ticks (>60 sec old) |  

### **3.4 Security**  

| Requirement ID | Description |  
|---------------|------------|  
| SC-01 | **Credentials**: Stored in `.env` (excluded from Git) |  
| SC-02 | **Authentication**: OAuth2 flow with `localhost:80` redirect |  

---

## **4. Operational Requirements**  

### **4.1 Trading Hours**  

| Requirement ID | Description |  
|---------------|------------|  
| OP-01 | **Active hours**: 9:15 AM - 3:30 PM IST |  
| OP-02 | **Days**: Mon-Fri (`TRADE_DAYS`) |  

### **4.2 Logging & Monitoring**  

| Requirement ID | Description |  
|---------------|------------|  
| LM-01 | **Log format**: JSON with timestamps |  
| LM-02 | **File rotation**: 10MB max, 5 backups |  
| LM-03 | **Decision tracking**: `DecisionLogger` for critical events |  

---

## **5. Deployment Requirements**  

### **5.1 Google Colab Setup**  

| Requirement ID | Description |  
|---------------|------------|  
| DP-01 | **Automated install**: `setup.py` handles dependencies |  
| DP-02 | **Token generation**: Auto-updates `.env` |  
| DP-03 | **Pre-flight checks**: Runs tests before main execution |  

---

## **6. Assumptions & Constraints**  

- **Market**: Only NIFTY index options (no equities)  
- **Broker**: Zerodha Kite API (no multi-broker support)  
- **Risk**: Assumes MIS orders (auto-square-off)  

---

## **7. Appendix**  

### **7.1 Configuration Reference**  
See `config.py` for all tunable parameters.  

### **7.2 Test Coverage**  
- Unit tests: `tests/test_strategies.py` (90%+ coverage)  
- Integration: Manual via `main.py`  

--- 

**Approval**  
Prepared by: Adam  
Reviewed by: Adam 
Date: 15/4/2025

--- 
