# Agentic Trader Platform - Deployment Guide

## Overview

The Agentic Trader Platform supports multiple deployment options, from local development to production Kubernetes clusters on AWS EKS.

## Deployment Options

| Option | Use Case | Complexity | Scalability |
|--------|----------|------------|-------------|
| Docker Compose | Local dev, testing | Low | Single node |
| Kubernetes | Production bare-metal | Medium | High |
| Helm | Production with dependencies | Medium | High |
| Terraform + EKS | Cloud-native production | High | Very High |

---

## 1. Docker Compose Deployment

### Prerequisites
- Docker 24.0+
- Docker Compose 2.0+
- 8GB RAM minimum

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/agentic-trader-platform.git
cd agentic-trader-platform

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose -f docker-compose.full.yml up -d

# Verify deployment
make health-check
```

### Services Included

| Service | Port | Description |
|---------|------|-------------|
| API Server | 8000 | FastAPI trading backend |
| Frontend | 3000 | React dashboard |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & event bus |
| ClickHouse | 8123 | Analytics database |
| Grafana | 3001 | Monitoring dashboards |
| Prometheus | 9090 | Metrics collection |
| ChromaDB | 8001 | Vector database |

---

## 2. Kubernetes Deployment

### Prerequisites
- kubectl 1.28+
- Running Kubernetes cluster (1.28+)
- Helm 3.12+ (optional, for dependencies)

### Option A: Plain Kubernetes Manifests

```bash
# Create namespace
kubectl create namespace agentic-trader

# Deploy infrastructure
kubectl apply -f infrastructure/k8s/00-namespace.yaml
kubectl apply -f infrastructure/k8s/01-secrets.yaml
kubectl apply -f infrastructure/k8s/02-configmap.yaml

# Deploy services
kubectl apply -f infrastructure/k8s/03-postgres.yaml
kubectl apply -f infrastructure/k8s/04-redis.yaml
kubectl apply -f infrastructure/k8s/05-api.yaml
kubectl apply -f infrastructure/k8s/06-ingress.yaml

# Verify
kubectl get pods -n agentic-trader
kubectl get svc -n agentic-trader
```

### Option B: Using Kustomize

```bash
kubectl apply -k infrastructure/k8s/overlays/production
```

---

## 3. Helm Deployment

### Prerequisites
- Helm 3.12+
- Kubernetes cluster with ingress controller

### Install Chart

```bash
# Add Bitnami repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Create namespace
kubectl create namespace agentic-trader

# Install with dependencies
helm install agentic-trader infrastructure/helm/agentic-trader \
  --namespace agentic-trader \
  --values infrastructure/helm/agentic-trader/values.yaml

# Verify
helm list -n agentic-trader
kubectl get pods -n agentic-trader
```

### Upgrade

```bash
helm upgrade agentic-trader infrastructure/helm/agentic-trader \
  --namespace agentic-trader \
  --set image.tag=v1.1.0
```

### Uninstall

```bash
helm uninstall agentic-trader -n agentic-trader
```

---

## 4. Terraform + AWS EKS Deployment

### Prerequisites
- Terraform 1.5+
- AWS CLI configured
- kubectl
- Helm

### Setup

```bash
# Navigate to Terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="db_password=YourSecurePassword123"

# Apply deployment
terraform apply -var="db_password=YourSecurePassword123"

# Configure kubectl
aws eks update-kubeconfig --name agentic-trader-cluster --region eu-west-1

# Verify cluster
kubectl get nodes
```

### Resources Created

| Resource | Type | Purpose |
|----------|------|---------|
| VPC | AWS VPC | Network isolation |
| EKS | Kubernetes 1.28 | Container orchestration |
| RDS | PostgreSQL 15.3 | Primary database |
| ElastiCache | Redis 7 | Cache & session store |
| ALB | Application Load Balancer | Traffic distribution |
| Security Groups | AWS SG | Network access control |

### Outputs

```bash
# View Terraform outputs
terraform output

