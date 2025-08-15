#!/usr/bin/env python3
"""
Script to list topics and partitions for each MSK broker.
"""

import boto3
import json
import argparse
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from kafka import KafkaAdminClient, KafkaConsumer
from kafka.admin import ConfigResource, ConfigResourceType
from kafka.errors import KafkaError
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


def get_bootstrap_servers(cluster_arn):
    """
    Get bootstrap servers for an MSK cluster.
    
    Args:
        cluster_arn (str): The ARN of the MSK cluster
        
    Returns:
        list: List of bootstrap server strings
    """
    try:
        msk_client = boto3.client('kafka')
        response = msk_client.get_bootstrap_brokers(
            ClusterArn=cluster_arn
        )
        
        bootstrap_servers = []
        if 'BootstrapBrokerString' in response:
            bootstrap_servers.append(response['BootstrapBrokerString'])
        if 'BootstrapBrokerStringTls' in response:
            bootstrap_servers.append(response['BootstrapBrokerStringTls'])
        if 'BootstrapBrokerStringSaslScram' in response:
            bootstrap_servers.append(response['BootstrapBrokerStringSaslScram'])
        if 'BootstrapBrokerStringIam' in response:
            bootstrap_servers.append(response['BootstrapBrokerStringIam'])
            
        return bootstrap_servers
    except ClientError as e:
        logger.error(f"Error getting bootstrap servers: {e}")
        return []


def get_cluster_topics_and_partitions(bootstrap_servers, cluster_name):
    """
    Get topics and partitions information for an MSK cluster.
    
    Args:
        bootstrap_servers (list): List of bootstrap server strings
        cluster_name (str): Name of the MSK cluster
        
    Returns:
        dict: Dictionary containing topics and partitions information
    """
    cluster_info = {
        'cluster_name': cluster_name,
        'bootstrap_servers': bootstrap_servers,
        'topics': {},
        'total_topics': 0,
        'total_partitions': 0,
        'broker_info': {}
    }
    
    for bootstrap_server in bootstrap_servers:
        try:
            logger.info(f"Connecting to {bootstrap_server} for cluster {cluster_name}")
            
            # Create admin client
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_server,
                request_timeout_ms=30000,
                security_protocol='PLAINTEXT'  # Adjust based on your cluster configuration
            )
            
            # Get metadata
            metadata = admin_client._client.cluster
            topics = metadata.topics()
            
            cluster_info['total_topics'] = len(topics)
            
            for topic_name, topic_metadata in topics.items():
                partitions = topic_metadata.partitions
                cluster_info['topics'][topic_name] = {
                    'partitions': len(partitions),
                    'replication_factor': topic_metadata.replication_factor,
                    'partition_details': {}
                }
                
                cluster_info['total_partitions'] += len(partitions)
                
                # Get partition details
                for partition_id, partition_metadata in partitions.items():
                    cluster_info['topics'][topic_name]['partition_details'][partition_id] = {
                        'leader': partition_metadata.leader,
                        'replicas': partition_metadata.replicas,
                        'isr': partition_metadata.isr
                    }
            
            # Get broker information
            brokers = metadata.brokers()
            for broker_id, broker in brokers.items():
                cluster_info['broker_info'][broker_id] = {
                    'host': broker.host,
                    'port': broker.port,
                    'rack': getattr(broker, 'rack', None)
                }
            
            admin_client.close()
            break  # Use the first successful connection
            
        except Exception as e:
            logger.error(f"Error connecting to {bootstrap_server}: {e}")
            continue
    
    return cluster_info


def get_detailed_topic_info(bootstrap_servers, topic_name):
    """
    Get detailed information about a specific topic.
    
    Args:
        bootstrap_servers (list): List of bootstrap server strings
        topic_name (str): Name of the topic
        
    Returns:
        dict: Detailed topic information
    """
    for bootstrap_server in bootstrap_servers:
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_server,
                request_timeout_ms=30000,
                security_protocol='PLAINTEXT'
            )
            
            # Get topic configuration
            config_resource = ConfigResource(ConfigResourceType.TOPIC, topic_name)
            configs = admin_client.describe_configs([config_resource])
            
            topic_config = {}
            for config in configs[topic_name]:
                topic_config[config.name] = {
                    'value': config.value,
                    'default': config.default,
                    'source': config.source
                }
            
            admin_client.close()
            return topic_config
            
        except Exception as e:
            logger.error(f"Error getting topic config for {topic_name}: {e}")
            continue
    
    return {}


