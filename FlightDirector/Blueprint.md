# SPLAT Flight Director - Deployment Configuration Form
-----------------------------------------------------------

## Organization Information
Organization Name: _____________________________________
Department: __________________________________________
Project Name: _______________________________________
Deployment Contact: __________________________________
Emergency Contact: ___________________________________

## Environment Selection
[ ] Development
[ ] Staging
[ ] Production

## Ground Control Configuration
-----------------------------------------------------------
Station ID: _______________  (e.g., gc-prod-01)
Location Name: _____________ (e.g., North Field Station)

Geographic Location:
  Latitude: _____________
  Longitude: ____________
  Elevation (m): ________

Network Configuration:
  IP Address: _________________
  Subnet Mask: ________________
  Gateway: ___________________
  DNS Servers: ________________
  SSH Port: __________________ (default: 22)

Hardware Configuration:
  [ ] Raspberry Pi 4B (4GB)
  [ ] Raspberry Pi 4B (8GB)
  [ ] Custom Hardware: _____________

LoRa Configuration:
  Frequency (MHz): ________ (default: 915.0)
  Bandwidth (kHz): ________ (default: 125)
  Spreading Factor: _______ (default: 7)
  TX Power (dBm): ________ (default: 20)
  Sync Word: _____________ (default: 0x42)

## Cloud Configuration
-----------------------------------------------------------
GCP Project ID: ____________________________________
Region: _________________________________________ (e.g., us-central1)
Zone: ___________________________________________ (e.g., us-central1-a)

Service Account:
  [ ] Create New
  [ ] Use Existing: _________________________________

Required Services:
  [x] IoT Core
  [x] Pub/Sub
  [x] Cloud Storage
  [x] Cloud Functions
  [ ] BigQuery
  [ ] Cloud Run

## Monitoring Configuration
-----------------------------------------------------------
Alert Recipients:
  Email: _________________________________________
  Phone: _________________________________________
  Webhook URL: __________________________________

Monitoring Level:
  [ ] Basic (System metrics only)
  [ ] Standard (System + Application metrics)
  [ ] Advanced (System + Application + Custom metrics)

Metrics Retention:
  [ ] 15 days
  [ ] 30 days
  [ ] 60 days
  [ ] 90 days

Dashboard Access:
  [ ] Public (View only)
  [ ] Private (Authentication required)
  [ ] Custom: ____________________________________

## Backup Configuration
-----------------------------------------------------------
Backup Schedule:
  [ ] Daily
  [ ] Weekly
  [ ] Custom: ____________________________________

Retention Period:
  [ ] 30 days
  [ ] 60 days
  [ ] 90 days
  [ ] Custom: ___________________________________

Backup Location:
  [ ] Same Region
  [ ] Multi-Region
  [ ] Custom Bucket: _____________________________

## Security Configuration
-----------------------------------------------------------
Access Control:
  [ ] Basic (Username/Password)
  [ ] SSH Keys
  [ ] IAM Integration
  [ ] Custom: ___________________________________

Firewall Rules:
  Allowed IPs: __________________________________
  Custom Rules: ________________________________

Certificate Management:
  [ ] Auto-generated
  [ ] Custom Certificates
  [ ] Let's Encrypt Integration

## SPLAT Node Configuration
-----------------------------------------------------------
Number of Nodes: _________________________________

Node Types:
  [ ] Standard Soil Probes
  [ ] Weather Stations
  [ ] Custom Sensors: _____________________________

Data Collection Interval:
  [ ] 5 minutes
  [ ] 15 minutes
  [ ] 30 minutes
  [ ] Custom: ___________________________________

## Additional Services
-----------------------------------------------------------
[ ] Automatic Updates
[ ] Remote Support Access
[ ] Custom Analytics
[ ] Data Export API
[ ] Integration Services

## Notes and Special Requirements
-----------------------------------------------------------
_________________________________________________
_________________________________________________
_________________________________________________
_________________________________________________

## Approval
-----------------------------------------------------------
Requested By: ____________________________________
Date: _________________________________________
Department Approval: _____________________________
IT Security Approval: ____________________________

## For Internal Use Only
-----------------------------------------------------------
Deployment ID: __________________________________
Key Storage Location: ____________________________
Documentation Location: __________________________
Backup Verification Date: ________________________
Last Security Audit: _____________________________
