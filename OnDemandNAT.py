import json
import os
import boto3
import jmespath
import random

def ec2_need_natgw(ec2):
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
        
def vpc_has_natgw(ec2):
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
    
def create_nat_gateway(ec2):
    alloc_json = ec2.describe_addresses(Filters=[{'Name' : 'tag:Name', 'Values' : ['OnDemandNAT-IPAddr']}])
    allocId = jmespath.search('Addresses[0].AllocationId', alloc_json )
    
    subnet_json = ec2.describe_subnets(Filters=[{'Name' : 'tag:Public', 'Values' : ['Yes']}])
    subnet_list = jmespath.search('Subnets[*].SubnetId', subnet_json)
    subnetId = random.choice(subnet_list)
    print ('%s\n' % subnetId)
    
    # Determine Subnet + Allocation IDs
    # Create NAT Gateway
    # Add Tags to NAT Gateway
    # Update relevant route-tables.
    pass
    
def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    nat_needed = ec2_need_natgw(ec2)
    nat_available = vpc_has_natgw(ec2)
    
    if nat_available == None:   # and nat_needed = true (removed for testing)
        create_nat_gateway(ec2)
    
    return {
        'nat-needed' : nat_needed
    ,   'gateways'  : nat_available
    }
