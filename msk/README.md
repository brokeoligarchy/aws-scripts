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

## Usage

### List MSK Clusters
```bash
python list_msk_clusters.py
```

This will:
- List all MSK clusters in your AWS account
- Display basic information for each cluster
- Save detailed information to a timestamped JSON file

### List Topics and Partitions
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

## Command Line Options for `list_msk_topics_partitions.py`

- `--cluster-arn`: Specify a particular cluster ARN to analyze
- `--save-json`: Save detailed output to a JSON file
- `--detailed`: Show detailed topic configurations

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

### Topics and Partitions Output
```
AWS MSK Topics and Partitions Lister
============================================================

Cluster: my-production-cluster
============================================================
Bootstrap Servers: b-1.mycluster.abc123.c2.kafka.us-east-1.amazonaws.com:9092
Total Topics: 5
Total Partitions: 15
Number of Brokers: 3

============================================================
BROKER INFORMATION
============================================================
Broker 1: 10.0.1.10:9092
Broker 2: 10.0.1.11:9092
Broker 3: 10.0.1.12:9092

============================================================
TOPICS AND PARTITIONS
============================================================
Topic Name                       Partitions   Replication  
------------------------------------------------------------
user-events                      3            3            
order-updates                    6            3            
system-logs                      3            3            
data-stream                      2            3            
analytics-data                   1            3            

============================================================
PARTITION DISTRIBUTION BY BROKER
============================================================
Broker     Leader Partitions   Total Replicas  
--------------------------------------------------
1          5                   15              
2          5                   15              
3          5                   15              
```

## Security Considerations

- The scripts use `PLAINTEXT` security protocol by default. For production clusters, you may need to modify the security protocol based on your cluster configuration (TLS, SASL, IAM)
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

3. **Connection Timeout**
   ```
   Error connecting to bootstrap-server: Connection timeout
   ```
   Solution: Check network connectivity and security group settings

4. **Security Protocol Issues**
   ```
   Error: SASL authentication failed
   ```
   Solution: Modify the `security_protocol` parameter in the script based on your cluster configuration

### Modifying Security Protocol

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
- `msk_topics_partitions_CLUSTERNAME_YYYYMMDD_HHMMSS.json`: Detailed topics and partitions information

## Contributing

Feel free to submit issues and enhancement requests!
