# AWS MSK Management Scripts

This repository contains Python scripts for managing and monitoring Amazon MSK (Managed Streaming for Apache Kafka) clusters.

## Scripts

### 1. `list_msk_clusters.py`
Lists all MSK clusters in your AWS account with detailed information including:
- Cluster name and ARN
- Cluster state and Kafka version
- Number of broker nodes
- Active brokers count
- Tags (if available)
- Saves detailed output to JSON file

### 2. `list_msk_topics_partitions.py`
Lists topics and partitions for each MSK broker, including:
- Total number of topics and partitions
- Broker information (host, port, rack)
- Topic details (partitions, replication factor)
- Partition distribution across brokers
- Detailed topic configurations (optional)
- **Requires direct Kafka connectivity**

### 3. `list_msk_cloudwatch_metrics.py` ⭐ **NEW - CloudWatch Based**
Lists topics and partitions using CloudWatch metrics (no direct Kafka connectivity required):
- Topic count and partition count from CloudWatch metrics
- Bytes in/out per second
- Messages in per second
- Offline partitions count
- Under-replicated partitions
- Broker-specific metrics (optional)
- Historical metrics data
- **No direct Kafka connectivity required**

## Prerequisites

1. **AWS CLI Configuration**: Make sure you have AWS CLI configured with appropriate credentials
   ```bash
   aws configure
   ```

2. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

3. **AWS Permissions**: Ensure your AWS credentials have the following permissions:
   - `kafka:ListClusters`
   - `kafka:DescribeCluster`
   - `kafka:ListNodes`
   - `kafka:ListTagsForResource`
   - `kafka:GetBootstrapBrokers`
   - `cloudwatch:GetMetricStatistics` (for CloudWatch script)

## Usage

### List MSK Clusters
```bash
python list_msk_clusters.py
```

This will:
- List all MSK clusters in your AWS account
- Display basic information for each cluster
- Save detailed information to a timestamped JSON file

### List Topics and Partitions (Direct Kafka Connection)
```bash
# List topics and partitions for all clusters
python list_msk_topics_partitions.py

# List topics and partitions for a specific cluster
python list_msk_topics_partitions.py --cluster-arn "arn:aws:kafka:region:account:cluster/cluster-name/..."

# Save detailed output to JSON file
python list_msk_topics_partitions.py --save-json

# Show detailed topic configurations
python list_msk_topics_partitions.py --detailed

# Combine options
python list_msk_topics_partitions.py --cluster-arn "arn:aws:kafka:region:account:cluster/cluster-name/..." --save-json --detailed
```

### List Topics and Partitions (CloudWatch Metrics) ⭐ **Recommended**
```bash
# Get metrics for all clusters (last 24 hours)
python list_msk_cloudwatch_metrics.py

# Get metrics for a specific cluster
python list_msk_cloudwatch_metrics.py --cluster-arn "arn:aws:kafka:region:account:cluster/cluster-name/..."

# Get metrics for last 7 days
python list_msk_cloudwatch_metrics.py --hours 168

# Include broker-specific metrics
python list_msk_cloudwatch_metrics.py --broker-metrics

# Save detailed output to JSON file
python list_msk_cloudwatch_metrics.py --save-json

# Combine options
python list_msk_cloudwatch_metrics.py --cluster-arn "arn:aws:kafka:region:account:cluster/cluster-name/..." --hours 48 --broker-metrics --save-json
```

## Command Line Options

### For `list_msk_topics_partitions.py`
- `--cluster-arn`: Specify a particular cluster ARN to analyze
- `--save-json`: Save detailed output to a JSON file
- `--detailed`: Show detailed topic configurations

### For `list_msk_cloudwatch_metrics.py`
- `--cluster-arn`: Specify a particular cluster ARN to analyze
- `--hours`: Number of hours to look back for metrics (default: 24)
- `--save-json`: Save detailed output to a JSON file
- `--broker-metrics`: Include broker-specific metrics

## Output Examples

### Cluster List Output
```
AWS MSK Cluster Lister
==================================================
Found 2 MSK cluster(s):

Cluster Name: my-production-cluster
Cluster ARN: arn:aws:kafka:us-east-1:123456789012:cluster/my-production-cluster/...
State: ACTIVE
Kafka Version: 2.8.1
Number of Broker Nodes: 3
Active Brokers: 3
Tags:
  Environment: production
  Project: data-pipeline
--------------------------------------------------
```

