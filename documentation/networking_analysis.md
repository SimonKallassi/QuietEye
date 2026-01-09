# QuietEye Network Protocol Analysis

**Date**: January 9, 2026  
**Branch**: `34-research-http-websockets-mqtt`  
**Purpose**: Evaluate HTTP, WebSockets, and MQTT for edge-to-cloud communication

---

## Executive Summary

This document analyzes three network protocols (HTTP, WebSockets, MQTT) for the QuietEye computer vision alert system. We recommend a **hybrid approach** using HTTP for the MVP, with a path to production using HTTP + MQTT for optimal performance and cost efficiency.

**Key Decision**: Start with HTTP-only MVP, evolve to HTTP + MQTT for production.

---

## Project Context

### System Overview
QuietEye is an edge-based computer vision system that:
- Processes multiple camera feeds on edge devices
- Detects various events (zone intrusion, fire, attendance, smoker detection, loitering, queue management)
- Sends alerts with snapshots to cloud backend
- Receives commands and configuration updates from cloud
- Provides optional live feed streaming to dashboard

### Communication Requirements

| Direction | Type | Frequency | Payload Size | Real-time? |
|-----------|------|-----------|--------------|------------|
| Edge → Cloud | Alert + Snapshot | On detection (~10-50/day) | 50-200 KB | Low latency preferred |
| Cloud → Edge | Commands/Config | Occasional | 1-5 KB | Medium latency OK |
| Cloud → Edge | Health checks | Every 30-60s | 100 bytes | Low priority |
| Edge → Dashboard | Live feed | On-demand | 500 KB/s | Real-time required |

---

## Protocol Analysis

### 1. HTTP (Request-Response)

**What it is**: The standard web protocol. Client sends a request, server responds. Think of it like mailing a letter and waiting for a reply.

#### Pros
- ✅ Simple to implement (libraries in every language)
- ✅ Works everywhere (no firewall issues)
- ✅ Perfect for occasional events (alerts)
- ✅ Cost-effective (pay only when data flows)
- ✅ Easy debugging with standard tools
- ✅ RESTful API patterns are well-understood

#### Cons
- ❌ One-way communication (client initiates only)
- ❌ Cloud cannot push to edge without polling
- ❌ Inefficient for continuous streams
- ❌ Higher latency for bidirectional needs

#### Best Use Cases
- Sending alerts from edge to cloud
- Uploading snapshots
- Any one-off data transfer

---

### 2. WebSockets (Persistent Bidirectional Connection)

**What it is**: A persistent connection between client and server where both can send messages anytime. Like an open phone line.

#### Pros
- ✅ True bidirectional communication
- ✅ Low latency (connection stays open)
- ✅ Great for live streaming
- ✅ Single connection for multiple message types
- ✅ Lower overhead than HTTP for frequent messages

#### Cons
- ❌ More complex to implement
- ❌ Connection management (reconnection logic)
- ❌ Cloud costs (paying for idle connections)
- ❌ Firewall/proxy issues in some networks
- ❌ Overkill for occasional alerts

#### Best Use Cases
- Live video feed streaming
- Real-time dashboard updates
- When you need instant bidirectional communication

---

### 3. MQTT (Publish-Subscribe Messaging)

**What it is**: A lightweight messaging protocol designed for IoT. Devices subscribe to "topics" and get messages when published. Like a radio broadcast system.

#### Pros
- ✅ Designed for IoT/embedded devices (very lightweight)
- ✅ Excellent for unreliable networks (built-in QoS)
- ✅ Efficient bandwidth usage
- ✅ Perfect for device fleets
- ✅ Built-in message delivery guarantees
- ✅ Cloud can push to edge easily
- ✅ Supports offline queuing

#### Cons
- ❌ Requires MQTT broker infrastructure
- ❌ Learning curve for pub/sub pattern
- ❌ Not ideal for large payloads (images)
- ❌ Additional service to maintain

#### Best Use Cases
- Commands from cloud to edge
- Health monitoring
- Configuration updates
- Device control

---

## Architecture Comparison

### Pattern 1: HTTP Only
```
Edge Device:
  └─ HTTP POST /api/alerts → Cloud (on detection)
  └─ HTTP GET /api/commands → Cloud (poll every 30s)

Cloud:
  └─ REST API receives alerts
  └─ REST API serves commands when polled
```

**Pros**: Simplest, cheapest, fastest to build  
**Cons**: Polling delay (30s), cloud can't instantly notify edge

---

