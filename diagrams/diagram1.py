from diagrams import Diagram, Cluster
from diagrams.aws.network import VPC, PublicSubnet, PrivateSubnet, ALB
# from diagrams.aws.security import InstanceConnect

with Diagram("AWS VPC Architecture"): #, show=False):
    with Cluster("us-east-1"):
        vpc = VPC("VPC")
        
        with Cluster("Public Subnets"):
            pub_subnet_1 = PublicSubnet("10.0.1.0")
            pub_subnet_2 = PublicSubnet("10.0.2.0")
        
        with Cluster("Private Subnets"):
            priv_subnet_1 = PrivateSubnet("10.0.3.0")
            priv_subnet_2 = PrivateSubnet("10.0.4.0")
        
        alb = ALB("Application Load Balancer")
        alb - pub_subnet_1
        alb - pub_subnet_2

        #instance_connect = InstanceConnect("Instance Connect Endpoint")
        #instance_connect - priv_subnet_1