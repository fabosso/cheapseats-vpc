import json
import os
import boto3
import jmespath
import random

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
    gateways = jmespath.search('NatGateways[*].NatGatewayId', gateway_json)
    
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
    
    print('%s\n----ID: %s\n' % (new_gw_json, gatewayId))
    
    ec2.create_tags(Resources=[gatewayId], Tags=[{'Key' : 'OnDemandNAT', 'Value' : 'True'}, {'Key' : 'Name', 'Value' : 'OnDemandNAT-Gateway'}])
    return gatewayId
    
def update_route_tables(gatewayId):
    routes_json = ec2.describe_route_tables(Filters=[{'Name' : 'tag:OnDemandNAT', 'Values' : ['Yes', 'True']}])
    routes_list = jmespath.search('RouteTables[*].RouteTableId', routes_json)
    
    for routeTableId in routes_list:
        ec2.delete_route(RouteTableId = routeTableId, DestinationCidrBlock = '0.0.0.0/0')
        ec2.create_route(RouteTableId = routeTableId, DestinationCidrBlock = '0.0.0.0/0', NatGatewayId = gatewayId)
    print ("%s\n---\nRouteTableIDs: %s\n" % (routes_json, routes_list))
    
def lambda_handler(event, context):
    
    nat_needed = ec2_need_natgw()
    nat_available = vpc_has_natgw()
    
    if nat_available == None:   # and nat_needed = true (removed for testing)
        gatewayId = create_nat_gateway()
        update_route_tables(gatewayId)
    else:
        gatewayId = nat_available[0]
        
    update_route_tables(gatewayId)
    
    return {
        'nat-needed' : nat_needed
    ,   'gateways'  : nat_available
    }
