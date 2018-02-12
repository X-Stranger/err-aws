from errbot import BotPlugin, botcmd

from libcloud.compute.types import Provider, NodeState
from libcloud.compute.providers import get_driver

import os
import logging
logging.basicConfig(level=logging.DEBUG)

class AWS(BotPlugin):

    def get_configuration_template(self):
        """ configuration entries """
        config = {
            'access_id': os.environ['AWS_ACCESS_KEY_ID'] if 'AWS_ACCESS_KEY_ID' in os.environ else None,
            'secret_key': os.environ['AWS_SECRET_ACCESS_KEY'] if 'AWS_SECRET_ACCESS_KEY' in os.environ else None,
            'region': os.environ['REGION'] if 'REGION' in os.environ else None
        }
        return config

    def _connect(self):
        """ connection to aws """
        access_id = self.config['access_id']
        secret_key = self.config['secret_key']
        region = self.config['region']

        cls = get_driver('ec2')
        driver = cls(access_id, secret_key, region=region)
        return driver

    def _find_instance_by_name(self, name):
        driver = self._connect()
        for instance in driver.list_nodes():
            if instance.name == name:
                return instance

    def _list_grids(self):
        driver = self._connect()
        grids = list()
        for net in driver.ex_list_networks():
            if 'Stack-Name' in net.extra['tags']:
                grids.append(net.extra['tags']['Stack-Name'])
        grids.sort()
        return grids

    def _list_active_grids(self):
        driver = self._connect()
        grids = dict()
        for node in driver.list_nodes():
            if node.name.endswith("mesos-master"):
                grids[node.name] = node.extra['tags']['Stack-Name']
        values = list(grids.values())
        values.sort()
        return values

    def _basic_instance_details(self, name):
        instance = self._find_instance_by_name(name)

        if instance is not None:
            details = {
                'id': instance.id,
                'status': NodeState.tostring(instance.state),
                'ip-private': instance.private_ips,
                'ip-public': instance.public_ips,
                'security_groups': instance.extra['groups'],
                'keypair': instance.extra['key_name'],
                'instance_type': instance.extra['instance_type'],
            }
        else:
            details = {'error': 'instance named {0} not found.'.format(name)}

        return details

    @botcmd
    def aws_list_grids(self, msg, args):
        ''' get list of all grids
            example:
            !aws list_grids
        '''
        grids = self._list_grids()
        sorted = ""
        for grid in grids:
            sorted += grid + "\n"
        self.send(msg.frm, sorted)

    @botcmd
    def aws_list_active_grids(self, msg, args):
        ''' get list of active grids
            example:
            !aws list_active_grids
        '''
        grids = self._list_active_grids()
        sorted = ""
        for grid in grids:
            sorted += grid + "\n"
        self.send(msg.frm, sorted)

    @botcmd
    def aws_list_inactive_grids(self, msg, args):
        ''' get list of inactive grids
            example:
            !aws list_inactive_grids
        '''
        grids_all = self._list_grids()
        grids_active = self._list_active_grids()
        grids_inactive = list(set(grids_all) - set(grids_active))
        sorted = ""
        for grid in grids_inactive:
            sorted += grid + "\n"
        self.send(msg.frm, sorted)

    @botcmd(split_args_with=' ')
    def aws_info(self, msg, args):
        ''' get details of a virtual machine
            options: name
            example:
            !aws info vm1
        '''
        vmname = args.pop(0)
        details = self._basic_instance_details(vmname)
        self.send(msg.frm, '{0}: {1}'.format(vmname, details))

    @botcmd
    def aws_reboot(self, msg, args):
        ''' reboot a virtual machine
            options: name
            example:
            !aws reboot vm1
        '''
        vm = self._find_instance_by_name(args)
        result = vm.reboot()
        response = ''
        if result:
            response = 'Successfully sent request to reboot.'
        else:
            response = 'Unable to complete request.'

        self.send(msg.frm, '{0}: {1}'.format(vm.name, response))


    @botcmd
    def aws_terminate(self, msg, args):
        ''' terminate/destroy a virtual machine
            options: name
            example:
            !aws terminate vm1
        '''
        vm = self._find_instance_by_name(args)
        result = vm.destroy()
        response = ''
        if result:
            response = 'Successfully sent request to terminate instance.'
        else:
            response = 'Unable to complete request.'

        self.send(msg.frm, '{0}: {1}'.format(vm.name, response))
