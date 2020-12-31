# Cheapseats VPC 
## What is this?
This is a set of cloudformation templates and supporting tools that I've written primarily for myself but that I've packaged up in case others may find them useful as well. It provisions
* A set of public and private subnets for each Availability Zone
* The associated route tables for both subnets
* Lambda functions to manage an On Demand NAT gateway.
Other Cheapseats stacks that I publish will be built using this as their foundation, and may expect stack exports or resources created by this stack to be present.
## Deployment
Two methods of deployment are supported for this project.
Firstly, it can be provisioned by using `aws cloudformation package` to upload it to an S3 bucket you control with all required components.