# Key outputs:
# - cluster_endpoint: EKS API endpoint
# - cluster_name: EKS cluster name
# - rds_endpoint: Database endpoint
# - redis_endpoint: Redis endpoint
# - load_balancer_dns: Application URL
```

---

## 5. GitOps with ArgoCD

### Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### Deploy Application

```bash
kubectl apply -f infrastructure/gitops/argocd/application.yaml
```

The application will auto-sync when changes are pushed to the repository.

---

## 6. GitOps with Flux

### Install Flux

```bash
flux install

# Bootstrap with GitHub
flux bootstrap github \
  --owner=your-org \
  --repository=agentic-trader-platform \
  --branch=main \
  --path=./infrastructure/gitops/flux \
  --personal
```

### Deploy Application

```bash
kubectl apply -f infrastructure/gitops/flux/kustomization.yaml
```

---

## Security Hardening

### Network Policies

```bash
# Apply network policies
kubectl apply -f infrastructure/security/network-policies.yaml
```

### OPA Gatekeeper

```bash
# Install Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/master/deploy/gatekeeper.yaml

# Apply policies
kubectl apply -f infrastructure/security/opa-policies.yaml
```

### Falco Runtime Security

```bash
# Install Falco
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco

# Apply custom rules
kubectl apply -f infrastructure/security/falco-rules.yaml
```

---

## Monitoring & Alerting

### Prometheus

```bash
# Access Prometheus
kubectl port-forward svc/prometheus-server 9090:9090 -n agentic-trader
```

### Grafana

```bash
# Access Grafana
kubectl port-forward svc/grafana 3000:3000 -n agentic-trader
# Default credentials: admin/admin
```

### AlertManager

```bash
# Access AlertManager
kubectl port-forward svc/alertmanager 9093:9093 -n agentic-trader
```

---

## Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n agentic-trader

# Check logs
kubectl logs <pod-name> -n agentic-trader

# Previous container logs
kubectl logs <pod-name> -n agentic-trader --previous
```

#### Database Connection Issues

```bash
# Test database connectivity
kubectl run debug --rm -it --image=postgres:15 -- psql postgresql://trader:<password>@postgres:5432/trading

# Check secret
kubectl get secret postgres-credentials -n agentic-trader -o yaml
```

#### Ingress Issues

```bash
# Check ingress status
kubectl get ingress -n agentic-trader

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

### Health Checks

```bash
# API health check
curl http://localhost:8000/health

# MCP health check
curl http://localhost:8000/mcp/health

# Kubernetes health
kubectl get componentstatuses
```

---

## Scaling

### Horizontal Pod Autoscaling

```bash
# Check HPA status
kubectl get hpa -n agentic-trader

# Manually scale
kubectl scale deployment api-server --replicas=5 -n agentic-trader
```

### EKS Node Scaling

```bash
# Update node group
eksctl scale nodegroup \
  --cluster=agentic-trader-cluster \
  --name=general \
  --nodes=5 \
  --nodes-min=2 \
  --nodes-max=10
```

---

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL backup
kubectl exec -it postgres-0 -n agentic-trader -- pg_dump -U trader trading > backup.sql

# Restore
kubectl exec -i postgres-0 -n agentic-trader -- psql -U trader trading < backup.sql
```

### Persistent Volume Backup

```bash
# List PVCs
kubectl get pvc -n agentic-trader

# Create snapshot (if using CSI driver)
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot
  namespace: agentic-trader
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: postgres-pvc
EOF
```

---

## Cost Optimization

### AWS Cost Estimates (Monthly)

| Resource | Instance | Cost |
|----------|----------|------|
| EKS Control Plane | - | $72 |
| EKS Nodes (2x) | t3.medium | $60 |
| RDS PostgreSQL | db.t3.micro | $15 |
| ElastiCache Redis | cache.t3.micro | $15 |
| ALB | - | $20 |
| **Total** | | **~$182/month** |

### Spot Instances

```bash
# Use spot instances for non-critical workloads
module "eks" {
  eks_managed_node_groups = {
    spot = {
      capacity_type = "SPOT"
      instance_types = ["t3.medium", "t3a.medium"]
    }
  }
}
```

---

## Support

- **Issues**: https://github.com/your-org/agentic-trader-platform/issues
- **Documentation**: https://docs.agentictrader.com
- **Slack**: #agentic-trader-support

---

*Last Updated: February 26, 2026*
*Version: 1.0.0*
