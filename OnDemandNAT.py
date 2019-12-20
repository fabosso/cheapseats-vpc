import json
import os
import boto3
import jmespath
import random
from datetime import datetime, timedelta

from botocore.exceptions import ClientError

ec2 = boto3.client('ec2')

def ec2_need_natgw():
    # Returns a True if any currently running instances have
    # The 'NAT-Required' tag set.
    filters = [
        {'Name': 'tag:NAT-Required', 'Values' : ['True','Yes']},
        {'Name': 'instance-state-name', 'Values' : ['running']}
    ]
    instances = ec2.describe_instances(Filters=filters)
    
    if (len(instances['Reservations']) > 0):
        return True
    else:
        return False
        
def vpc_has_natgw():
    filters = [
        {'Name': 'tag:OnDemandNAT', 'Values' : ['True','Yes']},
        {'Name': 'state', 'Values' : ['pending', 'available']}
    ]
    
    gateway_json = ec2.describe_nat_gateways(Filters=filters)
    gateways = jmespath.search('NatGateways[*].[NatGatewayId, State, CreateTime]', gateway_json)
    
    if len(gateways) > 0:
        return gateways
    else:
        return None
    
def create_nat_gateway():
    alloc_json = ec2.describe_addresses(Filters=[{'Name' : 'tag:Name', 'Values' : ['OnDemandNAT-IPAddr']}])
    allocId = jmespath.search('Addresses[0].AllocationId', alloc_json )
    
    subnet_json = ec2.describe_subnets(Filters=[{'Name' : 'tag:Public', 'Values' : ['Yes']}])
    subnet_list = jmespath.search('Subnets[*].SubnetId', subnet_json)
    subnetId = random.choice(subnet_list)
    
    new_gw_json = ec2.create_nat_gateway(AllocationId=allocId, SubnetId=subnetId)
    gatewayId = jmespath.search('NatGateway.NatGatewayId' , new_gw_json)
        
    ec2.create_tags(Resources=[gatewayId], Tags=[{'Key' : 'OnDemandNAT', 'Value' : 'True'}, {'Key' : 'Name', 'Value' : 'OnDemandNAT-Gateway'}])
    return gatewayId
    
def update_route_tables(gatewayId):
    routes_json = ec2.describe_route_tables(Filters=[{'Name' : 'tag:OnDemandNAT', 'Values' : ['Yes', 'True']}])
    routes_list = jmespath.search('RouteTables[*].RouteTableId', routes_json)
    
    # Wait for gateway to finish starting.
    waiter = ec2.get_waiter('nat_gateway_available')
    waiter.wait(NatGatewayIds = [gatewayId])
    
    for routeTableId in routes_list:
        try:
            ec2.delete_route(RouteTableId = routeTableId, DestinationCidrBlock = '0.0.0.0/0')
        except ClientError as e:
            # We expect the occasional failure where the route doesn't exist - this can be safely ignored.
            if e.response['Error']['Code'] != 'InvalidRoute.NotFound':
                raise e
        ec2.create_route(RouteTableId = routeTableId, DestinationCidrBlock = '0.0.0.0/0', NatGatewayId = gatewayId)
    
def autolaunch_handler(event, context):
    
    nat_needed = ec2_need_natgw()
    gateway_list = vpc_has_natgw()
    
    info = {
        'nat_needed' : nat_needed
    }
    
    if gateway_list == None and nat_needed == True:
        gatewayId = create_nat_gateway()
        update_route_tables(gatewayId)
        
        info['nat-launched'] = gatewayId
    elif gateway_list != None and nat_needed == False:
        gw_change_list = []
        
        for (gatewayId, state, created) in  gateway_list:
            age = datetime.now(created.tzinfo) - created
            if age >= timedelta(minutes=45):
                ec2.delete_nat_gateway(NatGatewayId = gatewayId)
                gw_change_list.append({'action' : 'deleted', 'gatewayId' : gatewayId, 'age' : ('%s' % age)})
            else:
                gw_change_list.append({'action' : 'skipped', 'gatewayId' : gatewayId, 'age' : ('%s' % age)})
        info['nat-changed'] = gw_change_list
    
    return info

    
def request_gateway_handler(event, context):
    gateway_list = vpc_has_natgw()
    
    info = {
        'nat_needed' : 'requested'
    }
    
    if gateway_list == None: #and nat_needed == True:
        gatewayId = create_nat_gateway()
        update_route_tables(gatewayId)
        info['nat-launched'] = gatewayId
    else: 
        info['nat-existing'] = True
        
    return info
