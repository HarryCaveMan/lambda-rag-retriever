from json import load as load_json_file
from argparse import ArgumentParser
from typing import Dict,Union,Optional
from boto3 import session
from botocore.exceptions import ClientError,WaiterError
from pathlib import Path
from uuid import uuid4
import json

def parse_args() -> Dict[str,str]:
    parser = ArgumentParser(
            prog="EmbeddingDeploy",
            description="Manage The ECR and Lambda stacks for rag embedding"
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
        "-s","--stack",
        type=str,
        default="us-east-1",
        help="The AWS profile to use for the client session"
    )
    parser.add_argument(
        "-u","--uuid",
        type=str,
        default=None,
        help="The uuid of this deployment"
    )
    return parser.parse_args().__dict__

def get_stack_op(cf,stack_name: str) -> str:
    try:
        stack = cf.describe_stacks(
            StackName=stack_name
        )["Stacks"][0]
        stack_state: str = stack["StackStatus"]
        if stack_state == "REVIEW_IN_PROGRESS":
            if stack.get("ChangeSetId") is None:
                return "CREATE"
        return "UPDATE"
    except ClientError as e:
        if e.response.get("Error",{}).get("Code") == "ValidationError":
            return "CREATE"
        else: raise e

def deploy(cf,stack_name: str,stack_op: str,stack_params:Dict[str,str],template_path: Path, uuid: str) -> (str,str):
    print(f"Deploying {stack_op} ChangeSet to {stack_name}...")
    change_set_name: str = "-".join((
        stack_name,
        stack_op,
        uuid
    ))
    try:
        with open(template_path,"r") as template_buffer:
            change_set = cf.create_change_set(
                ChangeSetName=change_set_name,
                StackName=stack_name,
                Parameters=stack_params,
                TemplateBody=template_buffer.read(),
                ChangeSetType=stack_op,
                OnStackFailure="DELETE" if stack_op == "CREATE" else "ROLLBACK",
                Capabilities=["CAPABILITY_IAM","CAPABILITY_NAMED_IAM","CAPABILITY_AUTO_EXPAND"]
            )
        changeset_waiter = cf.get_waiter('change_set_create_complete')
        changeset_waiter.wait(
            ChangeSetName=change_set["Id"]
        )
        print(f"{stack_op} ChangeSet created, executing ChangeSet...")
        cf.execute_change_set(
            ChangeSetName=change_set["Id"],
        )
        stack_waiter = cf.get_waiter('stack_create_complete') if stack_op == "CREATE" else  cf.get_waiter('stack_update_complete')
        stack_waiter.wait(
            StackName=stack_name
        )
    except WaiterError as e:
        raise Exception(f"Stack update failed for the following reason:\n\n{e.last_response}")
    return change_set["Id"],change_set["StackId"]

def main(stack: str,aws_profile: str,aws_region,uuid: Optional[str] = None) -> None:
    cicd_dir: Path = Path(__file__).absolute().parent
    cft_dir: Path = cicd_dir.parent.parent/"infra"/"cft"
    params_path: Path = cicd_dir/"params.json"
    template_path: Path = cft_dir/f"{stack}.yaml"
    sess = session.Session(profile_name=aws_profile,region_name=aws_region)
    cloudformation = sess.client("cloudformation")
    s3 = sess.client("s3")

    with open(params_path,"r") as params_json:
        params: Dict[str,Union[str,Dict[str,str]]] = load_json_file(params_json)

    stack_name: str = params[stack]["StackName"]
    stack_params: Dict[str,str] = params[stack]["StackParams"]
    stack_op: str = get_stack_op(cloudformation,stack_name)
    uuid = str(uuid4()) if uuid is None else uuid
    stack_params.append(
        {
            "ParameterKey":"Uuid",
            "ParameterValue":uuid
        }
    )

    change_set_id,stack_id = deploy(cloudformation,stack_name,stack_op,stack_params,template_path,uuid)

    print(f"Done:\n  Change Set ID: {change_set_id}\n  Stack ID: {stack_id}")

if __name__ == "__main__":
    main(**parse_args())