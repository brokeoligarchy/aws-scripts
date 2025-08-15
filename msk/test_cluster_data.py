#!/usr/bin/env python3
"""
Simple test script to check MSK cluster data structure.
"""

import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

def test_msk_clusters():
    """Test function to see the structure of MSK cluster data."""
    try:
        msk_client = boto3.client('kafka')
        response = msk_client.list_clusters()
        
        print("MSK Clusters Response Structure:")
        print("=" * 50)
        print(f"Response type: {type(response)}")
        print(f"Response keys: {list(response.keys())}")
        
        if 'ClusterInfoList' in response:
            clusters = response['ClusterInfoList']
            print(f"\nNumber of clusters: {len(clusters)}")
            
            for i, cluster in enumerate(clusters):
                print(f"\nCluster {i+1}:")
                print(f"  Type: {type(cluster)}")
                print(f"  Keys: {list(cluster.keys())}")
                
                # Print key values
                for key in ['ClusterName', 'ClusterArn', 'State']:
                    if key in cluster:
                        print(f"  {key}: {cluster[key]}")
                    else:
                        print(f"  {key}: NOT FOUND")
                
                # Print first few items as example
                if i == 0:
                    print(f"  Full cluster data (first cluster):")
                    print(json.dumps(cluster, indent=2, default=str))
        
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your AWS credentials.")
    except ClientError as e:
        print(f"AWS Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_msk_clusters()
