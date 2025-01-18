# Kubernetes Deployment Guide

## Overview

This document details the Kubernetes deployment configuration for the Crypto Anomaly Detection Engine (CADE). The system is deployed using a microservices architecture across multiple pods with automated scaling and monitoring.

## Cluster Requirements

### Minimum Specifications
```yaml
Kubernetes Version: 1.24+
Nodes:
  Standard Nodes:
    Count: 3
    CPU: 8 cores
    RAM: 32GB
    Storage: 100GB SSD
  Analytics Nodes:
    Count: 2
    CPU: 16 cores
    RAM: 64GB
    Storage: 200GB SSD
```

## Namespace Configuration

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cade
  labels:
    name: cade
    environment: production
    monitoring: enabled
```

## Core Services

### API Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: cade-api
  namespace: cade
spec:
  selector:
    app: cade-api
  ports:
    - name: http
      port: 80
      targetPort: 8000
    - name: websocket
      port: 8080
      targetPort: 8080
  type: LoadBalancer
```

### API Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cade-api
  namespace: cade
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cade-api
  template:
    metadata:
      labels:
        app: cade-api
    spec:
      containers:
        - name: cade-api
          image: cade/api:latest
          ports:
            - containerPort: 8000
            - containerPort: 8080
          resources:
            requests:
              cpu: "1"
              memory: "2Gi"
            limits:
              cpu: "2"
              memory: "4Gi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 5
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: cade-secrets
                  key: database-url
```

## Database Deployments

### TimescaleDB StatefulSet
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: timescaledb
  namespace: cade
spec:
  serviceName: timescaledb
  replicas: 2
  selector:
    matchLabels:
      app: timescaledb
  template:
    metadata:
      labels:
        app: timescaledb
    spec:
      containers:
        - name: timescaledb
          image: timescale/timescaledb:latest-pg14
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: timescaledb-data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "2"
              memory: "8Gi"
            limits:
              cpu: "4"
              memory: "16Gi"
  volumeClaimTemplates:
    - metadata:
        name: timescaledb-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
```

### Redis Cluster
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: cade
spec:
  serviceName: redis
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:6.2-alpine
          ports:
            - containerPort: 6379
          resources:
            requests:
              cpu: "0.5"
              memory: "1Gi"
            limits:
              cpu: "1"
              memory: "2Gi"
```

## Analysis Workers

### Chain Analysis Worker
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chain-analysis
  namespace: cade
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chain-analysis
  template:
    metadata:
      labels:
        app: chain-analysis
    spec:
      containers:
        - name: chain-analysis
          image: cade/chain-analysis:latest
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
```

## Monitoring & Logging

### Prometheus Configuration
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cade-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: cade-api
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

### Logging Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: cade
data:
  fluent.conf: |
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch-logging
      port 9200
      logstash_format true
      logstash_prefix k8s
      <buffer>
        flush_interval 5s
      </buffer>
    </match>
```

## Autoscaling

### HorizontalPodAutoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cade-api-hpa
  namespace: cade
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cade-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

## Network Policies

### API Network Policy
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: cade
spec:
  podSelector:
    matchLabels:
      app: cade-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: nginx-ingress
      ports:
        - protocol: TCP
          port: 8000
        - protocol: TCP
          port: 8080
```

## Resource Quotas

### Namespace Quota
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: cade-quota
  namespace: cade
spec:
  hard:
    requests.cpu: "32"
    requests.memory: 64Gi
    limits.cpu: "64"
    limits.memory: 128Gi
    pods: "50"
```

## Backup Configuration

### Database Backup CronJob
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
  namespace: cade
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: db-backup
              image: cade/db-backup:latest
              env:
                - name: BACKUP_DIR
                  value: /backups
              volumeMounts:
                - name: backup-volume
                  mountPath: /backups
          volumes:
            - name: backup-volume
              persistentVolumeClaim:
                claimName: backup-pvc
```

## Deployment Strategy

### Rolling Updates
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

## Configuration Management

### ConfigMap Example
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cade-config
  namespace: cade
data:
  ENVIRONMENT: production
  LOG_LEVEL: info
  MAX_CONNECTIONS: "1000"
  CACHE_TTL: "300"
```

### Secrets Management
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cade-secrets
  namespace: cade
type: Opaque
data:
  database-url: <base64-encoded-url>
  api-key: <base64-encoded-key>
  jwt-secret: <base64-encoded-secret>
```

## Maintenance Procedures

### Database Migration Job
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: cade
spec:
  template:
    spec:
      containers:
        - name: db-migration
          image: cade/migrations:latest
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: cade-secrets
                  key: database-url
      restartPolicy: Never
```
