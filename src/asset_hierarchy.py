# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Usage:
# python3 src/asset_hierarchy.py --asset-id <value> [--all-levels]
#
# Example:
# python3 src/asset_hierarchy.py --asset-id 066e9d16-b369-42fc-abf4-95ae81778b2c
# python3 src/asset_hierarchy.py --asset-id 2c8249d7-9391-4b66-a50d-7b311ea37aec --all-levels

import boto3
import time
import argparse
import uuid

sw_client = boto3.client('iotsitewise')
SCRIPT_TIMEOUT_SECONDS = 60

# Validate if the provided value is a valid UUID
def valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False

# Retrieve all associated assets for a given asset and hierarchy
def list_associated_assets(asset_id, hierarchy_id):
    all_associated_assets = []
    next_token = None
    # Paginate
    while True:
        if next_token:
            response = sw_client.list_associated_assets(assetId=asset_id,hierarchyId=hierarchy_id, nextToken=next_token)
        else:
            response = sw_client.list_associated_assets(assetId=asset_id,hierarchyId=hierarchy_id)
        associated_assets = response['assetSummaries']
        all_associated_assets += associated_assets
        # Check if there are more pages of results
        if 'nextToken' in response:
            next_token = response['nextToken']
        else:
            break   
        time.sleep(1) 
    return all_associated_assets

# Get name of an asset
def get_asset_name(asset_id):
    asset_name = None
    response = sw_client.describe_asset(assetId=asset_id,excludeProperties=True)
    asset_name = response['assetName']
    return asset_name

# Retrieve all child assets for a given asset
def get_child_assets(asset_id):
    child_assets = []
    response = sw_client.describe_asset(assetId=asset_id,excludeProperties=True)
    asset_hierarchies = response['assetHierarchies']
    for hierarchy in asset_hierarchies:
        hierarchy_id = hierarchy['id']
        associated_assets = list_associated_assets(asset_id,hierarchy_id)
        child_assets += associated_assets
        time.sleep(1)
    return child_assets

# Print hierarchy
def print_hierarchy(child_assets, hierarchy_level):
    elapsed_time = time.time() - script_start_time
    if elapsed_time > SCRIPT_TIMEOUT_SECONDS:
        raise Exception("Script execution timeout reached!")
    for child_asset in child_assets:
        child_asset_name = child_asset['name']
        child_asset_id = child_asset['id']
        position = 3 * (hierarchy_level-2)
        spaces = " " * position
        print(f'{spaces}|__ Asset Name: {child_asset_name}, Asset Id: {child_asset_id}')
        if not include_all_levels: continue
        next_level_child_assets = get_child_assets(child_asset_id)
        if len(next_level_child_assets)>0:
            print_hierarchy(next_level_child_assets, hierarchy_level+1)

if __name__ == "__main__":
    script_start_time = time.time()
    # Create the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments
    parser.add_argument("--asset-id", help="ID of the asset")
    parser.add_argument("--all-levels", help="Include all levels in the hierarchy", action="store_true")
    # Parse the arguments
    args = parser.parse_args()
    # Access the arguments
    asset_id = args.asset_id
    include_all_levels = args.all_levels
    # Validate the arguments
    if valid_uuid(asset_id):
        print(f'\nUser input successfully validated')
    else:
        raise Exception("\nInvalid Asset ID!")
    asset_name = get_asset_name(asset_id)
    child_assets = get_child_assets(asset_id)
    print(f'\nAsset Name: {asset_name}, Asset Id: {asset_id}')
    print_hierarchy(child_assets,2)