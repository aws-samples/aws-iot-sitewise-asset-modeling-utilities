# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Usage:
# python3 src/model_references.py --asset-model-id <value>
#
# Example:
# python3 src/model_references.py --asset-model-id ec6d3e7c-9026-4c1c-ac66-e73ba7666c2e

import boto3
import time
import argparse
import uuid
import csv
import os

src_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.dirname(src_dir))

sw_client = boto3.client('iotsitewise')
csv_file_name_suffix = f'references_{int(time.time())}.csv'
SCRIPT_TIMEOUT_SECONDS = 60*5 # 5 minutes
DATA_EXPORT_FOLDER_NAME = 'exported_data'
references = []
parent_models_map = {}

# Recommended actions
RECOMMENDED_ACTIONS = {
    'delete': 'DELETE',
    'delete_update': 'DELETE OR UPDATE',
    '': 'NO CHANGES OR '
}

# Validate if the provided value is a valid UUID
def valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False

# Retrieve name of the asset model
def get_asset_model_name(model_id):
    model_name = None
    response = sw_client.describe_asset_model(assetModelId=model_id,excludeProperties=True)
    model_name = response['assetModelName']
    return model_name

# Retrieve all models
def list_models():
    all_models = []
    next_token = None
    # Paginate
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
        time.sleep(1) 
    return all_models

# Retrieve assets created from a given model
def list_assets(model_id):
    all_assets = []
    next_token = None
    # Paginate
    while True:
        if next_token:
            response = sw_client.list_assets(assetModelId=model_id, nextToken=next_token)
        else:
            response = sw_client.list_assets(assetModelId=model_id)
        assets = response['assetSummaries']
        all_assets += assets
        # Check if there are more pages of results
        if 'nextToken' in response:
            next_token = response['nextToken']
        else:
            break   
        time.sleep(1) 
    return all_assets

# Get property name for a given model id and property id
def property_name_from_ids(model_id, property_id):
    property_name = ''
    response = sw_client.describe_asset_model(assetModelId=model_id)
    asset_model_properties = response['assetModelProperties']
    for item in asset_model_properties:
        if item['id'] == property_id: property_name = item['name']
    return property_name

# Map parent models for each model in SiteWise
def build_parent_models_map(models):
    global parent_models_map
    for model in models:
        model_id = model['id']
        response = sw_client.describe_asset_model(assetModelId=model_id, excludeProperties=True)
        asset_model_hierarchies = response['assetModelHierarchies']

        for hierarchy in asset_model_hierarchies:
            child_model_id = hierarchy['childAssetModelId']
            if child_model_id in parent_models_map:
                parent_models_map[child_model_id].append(model_id)
            else:
                parent_models_map[child_model_id] = [model_id]
        
        time.sleep(1/100) # Limit to a maximum of 100 DescribeAssetModel API calls per second

# Retrieve hierarchy references for the given model
def get_hierarchy_references(child_model_id):
    hierarchy_references_formatted = []

    if child_model_id in parent_models_map:
        for parent_id in parent_models_map[child_model_id]:
            response = sw_client.describe_asset_model(assetModelId=parent_id, excludeProperties=True)
            hierarchy_references = response['assetModelHierarchies']
            for model_hierarchy in hierarchy_references:  
                if model_hierarchy['childAssetModelId'] == child_model_id:
                    hierarchy_references_formatted.append({'assetModelId': parent_id,
                                            'assetModelName': response['assetModelName'],
                                            'hierarchyName': model_hierarchy['name'],
                                            'hierarchyId': model_hierarchy['id']})
    return hierarchy_references_formatted

