# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Usage:
# python3 src/search_models.py [--no-properties] [--no-assets] [--no-hierarchy-definitions] [--no-hierarchy-references]
#
# Examples:
# python3 src/search_models.py
# python3 src/search_models.py --no-properties
# python3 src/search_models.py --no-assets --no-hierarchy-definitions
# python3 src/search_models.py --no-properties --no-assets --no-hierarchy-definitions --no-hierarchy-references

import boto3
import time
import argparse
import uuid
import csv
import os

src_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.dirname(src_dir))

sw_client = boto3.client('iotsitewise')
DATA_EXPORT_FOLDER_NAME = 'exported_data'
csv_file_path = f'{root_dir}/{DATA_EXPORT_FOLDER_NAME}/filtered_models_{int(time.time())}.csv'

# Validate if the provided value is a valid UUID
def valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False

# Retrieve all models from AWS IoT SiteWise
def list_models():
    all_models = []
    next_token = None
    # Retrieve list of asset models using pagination
    while True:
        if next_token:
            response = sw_client.list_asset_models(nextToken=next_token)
        else:
            response = sw_client.list_asset_models()
        asset_models = response['assetModelSummaries']
        all_models += asset_models
        # Check if there are more pages of results
        if 'nextToken' in response:
            next_token = response['nextToken']
        else:
            break   
        time.sleep(1) # Limit to a maximum of 1 ListAssetModels API calls per second
    return all_models

# Return True if the provided model has associated assets
def model_has_assets(model_id):
    has_assets = False
    response = sw_client.list_assets(assetModelId=model_id)
    assets = response['assetSummaries']
    if len(assets) > 0: has_assets = True
    return has_assets

# Filter models based on the provided filtering criteria
def filter_models(no_hierarchy_references_filter,no_hierarchy_definitions_filter,no_properties_filter,no_assets_filter):
    filter_count_map = {}
    parent_models_map = {}
    active_filter_count = no_hierarchy_references_filter+no_hierarchy_definitions_filter+no_properties_filter+no_assets_filter
    filtered_models = []
    models = list_models()
    print(f'\nAnalyzing models..')
    # Build maps for each model
    for idx, model in enumerate(models):
        model_id = model['id']
        response = sw_client.describe_asset_model(
            assetModelId=model_id)
        asset_model_properties = response['assetModelProperties']
        asset_model_hierarchies = response['assetModelHierarchies']
        filter_match_count = 0
        
        if no_hierarchy_definitions_filter and len(asset_model_hierarchies) == 0: filter_match_count += 1
        if no_properties_filter and len(asset_model_properties) == 0: filter_match_count += 1
        if no_assets_filter and not model_has_assets(model_id): filter_match_count += 1
        filter_count_map[model_id] = filter_match_count

        for hierarchy in asset_model_hierarchies:
            child_model_id = hierarchy['childAssetModelId']
            if child_model_id in parent_models_map:
                parent_models_map[child_model_id].append(model_id)
            else:
                parent_models_map[child_model_id] = [model_id]
        
        progress = round((idx+1) / len(models) * 100, 1)
        print(f"\tProgress: {progress}%")
        time.sleep(1/30) # Limit to a maximum of 30 DescribeAssetModel and 30 ListAssets API calls per second
    
    # Update the maps and filter the models
    for idx, model in enumerate(models):
         model_id = model['id']
         if model_id in parent_models_map: 
             if model_id in filter_count_map: 
                filter_count_map[model_id] += 1
             else:
                filter_count_map[model_id] = 1
         if active_filter_count == 0 or (model_id in filter_count_map and active_filter_count == filter_count_map[model_id]):
            filtered_models.append(model)
                                                                         
    return filtered_models

if __name__ == "__main__":
    script_start = time.time()
    # Create the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments
    parser.add_argument("--no-hierarchy-references", help="Filter models not referenced by other asset models", action="store_true")
    parser.add_argument("--no-hierarchy-definitions", help="Filter models without any hierarchy definitions", action="store_true")
    parser.add_argument("--no-properties", help="Filter models with no properties", action="store_true")
    parser.add_argument("--no-assets", help="Filter models with no corresponding assets", action="store_true")
    # Parse the arguments
    args = parser.parse_args()
    # Access the arguments
    no_hierarchy_references_filter = args.no_hierarchy_references
    no_hierarchy_definitions_filter = args.no_hierarchy_definitions
    no_properties_filter = args.no_properties
    no_assets_filter = args.no_assets
    
    filtered_models = filter_models(no_hierarchy_references_filter,no_hierarchy_definitions_filter,no_properties_filter,no_assets_filter)
    filtered_model_count = len(filtered_models)
    if filtered_model_count == 0:
        print(f'\nNo models with provided conditions are found!')
    else:
        print(f'\nModels with provided conditions: {filtered_model_count}')
        
        csv_file = open(csv_file_path, mode='w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Model Name', 'Model ID'])

        for model in filtered_models:
            model_name = model['name']
            model_id = model['id']
            print(f'\tModel Name: {model_name}, Model Id: {model_id}')
            csv_writer.writerow([model_name, model_id])
        csv_file.close()
        print(f'\nExported references to {csv_file_path}')
    print(f'\n** Total execution time: {round((time.time() - script_start))} seconds **')