# Cheapseats VPC 
## What is this?
This is a set of cloudformation templates and supporting tools that I've written primarily for myself but that I've packaged up in case others may find them useful as well. It provisions
* A set of public and private subnets for each Availability Zone
* The associated route tables for both subnets
* Lambda functions to manage an On Demand NAT gateway.
Other Cheapseats stacks that I publish will be built using this as their foundation, and may expect stack exports or resources created by this stack to be present.
__THIS CODE IS PROVIDED AS-IS, WITH NO WARRANTY OR SUPPORT COMMITMENTS. THE USER IS FULLY RESPONSIBLE FOR THE COSTS THIS MAY INCUR IN THEIR AWS ACCOUNT__
## Expected Costs
* The On Demand NAT Gateway will incur costs while it is up and operational.
* The Lambda functions to manage the NAT Gateway may incur costs if you manage to exceed the free tier for Lambda within your AWS account.
## Deployment
Two methods of deployment are supported for this project.
Firstly, it can be provisioned by using `aws cloudformation package` to upload it to an S3 bucket you control with all required components. This is the recommended approach if you do not wish to alter or customize this template to suit your own needs.
### Pipeline Deployment
If you wish to customize this template and deploy it via a build pipeline you control then here are the steps you will need to follow.
1. Fork this repository into a repository you control (CodeCommit, Github or any other provider should work just fine).
1. Deploy cf-configstack.json, ensuring that you set CreateRoles to "Yes" to ensure that the template provisions the roles for CodeBuild and Cloudformation for you.
1. Create your pipeline in CodePipeline to suit your needs.
Note that for your first run, you may need to manually provision a NAT gateway within the default VPC for Codebuild to use. Once the environ
## Using the On Demand NAT Gateway
To use the on-demand NAT gateway, simply include a Lambda call to ${VPCName}-RequestNATGateway near the start of your build pipeline. It will ensure that the NAT gateway is up and running before continuing on to perform the rest of the build steps. The gateway will remain open for 45 minutes from the last request, and 

