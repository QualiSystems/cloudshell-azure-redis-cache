#!/usr/bin/env python
# -*- coding: utf-8 -*-
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.common.credentials import ServicePrincipalCredentials
from uuid import uuid4
"""
Tests for `CloudshellAzureCdnDeployerDriver`
"""

import unittest
from driver import CloudshellAzureCdnDeployerDriver


def mock_get_azure_attributes(context):
    azure_attributes = dict()
    azure_attributes['Azure Subscription ID'] = 'c56b164a-5995-47a2-b8ce-178b0e32534a'
    azure_attributes['Azure Client ID'] = '94520553-7db6-493a-af0f-354733db64b2'
    azure_attributes['Azure Secret'] = 'FSz64yvfyQ8gYL//yla0aYbBFmaX8ESdI/f4PNHhnTs='
    azure_attributes['Azure Tenant'] = '399d58c0-d633-4267-970a-4dce5a359079'
    azure_attributes['Region'] = 'westus'
    return azure_attributes


def resource_management_client(azure_attributes):
    credentials = ServicePrincipalCredentials(client_id=azure_attributes['Azure Client ID'],
                                              secret=azure_attributes['Azure Secret'],
                                              tenant=azure_attributes['Azure Tenant'])
    rmc = ResourceManagementClient(credentials, azure_attributes['Azure Subscription ID'])
    return rmc


def create_resource_group(context):
    azure_attributes = mock_get_azure_attributes(context)
    rmc = resource_management_client(azure_attributes)
    resource_group_params = {'location': azure_attributes['Region']}
    rmc.resource_groups.create_or_update(context.reservation.reservation_id, resource_group_params)


def delete_resource_group(context):
    azure_attributes = mock_get_azure_attributes(context)
    rmc = resource_management_client(azure_attributes)
    delete_op = rmc.resource_groups.delete(context.reservation.reservation_id)
    delete_op.wait()


def mock_context():
    global context

    class Object(object):
        pass

    context = Object()
    context.resource = Object()
    context.resource.attributes = dict()
    context.resource.attributes['Profile Name'] = uuid4()
    context.resource.attributes['Endpoint Origin Host Name'] = 'en.wikipedia.org'
    context.resource.attributes['Endpoint Origin Host Header'] = 'en.wikipedia.org'
    context.resource.attributes['Endpoint Origin Path'] = '/wiki'
    context.reservation = Object()
    context.reservation.reservation_id = '832fccde-16e4-4353-bdde-7333872b15e7'

    return context


class TestCloudshellAzureCdnDeployerDriver(unittest.TestCase):
    def setUp(self):
        self.context = mock_context()
        create_resource_group(context)

    def tearDown(self):
        delete_resource_group(context)

    def test_000_something(self):
        driver = CloudshellAzureCdnDeployerDriver(get_azure_attributes_service=mock_get_azure_attributes)
        driver.deploy(context)


if __name__ == '__main__':
    import sys

    sys.exit(unittest.main())