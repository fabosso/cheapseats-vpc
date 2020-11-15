import json
import jmespath
import boto3

from os import environ
from botocore.exceptions import ClientError

ec2 = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')
ssm = boto3.client('ssm')

vpc = environ.get('VPC_ID')
vpcname = environ.get('VPC_NAME')

def get_ssm_parameter(param):
    json = ssm.get_parameter(Name=param)
    
    return jmespath.search('Parameter.Value', json)

def list_target_routes():
    routes_json = ec2.describe_route_tables(Filters=[{'Name' : 'tag:VPN-Accessible', 'Values' : ['Yes', 'True']},
                                                     {'Name' : 'vpc-id', 'Values' : [vpc]}])
    return jmespath.search('RouteTables[*].RouteTableId', routes_json)
    
def vpn_launched(instanceid):
    print("Instance Launched: %s\n" % instanceid)
    vpn_instance = ec2_resource.Instance(instanceid)
    vpn_cidr = get_ssm_parameter('/%s/VPN/HomeNetworkCIDR' % vpcname)
    
    vpn_instance.wait_until_running()
    print("Instance Running: %s\n" % instanceid)
    
    # Disable Source / Destination check to allow this box to act as an OpenVPN router.
    ec2.modify_instance_attribute(InstanceId=instanceid, SourceDestCheck={'Value': False})
    print("Source Destination Check disabled")
    
    for routeTableId in list_target_routes():
        print("Adding VPN route for Route Table %s" % routeTableId)
        ec2.create_route(RouteTableId = routeTableId, DestinationCidrBlock = vpn_cidr, InstanceId = instanceid)

def vpn_stopped(instanceid):
    print("Instance Stopped: %s\n" % instanceid)
    
    vpn_cidr = get_ssm_parameter('/%s/VPN/HomeNetworkCIDR' % vpcname)
    for routeTableId in list_target_routes():
        print("Removing VPN route for Route Table %s" % routeTableId)
        try:
            ec2.delete_route(RouteTableId = routeTableId, DestinationCidrBlock = vpn_cidr)
        except ClientError as e:
            # We expect the occasional failure where the route doesn't exist - this can be safely ignored.
            if e.response['Error']['Code'] != 'InvalidRoute.NotFound':
                raise e
            else:
                print("No route to remove")

def notification_handler(event, context):
    for message_raw in jmespath.search('Records[*].Sns.Message', event):
        message_json = json.loads(message_raw)
        
        (instanceid, event) = jmespath.search('[EC2InstanceId, Event]', message_json)
        
        if event == 'autoscaling:EC2_INSTANCE_LAUNCH':
            vpn_launched(instanceid)
        elif event == 'autoscaling:EC2_INSTANCE_TERMINATE':
            vpn_stopped(instanceid)
        else:
            print('Unhandled Event: %s\n' % event)