### Pattern 2: HTTP + WebSocket
```
Edge Device:
  └─ HTTP POST /api/alerts → Cloud (on detection)
  └─ WebSocket connection ← Cloud (for commands)

Cloud:
  └─ REST API receives alerts
  └─ WebSocket server pushes commands
```

**Pros**: Instant commands, single connection  
**Cons**: Connection management, higher cloud costs for idle connections

---

### Pattern 3: HTTP + MQTT (Recommended for Production)
```
Edge Device:
  └─ HTTP POST /api/alerts → Cloud (on detection)
  └─ MQTT Subscribe: quieteye/devices/{device_id}/commands

Cloud:
  └─ REST API receives alerts
  └─ MQTT Publish to device topics
```

**Pros**: Best balance of simplicity and features, designed for IoT  
**Cons**: Requires MQTT broker (AWS IoT Core, HiveMQ)

---

## MVP Architecture Plan

### Goal
Build simplest functional system to validate concept with real customers.

### Tech Stack
- **Edge Device**: Jetson Orin Nano (8GB) - handles 4-6 cameras
- **Protocol**: HTTP only
- **Cloud**: AWS (API Gateway + Lambda + DynamoDB + S3)
- **Detection Types**: Zone intrusion, fire detection, face capture (3 models)

### MVP Communication Flow

```
┌─────────────────┐
│  Edge Device    │
│  (Jetson Orin)  │
│                 │
│  • CV Pipeline  │
│  • 4-6 Cameras  │
└────────┬────────┘
         │
         │ HTTP POST /api/alerts
         │ {
         │   device_id, camera_id, zone,
         │   alert_type, snapshot (base64),
         │   metadata, timestamp
         │ }
         │
         ▼
┌─────────────────────────┐
│   AWS API Gateway       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Lambda Function       │
│   • Parse alert         │
│   • Save to DynamoDB    │
│   • Upload to S3        │
│   • Trigger SNS         │
└─────────────────────────┘
         │
         ├──► DynamoDB (alert records)
         ├──► S3 (snapshots)
         └──► SNS (notifications)

┌─────────────────┐
│  Edge Device    │
│                 │
│  Poll every 30s │
└────────┬────────┘
         │
         │ HTTP GET /api/devices/{id}/commands
         │
         ▼
┌─────────────────────────┐
│   API Gateway           │
│   Returns pending       │
│   commands if any       │
└─────────────────────────┘
```

### MVP Implementation Details

#### Edge Device (Python)

```python
# alert_sender.py
import requests
import base64
import cv2
from datetime import datetime

API_BASE_URL = "https://your-api-gateway.execute-api.us-east-1.amazonaws.com/prod"
DEVICE_ID = "device_001"

def send_alert(snapshot_image, metadata):
    """Send detection alert to cloud"""
    
    # Encode snapshot as JPEG base64
    _, buffer = cv2.imencode('.jpg', snapshot_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    
    payload = {
        "device_id": DEVICE_ID,
        "camera_id": metadata["camera_id"],
        "zone": metadata["zone"],
        "alert_type": metadata["alert_type"],
        "coordinates": metadata["coordinates"],
        "snapshot": jpg_as_text,
        "timestamp": datetime.utcnow().isoformat(),
        "confidence": metadata.get("confidence", 0.0)
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/alerts",
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"✓ Alert sent: {metadata['alert_type']}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            # TODO: Store locally for retry
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {e}")
        # TODO: Queue for retry
        return False


def poll_commands():
    """Poll for pending commands from cloud"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/devices/{DEVICE_ID}/commands",
            timeout=5
        )
        
        if response.status_code == 200:
            commands = response.json().get("commands", [])
            for cmd in commands:
                execute_command(cmd)
                acknowledge_command(cmd["id"])
        
    except requests.exceptions.RequestException as e:
        print(f"Command poll failed: {e}")


def execute_command(command):
    """Execute command from cloud"""
    action = command.get("action")
    params = command.get("params", {})
    
    if action == "restart":
        # Restart service
        os.system("sudo systemctl restart quieteye")
    elif action == "update_config":
        # Update configuration
        update_config(params)
    elif action == "healthcheck":
        # Send health status
        send_health_status()
    else:
        print(f"Unknown command: {action}")


# Main loop (simplified)
import threading
import time

def command_poller():
    """Background thread for polling commands"""
    while True:
        poll_commands()
        time.sleep(30)  # Poll every 30 seconds

# Start command polling in background
threading.Thread(target=command_poller, daemon=True).start()
```

