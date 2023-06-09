#!/bin/bash

# Set parameters
STACK_NAME="my-flask-app-stack"
TEMPLATE_FILE="my-flask-app.yaml"
REGION='eu-west-1'

echo "Starting creation of the stack..."
# Create CloudFormation stack
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://$TEMPLATE_FILE \
  --region $REGION \

# Wait for stack to complete
echo "Waiting for stack to be created..."
aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME \
  --region $REGION
echo "Stack created!"

echo "Waiting for Flask web servers to be deployed..."
# Get public IP address of EC2 instances
INSTANCE_ID_1=$(aws cloudformation describe-stack-resources \
    --stack-name $STACK_NAME \
    --query 'StackResources[?LogicalResourceId==`EC2Instance1`].PhysicalResourceId' \
    --output text)

INSTANCE_ID_2=$(aws cloudformation describe-stack-resources \
    --stack-name $STACK_NAME \
    --query 'StackResources[?LogicalResourceId==`EC2Instance2`].PhysicalResourceId' \
    --output text)

PUBLIC_IP_1=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID_1 \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

PUBLIC_IP_2=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID_2 \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

python3 ./update_ips.py $PUBLIC_IP_1 $PUBLIC_IP_2

echo "Flask web servers deployed successfully!"
echo "The URL for the first web server is http://${PUBLIC_IP_1}:5000"
echo "The URL for the second web server is http://${PUBLIC_IP_2}:5000"
