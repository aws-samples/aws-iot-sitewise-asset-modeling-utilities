# AWS IoT SiteWise Asset Modeling Utilities

## Table of contents
1. [About this Repo](#about-this-repo)
2. [Prerequisites](#prerequisites)
3. [How to use?](#how-to-use)
    1. [Prepare your environment](#1-prepare-your-environment)
    2. [Searching models](#2-search-models)
    3. [Find model references](#3-find-model-references)
    4. [Retrieve asset hierarchy](#4-retrieve-asset-hierarchy)

## About this Repo
This repo provides code samples to interact with AWS IoT SiteWise Models and Assets using [AWS SDK for Python (Boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iotsitewise.html). Using this repo, you can easily search models, find references for a given model and retrieve asset hierarchy.

## Pre-requisities
1. An active AWS account
2. Supported region for AWS IoT SiteWise
3. IAM user with administrator access to AWS IoT SiteWise

## How to use
### 1) Prepare your environment
1. Configure [AWS credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html) either using config file or shared credential file. Ensure your region is configured in the config file.

2. Ensure Python 3 is installed on your system, you can verify by running `python3 --version` or `python --version` (on Windows).

3. Clone this repository using `git clone https://github.com/aws-samples/aws-iot-sitewise-asset-modeling-utilities`

4. Install required Python modules by running `pip install -r requirements.txt`

### 2) Search models
Retrieve a list of models that meet the filtering criteria and export the list to a CSV file.

####Synopsis:
```python
python3 src/search_models.py 
[--no-properties]
[--no-assets]
[--no-hierarchy-definitions]
[--no-hierarchy-references]
```
####Options:
`--no-properties` (boolean)
Exclude models with no properties.

`--no-assets` (boolean)
Exclude models with no assets.

`--no-hierarchy-definitions` (boolean)
Exclude models with no hierarchy definitions.

`--no-hierarchy-references` (boolean)
Exclude models that are not referenced in hierarchy definitions of other models.

####Examples:
`python3 src/search_models.py --no-properties --no-assets`

Output:
```
Analyzing models..
        Progress: 3.4%
        Progress: 6.9%
        Progress: x.x%
Models with provided conditions: 2
        Model Name: Pumping Station Model, Model Id: 75a0a3e2-af8f-4780-b8c5-607c397ec581
        Model Name: PumpTest, Model Id: cd602abe-5320-4c0f-a640-9fb22a9aa1c5
Exported references to /Users/gottraju/aws-iot-sitewise-asset-modeling-utilities/exported_data/filtered_models_1693800235.csv
** Total execution time: 6 seconds **
```
### 3) Find model references
Retrieve a list of references for a given model, which may include assets, hierarchy references, and properties (roll-up metrics), and export the list to a CSV file.

####Synopsis:
```python
python3 src/model_references.py
--asset-model-id <value>
```
####Options:
`--asset-model-id` (string)
The ID of the asset model.

####Examples:
`python3 src/model_references.py --asset-model-id ec6d3e7c-9026-4c1c-ac66-e73ba7666c2e`

Output:
```
User input successfully validated

Building a map of all hierarchy references for all models..

Finding references for model: CNC Machine..
        Checking references at model: Address..
        Checking references at model: Line..
        Checking references at model: Line..

Exported references to /Users/gottraju/aws-iot-sitewise-asset-modeling-utilities/exported_data/CNC Machine_references_1693801432.csv
```
### 4) Retrieve asset hierarchy
Retrieve asset hierarchy for a given asset.

####Synopsis:
```python
python3 src/asset_hierarchy.py
--asset-id <value>
[--all-levels] 
```
####Options:
`--asset-id` (string)
The ID of the asset.

`--all-levels` (boolean)
Include all lower levels in the asset hierarchy.
####Examples:
`python3 src/asset_hierarchy.py --asset-id 2c8249d7-9391-4b66-a50d-7b311ea37aec --all-levels`

Output:
```
User input successfully validated

Asset Name: Octank Manufacturing, Asset Id: 2c8249d7-9391-4b66-a50d-7b311ea37aec
|__ Asset Name: Site A, Asset Id: 494b247c-6f7d-498a-9789-5c08cb007f30
   |__ Asset Name: Pumping Station 1, Asset Id: c1aceb02-d043-410e-aea1-29e06d551c11
      |__ Asset Name: Pump 1-3, Asset Id: 73bd0b2e-16a8-4242-85cf-f25f4e2acbb2
      |__ Asset Name: Pump 1-2, Asset Id: 261768b2-f2bc-4b0e-9b99-abe5607872bc
      |__ Asset Name: Pump 1-1, Asset Id: 7a0bf6d4-04e0-4807-a75c-165e49510568
      |__ Asset Name: Pump 1-4, Asset Id: 4732c981-4497-4416-93f2-b23f0176745b
      |__ Asset Name: Pump 1-5, Asset Id: 985df25b-b56e-4421-84e5-c1b972c25ec6
   |__ Asset Name: Pumping Station 2, Asset Id: ad0dd5ae-bb89-4c43-b66c-f2038145a0f0
      |__ Asset Name: Pump 2-2, Asset Id: c3b9cf15-cda8-4f34-814a-c61b3304a046
      |__ Asset Name: Pump 2-3, Asset Id: 9cf8ade0-8733-402a-8a58-91491fb99934
      |__ Asset Name: Pump 2-1, Asset Id: 08b1f0a5-0b59-4a72-94ff-6cd68820e530
```