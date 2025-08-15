#!/usr/bin/env python3
"""
Script to list MSK clusters and their metrics using CloudWatch.
This approach doesn't require direct Kafka connectivity.
"""

import boto3
import json
import argparse
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_msk_clusters():
    """
    Get all MSK clusters from AWS account.
    
    Returns:
        list: List of MSK cluster information
    """
    try:
        msk_client = boto3.client('kafka')
        response = msk_client.list_clusters()
        return response['ClusterInfoList']
    except Exception as e:
        logger.error(f"Error getting MSK clusters: {e}")
        return []


def get_cluster_metrics(cluster_arn, cluster_name, start_time, end_time):
    """
    Get CloudWatch metrics for an MSK cluster.
    
    Args:
        cluster_arn (str): The ARN of the MSK cluster
        cluster_name (str): Name of the MSK cluster
        start_time (datetime): Start time for metrics
        end_time (datetime): End time for metrics
        
    Returns:
        dict: Dictionary containing cluster metrics
    """
    try:
        cloudwatch = boto3.client('cloudwatch')
        
        # Extract cluster name from ARN for metric dimensions
        cluster_name_metric = cluster_name.replace('-', '_')
        
        # Define metrics to retrieve
        metrics_to_get = [
            {
                'name': 'BytesInPerSec',
                'description': 'Bytes In Per Second',
                'unit': 'Bytes/Second'
            },
            {
                'name': 'BytesOutPerSec', 
                'description': 'Bytes Out Per Second',
                'unit': 'Bytes/Second'
            },
            {
                'name': 'MessagesInPerSec',
                'description': 'Messages In Per Second',
                'unit': 'Count/Second'
            },
            {
                'name': 'PartitionCount',
                'description': 'Number of Partitions',
                'unit': 'Count'
            },
            {
                'name': 'TopicCount',
                'description': 'Number of Topics',
                'unit': 'Count'
            },
            {
                'name': 'OfflinePartitionsCount',
                'description': 'Offline Partitions Count',
                'unit': 'Count'
            },
            {
                'name': 'UnderReplicatedPartitions',
                'description': 'Under Replicated Partitions',
                'unit': 'Count'
            },
            {
                'name': 'ActiveControllerCount',
                'description': 'Active Controller Count',
                'unit': 'Count'
            },
            {
                'name': 'GlobalTopicCount',
                'description': 'Global Topic Count',
                'unit': 'Count'
            },
            {
                'name': 'GlobalPartitionCount',
                'description': 'Global Partition Count',
                'unit': 'Count'
            }
        ]
        
        cluster_metrics = {
            'cluster_name': cluster_name,
            'cluster_arn': cluster_arn,
            'metrics': {},
            'summary': {}
        }
        
        for metric_info in metrics_to_get:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/Kafka',
                    MetricName=metric_info['name'],
                    Dimensions=[
                        {
                            'Name': 'Cluster Name',
                            'Value': cluster_name_metric
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5-minute periods
                    Statistics=['Average', 'Maximum', 'Minimum']
                )
                
                if response['Datapoints']:
                    # Get the latest datapoint
                    latest_datapoint = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                    
                    cluster_metrics['metrics'][metric_info['name']] = {
                        'description': metric_info['description'],
                        'unit': metric_info['unit'],
                        'latest_value': {
                            'average': latest_datapoint.get('Average'),
                            'maximum': latest_datapoint.get('Maximum'),
                            'minimum': latest_datapoint.get('Minimum'),
                            'timestamp': latest_datapoint['Timestamp'].isoformat()
                        },
                        'all_datapoints': [
                            {
                                'timestamp': dp['Timestamp'].isoformat(),
                                'average': dp.get('Average'),
                                'maximum': dp.get('Maximum'),
                                'minimum': dp.get('Minimum')
                            }
                            for dp in response['Datapoints']
                        ]
                    }
                    
                    # Add to summary for easy access
                    if metric_info['name'] in ['TopicCount', 'PartitionCount', 'GlobalTopicCount', 'GlobalPartitionCount']:
                        cluster_metrics['summary'][metric_info['name']] = latest_datapoint.get('Average', 0)
                        
                else:
                    logger.warning(f"No datapoints found for metric {metric_info['name']} in cluster {cluster_name}")
                    
            except ClientError as e:
                logger.error(f"Error getting metric {metric_info['name']} for cluster {cluster_name}: {e}")
                continue
        
        return cluster_metrics
        
    except Exception as e:
        logger.error(f"Error getting CloudWatch metrics for cluster {cluster_name}: {e}")
        return None


def get_broker_metrics(cluster_arn, cluster_name, start_time, end_time):
    """
    Get broker-specific metrics for an MSK cluster.
    
    Args:
        cluster_arn (str): The ARN of the MSK cluster
        cluster_name (str): Name of the MSK cluster
        start_time (datetime): Start time for metrics
        end_time (datetime): End time for metrics
        
    Returns:
        dict: Dictionary containing broker metrics
    """
    try:
        cloudwatch = boto3.client('cloudwatch')
        msk_client = boto3.client('kafka')
        
        # Get broker nodes
        try:
            nodes_response = msk_client.list_nodes(ClusterArn=cluster_arn)
            brokers = nodes_response['NodeInfoList']
        except ClientError:
            logger.warning(f"Could not get broker nodes for cluster {cluster_name}")
            return {}
        
        cluster_name_metric = cluster_name.replace('-', '_')
        broker_metrics = {}
        
        for broker in brokers:
            broker_id = broker['NodeInfo']['BrokerNodeInfo']['BrokerId']
            
            # Get broker-specific metrics
            broker_metrics_list = [
                'BytesInPerSec',
                'BytesOutPerSec',
                'MessagesInPerSec',
                'PartitionCount',
                'OfflinePartitionsCount',
                'UnderReplicatedPartitions'
            ]
            
            broker_metrics[broker_id] = {
                'broker_id': broker_id,
                'metrics': {}
            }
            
            for metric_name in broker_metrics_list:
                try:
                    response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/Kafka',
                        MetricName=metric_name,
                        Dimensions=[
                            {
                                'Name': 'Cluster Name',
                                'Value': cluster_name_metric
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': str(broker_id)
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Average', 'Maximum', 'Minimum']
                    )
                    
                    if response['Datapoints']:
                        latest_datapoint = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                        broker_metrics[broker_id]['metrics'][metric_name] = {
                            'latest_value': {
                                'average': latest_datapoint.get('Average'),
                                'maximum': latest_datapoint.get('Maximum'),
                                'minimum': latest_datapoint.get('Minimum'),
                                'timestamp': latest_datapoint['Timestamp'].isoformat()
                            }
                        }
                        
                except ClientError as e:
                    logger.debug(f"Error getting broker metric {metric_name} for broker {broker_id}: {e}")
                    continue
        
        return broker_metrics
        
    except Exception as e:
        logger.error(f"Error getting broker metrics for cluster {cluster_name}: {e}")
        return {}


def print_cluster_summary(cluster_metrics, broker_metrics):
    """
    Print a summary of cluster metrics.
    
    Args:
        cluster_metrics (dict): Cluster metrics dictionary
        broker_metrics (dict): Broker metrics dictionary
    """
    if not cluster_metrics:
        return
    
    print(f"\n{'='*80}")
    print(f"CLUSTER: {cluster_metrics['cluster_name']}")
    print(f"{'='*80}")
    print(f"ARN: {cluster_metrics['cluster_arn']}")
    
    # Print summary metrics
    summary = cluster_metrics.get('summary', {})
    print(f"\n{'='*40}")
    print("SUMMARY METRICS")
    print(f"{'='*40}")
    print(f"Topics: {summary.get('TopicCount', 'N/A')}")
    print(f"Partitions: {summary.get('PartitionCount', 'N/A')}")
    print(f"Global Topics: {summary.get('GlobalTopicCount', 'N/A')}")
    print(f"Global Partitions: {summary.get('GlobalPartitionCount', 'N/A')}")
    
    # Print detailed metrics
    print(f"\n{'='*40}")
    print("DETAILED METRICS")
    print(f"{'='*40}")
    
    for metric_name, metric_data in cluster_metrics.get('metrics', {}).items():
        latest = metric_data['latest_value']
        print(f"\n{metric_data['description']} ({metric_name}):")
        print(f"  Unit: {metric_data['unit']}")
        print(f"  Latest Average: {latest['average']}")
        print(f"  Latest Maximum: {latest['maximum']}")
        print(f"  Latest Minimum: {latest['minimum']}")
        print(f"  Timestamp: {latest['timestamp']}")
    
    # Print broker metrics
    if broker_metrics:
        print(f"\n{'='*40}")
        print("BROKER METRICS")
        print(f"{'='*40}")
        
        for broker_id, broker_data in broker_metrics.items():
            print(f"\nBroker {broker_id}:")
            for metric_name, metric_data in broker_data['metrics'].items():
                latest = metric_data['latest_value']
                print(f"  {metric_name}:")
                print(f"    Average: {latest['average']}")
                print(f"    Maximum: {latest['maximum']}")
                print(f"    Minimum: {latest['minimum']}")


def save_metrics_to_json(cluster_metrics, broker_metrics):
    """
    Save metrics to a JSON file.
    
    Args:
        cluster_metrics (dict): Cluster metrics dictionary
        broker_metrics (dict): Broker metrics dictionary
    """
    if not cluster_metrics:
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"msk_cloudwatch_metrics_{cluster_metrics['cluster_name']}_{timestamp}.json"
    
    output_data = {
        'cluster_metrics': cluster_metrics,
        'broker_metrics': broker_metrics,
        'generated_at': datetime.now().isoformat()
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\nDetailed metrics saved to: {filename}")
    except Exception as e:
        logger.error(f"Error saving to file: {e}")


def main():
    """
    Main function to get MSK metrics from CloudWatch.
    """
    parser = argparse.ArgumentParser(description='Get MSK metrics from CloudWatch')
    parser.add_argument('--cluster-arn', help='Specific cluster ARN to analyze')
    parser.add_argument('--hours', type=int, default=24, help='Number of hours to look back for metrics (default: 24)')
    parser.add_argument('--save-json', action='store_true', help='Save detailed output to JSON file')
    parser.add_argument('--broker-metrics', action='store_true', help='Include broker-specific metrics')
    
    args = parser.parse_args()
    
    print("AWS MSK CloudWatch Metrics Lister")
    print("=" * 60)
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=args.hours)
    
    print(f"Time range: {start_time.isoformat()} to {end_time.isoformat()}")
    
    try:
        if args.cluster_arn:
            # Analyze specific cluster
            clusters = [{'ClusterArn': args.cluster_arn, 'ClusterName': 'Specified Cluster'}]
        else:
            # Get all clusters
            clusters = get_msk_clusters()
        
        if not clusters:
            print("No MSK clusters found or accessible.")
            return
        
        for cluster in clusters:
            cluster_arn = cluster['ClusterArn']
            cluster_name = cluster['ClusterName']
            
            print(f"\nAnalyzing cluster: {cluster_name}")
            print(f"ARN: {cluster_arn}")
            
            # Get cluster metrics
            cluster_metrics = get_cluster_metrics(cluster_arn, cluster_name, start_time, end_time)
            
            if not cluster_metrics:
                print(f"Could not get metrics for cluster {cluster_name}")
                continue
            
            # Get broker metrics if requested
            broker_metrics = {}
            if args.broker_metrics:
                broker_metrics = get_broker_metrics(cluster_arn, cluster_name, start_time, end_time)
            
            # Print summary
            print_cluster_summary(cluster_metrics, broker_metrics)
            
            # Save to JSON if requested
            if args.save_json:
                save_metrics_to_json(cluster_metrics, broker_metrics)
    
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your AWS credentials.")
        print("You can configure them using: aws configure")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
