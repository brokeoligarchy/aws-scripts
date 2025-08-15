#!/usr/bin/env python3
"""
Script to list all MSK clusters in an AWS account.
"""

import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError


def list_msk_clusters():
    """
    List all MSK clusters in the AWS account.
    """
    try:
        # Initialize the MSK client
        msk_client = boto3.client('kafka')
        
        # Get all MSK clusters
        response = msk_client.list_clusters()
        
        if not response['ClusterInfoList']:
            print("No MSK clusters found in this AWS account.")
            return
        
        print(f"Found {len(response['ClusterInfoList'])} MSK cluster(s):\n")
        
        for cluster in response['ClusterInfoList']:
            print(f"Cluster Name: {cluster['ClusterName']}")
            print(f"Cluster ARN: {cluster['ClusterArn']}")
            print(f"State: {cluster['State']}")
            print(f"Kafka Version: {cluster['CurrentBrokerSoftwareInfo']['KafkaVersion']}")
            print(f"Number of Broker Nodes: {cluster['NumberOfBrokerNodes']}")
            
            # Get broker information
            if cluster['State'] == 'ACTIVE':
                try:
                    broker_response = msk_client.list_nodes(
                        ClusterArn=cluster['ClusterArn']
                    )
                    print(f"Active Brokers: {len(broker_response['NodeInfoList'])}")
                except ClientError as e:
                    print(f"Could not get broker info: {e}")
            
            # Get tags if available
            try:
                tags_response = msk_client.list_tags_for_resource(
                    ResourceArn=cluster['ClusterArn']
                )
                if tags_response['Tags']:
                    print("Tags:")
                    for tag in tags_response['Tags']:
                        print(f"  {tag['Key']}: {tag['Value']}")
            except ClientError:
                print("Tags: Not available")
            
            print("-" * 50)
        
        # Save detailed output to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"msk_clusters_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(response['ClusterInfoList'], f, indent=2, default=str)
        
        print(f"\nDetailed cluster information saved to: {filename}")
        
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your AWS credentials.")
        print("You can configure them using: aws configure")
    except ClientError as e:
        print(f"AWS Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def get_cluster_details(cluster_arn):
    """
    Get detailed information about a specific MSK cluster.
    
    Args:
        cluster_arn (str): The ARN of the MSK cluster
    """
    try:
        msk_client = boto3.client('kafka')
        
        response = msk_client.describe_cluster(
            ClusterArn=cluster_arn
        )
        
        cluster = response['ClusterInfo']
        
        print(f"\nDetailed information for cluster: {cluster['ClusterName']}")
        print(f"ARN: {cluster['ClusterArn']}")
        print(f"State: {cluster['State']}")
        print(f"Creation Time: {cluster['CreationTime']}")
        print(f"Kafka Version: {cluster['CurrentBrokerSoftwareInfo']['KafkaVersion']}")
        print(f"Number of Broker Nodes: {cluster['NumberOfBrokerNodes']}")
        
        # Broker configuration
        if 'BrokerNodeGroupInfo' in cluster:
            broker_info = cluster['BrokerNodeGroupInfo']
            print(f"Instance Type: {broker_info['InstanceType']}")
            print(f"Client Subnets: {broker_info['ClientSubnets']}")
            if 'SecurityGroups' in broker_info:
                print(f"Security Groups: {broker_info['SecurityGroups']}")
        
        # Encryption configuration
        if 'EncryptionInfo' in cluster:
            encryption = cluster['EncryptionInfo']
            print(f"Encryption at Rest: {encryption.get('EncryptionAtRest', 'Not configured')}")
            print(f"Encryption in Transit: {encryption.get('EncryptionInTransit', 'Not configured')}")
        
        return cluster
        
    except ClientError as e:
        print(f"Error getting cluster details: {e}")
        return None


if __name__ == "__main__":
    print("AWS MSK Cluster Lister")
    print("=" * 50)
    
    # List all clusters
    list_msk_clusters()
    
    # Optionally get details for a specific cluster
    # Uncomment the following lines and provide a cluster ARN to get detailed info
    # cluster_arn = "arn:aws:kafka:region:account:cluster/cluster-name/..."
    # get_cluster_details(cluster_arn)