### CloudWatch Metrics Output
```
AWS MSK CloudWatch Metrics Lister
============================================================
Time range: 2024-01-15T10:00:00 to 2024-01-16T10:00:00

Analyzing cluster: my-production-cluster
ARN: arn:aws:kafka:us-east-1:123456789012:cluster/my-production-cluster/...

================================================================================
CLUSTER: my-production-cluster
================================================================================
ARN: arn:aws:kafka:us-east-1:123456789012:cluster/my-production-cluster/...

========================================
SUMMARY METRICS
========================================
Topics: 5.0
Partitions: 15.0
Global Topics: 5.0
Global Partitions: 15.0

========================================
DETAILED METRICS
========================================

Bytes In Per Second (BytesInPerSec):
  Unit: Bytes/Second
  Latest Average: 1024.5
  Latest Maximum: 2048.0
  Latest Minimum: 512.0
  Timestamp: 2024-01-16T10:00:00

Messages In Per Second (MessagesInPerSec):
  Unit: Count/Second
  Latest Average: 100.2
  Latest Maximum: 150.0
  Latest Minimum: 50.0
  Timestamp: 2024-01-16T10:00:00

Number of Topics (TopicCount):
  Unit: Count
  Latest Average: 5.0
  Latest Maximum: 5.0
  Latest Minimum: 5.0
  Timestamp: 2024-01-16T10:00:00

Number of Partitions (PartitionCount):
  Unit: Count
  Latest Average: 15.0
  Latest Maximum: 15.0
  Latest Minimum: 15.0
  Timestamp: 2024-01-16T10:00:00
```

## Advantages of CloudWatch Approach

### ✅ **Benefits of `list_msk_cloudwatch_metrics.py`**
- **No direct Kafka connectivity required** - works from anywhere with AWS access
- **No security protocol configuration** - uses AWS API calls only
- **Historical data** - can analyze metrics over time periods
- **Broker-specific metrics** - detailed per-broker information
- **Performance metrics** - bytes in/out, messages per second
- **Health metrics** - offline partitions, under-replicated partitions
- **Works with all cluster types** - regardless of security configuration

### ⚠️ **Limitations of CloudWatch Approach**
- **Metric granularity** - 5-minute periods (not real-time)
- **Limited topic details** - shows counts but not individual topic names
- **No partition distribution** - can't see which broker leads which partition
- **Requires CloudWatch metrics** - clusters must have metrics enabled

### 🔧 **When to Use Each Script**

**Use `list_msk_cloudwatch_metrics.py` when:**
- You need quick overview without Kafka connectivity
- You want historical performance data
- You're monitoring from outside the VPC
- You need broker-specific performance metrics
- You want to avoid security protocol configuration

**Use `list_msk_topics_partitions.py` when:**
- You need detailed topic names and configurations
- You want real-time partition distribution
- You need to see which broker leads which partition
- You're working from within the VPC with direct access

## Security Considerations

- The CloudWatch script uses only AWS API calls - no direct Kafka connectivity
- The direct Kafka script uses `PLAINTEXT` security protocol by default. For production clusters, you may need to modify the security protocol based on your cluster configuration (TLS, SASL, IAM)
- Ensure your AWS credentials have minimal required permissions
- Consider using AWS IAM roles when running on EC2 instances

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   ```
   Error: AWS credentials not found. Please configure your AWS credentials.
   ```
   Solution: Run `aws configure` to set up your credentials

2. **Permission Denied**
   ```
   AWS Error: An error occurred (AccessDeniedException) when calling the ListClusters operation
   ```
   Solution: Ensure your AWS user/role has the required MSK permissions

3. **No CloudWatch Metrics Found**
   ```
   No datapoints found for metric TopicCount in cluster my-cluster
   ```
   Solution: Ensure CloudWatch metrics are enabled for your MSK cluster

4. **Connection Timeout (Direct Kafka)**
   ```
   Error connecting to bootstrap-server: Connection timeout
   ```
   Solution: Check network connectivity and security group settings

5. **Security Protocol Issues (Direct Kafka)**
   ```
   Error: SASL authentication failed
   ```
   Solution: Modify the `security_protocol` parameter in the script based on your cluster configuration

### Modifying Security Protocol (Direct Kafka Only)

If your MSK cluster uses TLS, SASL, or IAM authentication, modify the `security_protocol` parameter in `list_msk_topics_partitions.py`:

```python
# For TLS
security_protocol='SSL'

# For SASL/SCRAM
security_protocol='SASL_PLAINTEXT'

# For IAM
security_protocol='SASL_SSL'
```

## File Outputs

The scripts generate the following output files:
- `msk_clusters_YYYYMMDD_HHMMSS.json`: Detailed cluster information
- `msk_topics_partitions_CLUSTERNAME_YYYYMMDD_HHMMSS.json`: Detailed topics and partitions information (direct Kafka)
- `msk_cloudwatch_metrics_CLUSTERNAME_YYYYMMDD_HHMMSS.json`: CloudWatch metrics data

## Contributing

Feel free to submit issues and enhancement requests!
