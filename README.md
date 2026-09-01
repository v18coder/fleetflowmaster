# FleetFlow Master: Modular Fleet & Logistics Management System

FleetFlow replaces inefficient manual logbooks with a centralized, rule-based digital hub optimizing the lifecycle of delivery fleets, monitoring driver safety, and tracking financial performance.

## Core Features (8 Modules)
1. **Login & RBAC**: Role-based access control for Fleet Managers, Dispatchers, Safety Officers, and Financial Analysts with quick demo login buttons.
2. **Command Center (Dashboard)**: High-level overview with 4 KPIs (Active Fleet, Maintenance Alerts, Utilization Rate %, Pending Cargo), multi-dimensional filtering, and live fleet monitoring.
3. **Vehicle Registry**: Asset lifecycle tracking, maximum load capacities, odometer gauges, and "Out of Service" (Retired) toggling.
4. **Trip Dispatcher**: Point A to Point B dispatch lifecycle (`Draft` -> `Dispatched` -> `Completed` -> `Cancelled`) with automated payload capacity checks and driver category validation.
5. **Maintenance & Service Logs**: Service log tracking with **Auto-Logic** that automatically switches vehicle status to `In Shop` and removes it from dispatch availability until resolved.
6. **Fuel & Operational Expenses**: Refill tracking, trip-linked expense logging, and automated Total Operational Cost (`Fuel + Maintenance + Expenses`) aggregation.
7. **Driver Profiles & Safety**: License expiration tracking with alert badges, safety score ratings, and duty toggles (`On Duty`, `Off Duty`, `Suspended`).
8. **Operational Analytics & Reports**: Fuel efficiency (`km/L`), Cost-per-km metrics, vehicle ROI calculator, and one-click CSV/printable PDF audit exports.

## Quick Start

```bash
# 1. Navigate to directory
cd D:\VIVEK\FLEET-FLOW\fleetflowmaster

# 2. Run application
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## Demo Credentials
* **Manager**: `manager@fleetflow.com` / `password123`
* **Dispatcher**: `dispatcher@fleetflow.com` / `password123`
* **Safety Officer**: `safety@fleetflow.com` / `password123`
* **Financial Analyst**: `finance@fleetflow.com` / `password123`