#### AWS Lambda Function (Python)

```python
# alert_handler.py
import json
import boto3
import base64
from datetime import datetime
import uuid

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

ALERTS_TABLE = dynamodb.Table('quieteye-alerts')
SNAPSHOTS_BUCKET = 'quieteye-snapshots'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:xxx:quieteye-notifications'

def lambda_handler(event, context):
    """Process incoming alert from edge device"""
    
    try:
        # Parse request body
        body = json.loads(event['body'])
        
        device_id = body['device_id']
        camera_id = body['camera_id']
        alert_type = body['alert_type']
        snapshot_b64 = body['snapshot']
        timestamp = body['timestamp']
        
        # Generate unique alert ID
        alert_id = str(uuid.uuid4())
        
        # Save snapshot to S3
        snapshot_key = f"{device_id}/{camera_id}/{alert_id}.jpg"
        s3.put_object(
            Bucket=SNAPSHOTS_BUCKET,
            Key=snapshot_key,
            Body=base64.b64decode(snapshot_b64),
            ContentType='image/jpeg',
            Metadata={
                'device_id': device_id,
                'camera_id': camera_id,
                'alert_type': alert_type
            }
        )
        
        # Save alert record to DynamoDB
        ALERTS_TABLE.put_item(
            Item={
                'alert_id': alert_id,
                'device_id': device_id,
                'camera_id': camera_id,
                'alert_type': alert_type,
                'zone': body.get('zone', ''),
                'coordinates': body.get('coordinates', {}),
                'timestamp': timestamp,
                'confidence': body.get('confidence', 0.0),
                'snapshot_url': f"s3://{SNAPSHOTS_BUCKET}/{snapshot_key}",
                'status': 'new',
                'created_at': datetime.utcnow().isoformat()
            }
        )
        
        # Send notification
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"QuietEye Alert: {alert_type}",
            Message=f"Device {device_id} detected {alert_type} at {timestamp}"
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'alert_id': alert_id,
                'status': 'received'
            })
        }
        
    except Exception as e:
        print(f"Error processing alert: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### MVP Features
- ✅ Zone intrusion detection
- ✅ Fire detection
- ✅ Face capture for attendance
- ✅ Alert storage (DynamoDB)
- ✅ Snapshot storage (S3, 30-day lifecycle)
- ✅ Email/SMS notifications
- ✅ Simple web dashboard (view alerts, update status)
- ✅ Device command polling (30-second interval)

### MVP Limitations
- ⏱️ 30-second delay for commands (polling interval)
- ❌ No live feed streaming
- ❌ No advanced analytics (heatmaps, queue metrics)
- ❌ No smoker/loitering detection

### MVP Timeline
- **Week 1-2**: Edge device setup + CV models
- **Week 3**: AWS backend (API Gateway + Lambda + DynamoDB + S3)
- **Week 4**: Dashboard (React app showing alerts)
- **Week 5**: Testing + polish

### MVP Cost Estimate (per month)
- API Gateway: $1-3
- Lambda: $2-5
- DynamoDB: $1-2
- S3: $1-2
- SNS/SES: $1-3
- EC2/AppRunner (dashboard): $10-20
- **Total**: $20-35/month (flat, not per device)

---

## Production Architecture Plan

### Overview
Move from HTTP-only to a hybrid HTTP + MQTT approach for better scalability and instant command delivery.

**Key Changes**:
- Edge devices subscribe to MQTT topics for commands instead of polling
- Cloud uses MQTT broker to instantly push commands to devices
- Continue using HTTP for alert uploads (optimal for occasional high-payload events)
- Add WebSocket relay for optional live feed streaming

### Communication Flow

```
┌─────────────────┐
│  Edge Device    │
└────┬────┬───────┘
     │    │ MQTT Subscribe
     │    │ (commands, config)
     │    │
     │    ▼
     │  ┌──────────────────┐
     │  │  MQTT Broker     │
     │  │  (AWS IoT Core)  │
     │  └──────────────────┘
     │         ▲
     │         │ Publish commands
     │         │ from cloud
     │
     │ HTTP POST /api/alerts
     │ (snapshots + metadata)
     │
     ▼
┌─────────────────────────┐
│   Cloud Backend         │
│   (API Gateway + Λ)     │
└─────────────────────────┘
     │
     ├──► DynamoDB (alert storage)
     ├──► S3 (snapshots)
     ├──► SNS (notifications)
     └──► MQTT (push commands)