def print_cluster_summary(cluster_info):
    """
    Print a summary of cluster information.
    
    Args:
        cluster_info (dict): Cluster information dictionary
    """
    print(f"\n{'='*60}")
    print(f"Cluster: {cluster_info['cluster_name']}")
    print(f"{'='*60}")
    print(f"Bootstrap Servers: {', '.join(cluster_info['bootstrap_servers'])}")
    print(f"Total Topics: {cluster_info['total_topics']}")
    print(f"Total Partitions: {cluster_info['total_partitions']}")
    print(f"Number of Brokers: {len(cluster_info['broker_info'])}")
    
    print(f"\n{'='*60}")
    print("BROKER INFORMATION")
    print(f"{'='*60}")
    for broker_id, broker_info in cluster_info['broker_info'].items():
        print(f"Broker {broker_id}: {broker_info['host']}:{broker_info['port']}")
        if broker_info['rack']:
            print(f"  Rack: {broker_info['rack']}")
    
    print(f"\n{'='*60}")
    print("TOPICS AND PARTITIONS")
    print(f"{'='*60}")
    print(f"{'Topic Name':<30} {'Partitions':<12} {'Replication':<12}")
    print("-" * 60)
    
    for topic_name, topic_info in sorted(cluster_info['topics'].items()):
        print(f"{topic_name:<30} {topic_info['partitions']:<12} {topic_info['replication_factor']:<12}")
    
    # Show partition distribution across brokers
    print(f"\n{'='*60}")
    print("PARTITION DISTRIBUTION BY BROKER")
    print(f"{'='*60}")
    
    broker_partitions = {}
    for topic_name, topic_info in cluster_info['topics'].items():
        for partition_id, partition_info in topic_info['partition_details'].items():
            leader = partition_info['leader']
            if leader not in broker_partitions:
                broker_partitions[leader] = {'leader': 0, 'replica': 0}
            
            broker_partitions[leader]['leader'] += 1
            
            for replica in partition_info['replicas']:
                if replica not in broker_partitions:
                    broker_partitions[replica] = {'leader': 0, 'replica': 0}
                broker_partitions[replica]['replica'] += 1
    
    print(f"{'Broker':<10} {'Leader Partitions':<18} {'Total Replicas':<15}")
    print("-" * 50)
    for broker_id in sorted(broker_partitions.keys()):
        info = broker_partitions[broker_id]
        print(f"{broker_id:<10} {info['leader']:<18} {info['replica']:<15}")


def save_cluster_info(cluster_info):
    """
    Save cluster information to a JSON file.
    
    Args:
        cluster_info (dict): Cluster information dictionary
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"msk_topics_partitions_{cluster_info['cluster_name']}_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(cluster_info, f, indent=2, default=str)
        print(f"\nDetailed information saved to: {filename}")
    except Exception as e:
        logger.error(f"Error saving to file: {e}")


def main():
    """
    Main function to list topics and partitions for all MSK clusters.
    """
    parser = argparse.ArgumentParser(description='List MSK topics and partitions')
    parser.add_argument('--cluster-arn', help='Specific cluster ARN to analyze')
    parser.add_argument('--save-json', action='store_true', help='Save detailed output to JSON file')
    parser.add_argument('--detailed', action='store_true', help='Show detailed topic configuration')
    
    args = parser.parse_args()
    
    print("AWS MSK Topics and Partitions Lister")
    print("=" * 60)
    
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
            
            # Get bootstrap servers
            bootstrap_servers = get_bootstrap_servers(cluster_arn)
            if not bootstrap_servers:
                print(f"Could not get bootstrap servers for cluster {cluster_name}")
                continue
            
            # Get topics and partitions
            cluster_info = get_cluster_topics_and_partitions(bootstrap_servers, cluster_name)
            
            if cluster_info['total_topics'] == 0:
                print(f"No topics found in cluster {cluster_name}")
                continue
            
            # Print summary
            print_cluster_summary(cluster_info)
            
            # Save to JSON if requested
            if args.save_json:
                save_cluster_info(cluster_info)
            
            # Show detailed topic configuration if requested
            if args.detailed:
                print(f"\n{'='*60}")
                print("DETAILED TOPIC CONFIGURATIONS")
                print(f"{'='*60}")
                
                for topic_name in cluster_info['topics'].keys():
                    print(f"\nTopic: {topic_name}")
                    topic_config = get_detailed_topic_info(bootstrap_servers, topic_name)
                    for config_name, config_info in topic_config.items():
                        print(f"  {config_name}: {config_info['value']} (default: {config_info['default']})")
    
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your AWS credentials.")
        print("You can configure them using: aws configure")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
