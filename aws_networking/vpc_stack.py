from aws_cdk import core
from aws_cdk import aws_ec2 as ec2
from utils import cdk_utils
import app_config


class VPCStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        prj_name = self.node.try_get_context("project_name")
        env_name = self.node.try_get_context('env')
        print(prj_name, env_name)

        """
        NOTE: An internet gateway is created by default in a VPC when you create a Public Subnet
        """
        self.vpc = ec2.Vpc(self, id=f'{prj_name}-VPC',
                           cidr='10.40.0.0/16',  # 65536 available addresses in vpc
                           max_azs=1,  # max availability zones
                           enable_dns_hostnames=True,
                           # enable public dns address, and gives EC2 auto-assign dns host names to instances
                           enable_dns_support=True,  # 0.2 dns server is used, use Amazon DNS server
                           subnet_configuration=[
                               ec2.SubnetConfiguration(
                                   name="Public",
                                   subnet_type=ec2.SubnetType.PUBLIC,  # has internet gateway associated.
                                   # resources are accessible from the internet
                                   # resources can access internet
                                   cidr_mask=24  # means a subnet mask of: 255.255.255.0 meaning there
                                   # are 251  usable IP addresses in the PUBLIC subnet
                               ),
                               ec2.SubnetConfiguration(
                                   name="Private",
                                   subnet_type=ec2.SubnetType.PRIVATE,
                                   # nat gateway attached
                                   # resource can access the internet
                                   # resources ARE NOT accessible from internet
                                   cidr_mask=24
                               ),
                               ec2.SubnetConfiguration(
                                   name="Isolated",
                                   subnet_type=ec2.SubnetType.ISOLATED,
                                   # no nat or internet gateway
                                   # no access to or from internet
                                   # databases are good candidates for ISOLATED
                                   # only other AWS resources can access
                                   # isolated resources
                                   cidr_mask=24
                               )
                           ],
                           nat_gateways=1  # always provisioned in public subnet.
                           # should be same as azs for failure
                           )

        # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
        self.vpc.add_gateway_endpoint(f"{env_name}-S3Endpoint",
                                      service=ec2.GatewayVpcEndpointAwsService.S3,
                                      # Add only to ISOLATED subnets
                                      subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED)]
                                      )

        self.bastion_sg = ec2.SecurityGroup(self, id='bastionsg',
                                            security_group_name=f'{prj_name}-cdk-bastion-sg',
                                            vpc=self.vpc,
                                            description=f'{env_name} SG for Bastion',
                                            allow_all_outbound=True)
        # add SSH inbound rule
        # self.bastion_sg.add_ingress_rule(ec2.Peer.any_ipv4(), # any machine is allowed to ssh
        #                                  ec2.Port.tcp(22),
        #                                 description='SSH Access')
        self.bastion_sg.add_ingress_rule(ec2.Peer.ipv4('73.209.223.60/32'),  # only my machine
                                         ec2.Port.tcp(22),
                                         description='SSH Access')

        # add SSH inbound rule
        # self.bastion_sg.add_ingress_rule(ec2.Peer.any_ipv4(), # any machine is allowed to ssh
        #                                  ec2.Port.tcp(8000),
        #                                 description='HTTP Access')
        self.bastion_sg.add_ingress_rule(ec2.Peer.ipv4('73.209.223.60/32'),  # only my machine
                                         ec2.Port.tcp(8000),
                                         description='HTTP Access')

        self.bastion_host = ec2.Instance(self, id=f'{env_name}-bastion-host',
                                         instance_type=ec2.InstanceType(instance_type_identifier='t2.micro'),
                                         machine_image=ec2.AmazonLinuxImage(
                                             edition=ec2.AmazonLinuxEdition.STANDARD,
                                             generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
                                             virtualization=ec2.AmazonLinuxVirt.HVM,
                                             storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
                                         ),
                                         vpc=self.vpc,
                                         key_name='pryan-spr3',  # must create the key name manually first
                                         # this is the pem private/public key
                                         vpc_subnets=ec2.SubnetSelection(
                                             # this will create the ec2 instance in one of the PUBLIC subnets of the VPC that we just defined above
                                             subnet_type=ec2.SubnetType.PUBLIC
                                         ),
                                         security_group=self.bastion_sg
                                         )

        # PRIVATE
        self.private_ec2_sg = ec2.SecurityGroup(self, id=f'{env_name}-private-ec2-sg',
                                                security_group_name=f'{prj_name}-cdk-private-sg',
                                                vpc=self.vpc,
                                                description=f'{env_name} SG for Private',
                                                allow_all_outbound=True)
        self.private_ec2_sg.add_ingress_rule(self.bastion_sg,  # only the bastion box can ssh in
                                             ec2.Port.tcp(22),
                                             description='SSH Access')

        self.private_host = ec2.Instance(self, id=f'{env_name}-private-host',
                                         instance_type=ec2.InstanceType(instance_type_identifier='t2.micro'),
                                         machine_image=ec2.AmazonLinuxImage(
                                             edition=ec2.AmazonLinuxEdition.STANDARD,
                                             generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
                                             virtualization=ec2.AmazonLinuxVirt.HVM,
                                             storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
                                         ),
                                         vpc=self.vpc,
                                         key_name='pryan-spr3',  # must create the key name manually first
                                         # this is the pem private/public key
                                         vpc_subnets=ec2.SubnetSelection(
                                             # this will create the ec2 instance in one of the PUBLIC subnets of the VPC that we just defined above
                                             subnet_type=ec2.SubnetType.PRIVATE
                                         ),
                                         security_group=self.private_ec2_sg
                                         )

        # ISOLATED
        self.isolated_ec2_sg = ec2.SecurityGroup(self, id=f'{env_name}-isolated-ec2-sg',
                                                 security_group_name=f'{prj_name}-cdk-isolated-sg',
                                                 vpc=self.vpc,
                                                 description=f'{env_name} SG for Isolated',
                                                 allow_all_outbound=True)
        self.isolated_ec2_sg.add_ingress_rule(self.bastion_sg,  # only the bastion box can ssh in
                                              ec2.Port.tcp(22),
                                              description='SSH Access')

        self.isolated_host = ec2.Instance(self, id=f'{env_name}-isolated-host',
                                          instance_type=ec2.InstanceType(instance_type_identifier='t2.micro'),
                                          machine_image=ec2.AmazonLinuxImage(
                                              edition=ec2.AmazonLinuxEdition.STANDARD,
                                              generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
                                              virtualization=ec2.AmazonLinuxVirt.HVM,
                                              storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
                                          ),
                                          vpc=self.vpc,
                                          key_name='pryan-spr3',  # must create the key name manually first
                                          # this is the pem private/public key
                                          vpc_subnets=ec2.SubnetSelection(
                                              # this will create the ec2 instance in one of the PUBLIC subnets of the VPC that we just defined above
                                              subnet_type=ec2.SubnetType.ISOLATED
                                          ),
                                          security_group=self.isolated_ec2_sg
                                          )

        cdk_utils.add_tags(self.vpc, app_config.email)
        cdk_utils.add_tags(self.bastion_host, app_config.email)
        cdk_utils.add_tags(self.bastion_sg, app_config.email)
        cdk_utils.add_tags(self.isolated_host, app_config.email)
        cdk_utils.add_tags(self.isolated_ec2_sg, app_config.email)
        cdk_utils.add_tags(self.private_host, app_config.email)
        cdk_utils.add_tags(self.private_ec2_sg, app_config.email)