┌─────────────────┐
│  Dashboard      │
└────────┬────────┘
         │ WebSocket (live feed, optional)
         │
         ▼
┌─────────────────┐
│  Edge Device    │
│  Stream frames  │
└─────────────────┘
```

### Production Features
- ✅ All 7 detection types
- ✅ Instant command delivery (MQTT, <1s)
- ✅ Device health monitoring
- ✅ Live feed streaming (WebSocket, optional)
- ✅ Presence heatmaps
- ✅ Queue management analytics
- ✅ Scalable to 100+ devices
- ✅ Device fleet management
- ✅ OTA (Over-The-Air) updates

### Production Cost Estimate (100 devices, per month)
- API Gateway: $3-10
- Lambda: $5-15
- DynamoDB: $5-10
- S3: $5-10
- MQTT Broker (AWS IoT Core): $20-50
- SNS/SES (Notifications): $5-10
- Compute (Dashboard + relay): $50-100
- **Total**: **$95-205/month** (scales sub-linearly with more devices)

---

## Performance Benchmarks (Target)

### Edge Device
- **FPS per camera**: 15-30 fps
- **Detection latency**: <100ms per frame
- **Alert generation**: <500ms from detection to HTTP POST
- **CPU usage**: <70% average
- **GPU usage**: <80% average
- **Power consumption**: <25W (Jetson Orin Nano)

### Network
- **Alert delivery**: <2 seconds edge to cloud
- **Command delivery (MQTT)**: <1 second cloud to edge
- **Live feed latency**: <500ms (WebSocket)
- **Bandwidth per device**: ~1-5 MB/day (alerts only), ~500 KB/s (live feed)

### Cloud
- **API latency**: <200ms (P95)
- **Lambda cold start**: <1 second
- **Dashboard load time**: <2 seconds
- **Notification delivery**: <5 seconds (email), <30 seconds (SMS)

---

## Security Considerations

### MVP
- HTTPS for all API calls
- API keys for device authentication
- Basic input validation

### Production
- TLS 1.2+ for all connections
- X.509 certificates for MQTT (AWS IoT Core)
- Device provisioning workflow
- JWT tokens for dashboard authentication
- Encrypted snapshot storage (S3 server-side encryption)
- IAM roles with least privilege
- Network isolation (VPC)
- Regular security audits

---

## Monitoring & Observability

### MVP
- CloudWatch logs for Lambda
- Basic error tracking

### Production
- CloudWatch metrics (API Gateway, Lambda, IoT Core)
- Custom metrics (FPS, detection rate, alert volume)
- Device health dashboard
- Alert on device offline (>5 minutes)
- Alert on high error rate (>5%)
- Distributed tracing (X-Ray)
- Log aggregation (CloudWatch Insights)

---

## Recommendations Summary

### Start Here (MVP)
1. **Implement**: HTTP-only architecture
2. **Deploy**: AWS API Gateway + Lambda + DynamoDB + S3
3. **Test**: Alert delivery, command polling
4. **Validate**: Performance and latency with real workload
5. **Timeline**: 4-5 weeks to working MVP

### Evolve To (Production)
1. **Add**: MQTT broker (AWS IoT Core) for instant commands
2. **Enhance**: Live feed capability, advanced analytics
3. **Scale**: Multiple edge devices per location
4. **Timeline**: 3-4 months post-MVP to production-ready

### Don't Overbuild
- Start simple, measure, iterate
- Validate MVP concept with real customers before scaling
- Don't implement all 7 detection types at once
- Focus on core value proposition first (zone intrusion + fire + attendance)

---

## Next Steps

1. **Set up AWS account**: Free tier for 12 months
2. **Implement MVP edge code**: Alert sender using HTTP
3. **Deploy MVP backend**: API Gateway + Lambda + DynamoDB + S3
4. **Test end-to-end**: Validate alert delivery pipeline
5. **Build dashboard**: Simple UI showing alerts and status updates
6. **Gather feedback**: Test with real customer before production investment

---

## References

- [MQTT Protocol Specification](https://mqtt.org/mqtt-specification/)
- [AWS IoT Core Documentation](https://docs.aws.amazon.com/iot/latest/developerguide/)
- [WebSocket RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)
- [Jetson Orin Modules](https://developer.nvidia.com/embedded/jetson-orin)
- [HTTP/1.1 RFC 2616](https://datatracker.ietf.org/doc/html/rfc2616)

---

**Document Version**: 1.0  
**Last Updated**: January 9, 2026  
**Status**: Approved for MVP Implementation
