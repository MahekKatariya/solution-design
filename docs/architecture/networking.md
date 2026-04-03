# Networking Architecture

## VPC Design

- CIDR: 10.0.0.0/20
- 3 Availability Zones

## Subnets

### Public Subnets
- ALB
- NAT Gateway

### Private Subnets
- EKS nodes
- Internal services

### DB Subnets
- RDS
- Redis

---

## Traffic Flow

Internet → CloudFront → ALB → EKS

Internal:
- Service-to-service via ClusterIP
- External APIs via NAT Gateway

---

## Security

- Security Groups (least privilege)
- NACLs for subnet-level control
- Private-only DB access