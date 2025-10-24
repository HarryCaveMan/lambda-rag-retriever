from json import load as load_json_file
from boto3 import session
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict,Any

def parse_args():
    parser = ArgumentParser(
        prog="CreateNewUsagePlanWithKey",
        description="Creates a new usage plan with key for an AWS API gateway api"
    )
    parser.add_argument(
        "-p","--aws-profile",
        type=str,
        help="The AWS profile to use for the client session"
    )
    parser.add_argument(
        "-r","--aws-region",
        type=str,
        default="us-east-1",
        help="The AWS profile to use for the client session"
    )
    parser.add_argument(
        "-n","--usage-plan-name",
        type=str,
        help="The name to give the usage plan (will be propagated to the key with a \"_key\" suffix)"
    )
    return parser.parse_args().__dict__

def create_or_update_usage_plan(client,usage_plan_name,api_id,stage) -> str:
    res = client.create_usage_plan(
        name=usage_plan_name,
        description=f"Usage plan {usage_plan_name} for API {api_id}",
        apiStages=[
            {
                "apiId": api_id,
                "stage": stage
            }
        ]
    )
    return res["id"]

def create_api_key(client,usage_plan_id) -> (str,str):
    res = client.create_api_key(
        name=f"{usage_plan_id}_key",
        description=f"API key for usage plan {usage_plan_id}",
        enabled=True,
    )
    return res["id"],res["value"]

def create_usage_plan_key(client,usage_plan_id,key_id) -> None:
    client.create_usage_plan_key(
        usagePlanId=usage_plan_id,
        keyId=key_id,
        keyType="API_KEY"
    )

def get_stack_info(param_file_path: Path) -> (str,str):
    with open(param_file_path,"r") as paramfile:
        stack_params: Dict[str,Any] = load_json_file(paramfile)
    return stack_params["lambda"]["StackName"],next(param["ParameterValue"]  for param in stack_params["lambda"]["StackParams"] if param["ParameterKey"]=="Stage")

def get_gateway_id(cf,stack_name: str) -> str:
    return cf.describe_stack_resource(
        StackName=stack_name,
        LogicalResourceId="RestApi"
    )["StackResourceDetail"]["PhysicalResourceId"]

def main(aws_profile,aws_region,usage_plan_name) -> None:
    sess = session.Session(profile_name=aws_profile,region_name=aws_region)
    apig = sess.client('apigateway')
    stack_name,api_stage = get_stack_info(Path(__file__).parent/"params.json")
    cloudformation = sess.client('cloudformation')
    gateway_id: str = get_gateway_id(cloudformation,stack_name)
    usage_plan_id = create_or_update_usage_plan(apig,usage_plan_name,gateway_id,api_stage)
    key_id,key_value = create_api_key(apig,usage_plan_id)
    create_usage_plan_key(apig,usage_plan_id,key_id)
    print(f"Successfully created usage plan, new key: {key_value}")

if __name__ == "__main__":
    args = parse_args()
    main(**args)