# Retrieve dependent properties
def extract_dependent_properties(model_id, hierarchy_id, lower_level_properties):
    properties = []
    lower_level_property_ids = [property['propertyId'] for property in lower_level_properties]
    lower_level_property_names = [property['propertyName'] for property in lower_level_properties]
    response = sw_client.describe_asset_model(assetModelId=model_id)
    asset_model_properties = response['assetModelProperties']
    asset_model_hierarchies = response['assetModelHierarchies']

    for property in asset_model_properties:
        property_type_obj = property['type']
        property_name = property['name']
        property_id = property['id']
        property_type_name = list(property_type_obj.keys())[0]

        if property_type_name == 'metric' and 'variables' in property_type_obj[property_type_name]: 
            variables = property_type_obj[property_type_name]['variables']
            include_property = False
            dependent_on = ''
            for variable in variables:
                property_value_obj = variable['value']
                independent_property_id = property_value_obj['propertyId']
                # Property dependent on lower level properties
                if 'hierarchyId' in property_value_obj:
                    # Dependent on property part of dependency tree
                    if independent_property_id in lower_level_property_ids:
                        index = lower_level_property_ids.index(independent_property_id)
                        dependent_on += lower_level_property_names[index] + ','
                    # Dependent on property not part of dependency tree
                    else:
                        child_model_id = ''
                        for item in asset_model_hierarchies:
                            if item['id'] == property_value_obj['hierarchyId']: 
                                child_model_id = item['childAssetModelId']
                                break
                        independent_property_name = property_name_from_ids(child_model_id, independent_property_id)
                        dependent_on += independent_property_name + ','
                # Property not dependent on lower level properties
                else:
                    independent_property_name = ''
                    for item in asset_model_properties:
                        if item['id'] == independent_property_id: independent_property_name = item['name']
                    dependent_on += independent_property_name + ','

                if ('hierarchyId' in property_value_obj and property_value_obj['hierarchyId'] == hierarchy_id and
                        (independent_property_id in lower_level_property_ids or len(lower_level_properties) == 0)):
                    include_property = True

            if include_property:
                properties.append({'propertyName': property_name, 'propertyType': property_type_name, 'propertyId': property_id,
                                   'propertyDependentOn': dependent_on})
    return properties

# Retrieve references for the given model
def get_references(models, model_id, reference_level, lower_level_properties):
    elapsed_time = time.time() - script_start_time
    if elapsed_time > SCRIPT_TIMEOUT_SECONDS:
        raise Exception("\n Script execution timeout reached!")
    global references

    if reference_level == 1:
        assets = list_assets(model_id)
        for asset in assets:
            references.append([reference_level, 'Asset', asset['name'], asset['id'], '', '', '', '', '', '', '', ''])   

    hierarchy_references = get_hierarchy_references(model_id)
    for hierarchy in hierarchy_references:
        parent_model_id = hierarchy['assetModelId']
        parent_model_name = hierarchy['assetModelName']
        hierarchy_id = hierarchy['hierarchyId']
        hierarchy_name = hierarchy['hierarchyName']
        if reference_level == 1:
            references.append([reference_level, 'Hierarchy Definition', '', '', hierarchy_name, hierarchy_id, parent_model_name, parent_model_id, '', '', '', ''])
        properties = extract_dependent_properties(parent_model_id, hierarchy_id, lower_level_properties)
        for property in properties:
            references.append([reference_level+1, 'Property', '', '', hierarchy_name, hierarchy_id, parent_model_name, parent_model_id, property['propertyName'], property['propertyId'], property['propertyType'], property['propertyDependentOn']])
        print(f'\tChecking references at model: {get_asset_model_name(parent_model_id)}..')
        if len(properties) > 0: get_references(models, parent_model_id, reference_level+1, properties)

if __name__ == "__main__":
    script_start_time = time.time()
    # Create the argument parser
    parser = argparse.ArgumentParser()
    # Add the arguments
    parser.add_argument("--asset-model-id", help="ID of the asset model")
    # Parse the arguments
    args = parser.parse_args()
    # Access the arguments
    asset_model_id = args.asset_model_id
    # Validate the arguments
    if valid_uuid(asset_model_id):
        print(f'\nUser input successfully validated')
    else:
        raise Exception("\nInvalid Asset Model ID!")
    
    models = list_models()
    print(f'\nBuilding a map of all hierarchy references for all models..')
    build_parent_models_map(models)
    model_name = get_asset_model_name(asset_model_id)

    print(f'\nFinding references for model: {model_name}..')
    get_references(models, asset_model_id, 1, [])
    
    if len(references) > 0: 
        file_path = f'{root_dir}/{DATA_EXPORT_FOLDER_NAME}/{model_name}_{csv_file_name_suffix}'
        csv_file = open(file_path, mode='w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Reference Level', 'Reference Type', 'Asset Name', 'Asset ID', 'Hierarchy Name', 'Hierarchy ID', 'Model Name', 'Model ID', 'Property Name', 'Property ID', 'Property Type', 'Property Dependent On'])
        for reference in references: csv_writer.writerow(reference)
        csv_file.close()
        print(f'\nExported references to {file_path}')
    else:
        print(f'\nNo references found!')