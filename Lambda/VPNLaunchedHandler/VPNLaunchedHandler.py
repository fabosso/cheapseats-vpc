import json
import jmespath
import boto3

ec2 = boto3.client('ec2')

def vpn_launched(instanceid):
    print("Instance Launched: %s\n" % instanceid)
    vpn_instance = ecc.Instance(instanceid)
    
    vpn_instance.wait_until_running()
    print("Instance Running: %s\n" % instanceid)
    
    # Disable Source / Destination check to allow this box to act as an OpenVPN router.
    ec2.modify_instance_attribute(InstanceId=instanceid, SourceDestCheck={'Value': False})

def vpn_stopped(instanceid):
    print("Instance Stopped: %s\n" % instanceid)

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
