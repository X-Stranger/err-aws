from errbot import BotPlugin, botcmd

from libcloud.compute.types import Provider, NodeState
from libcloud.compute.providers import get_driver

import logging
logging.basicConfig(level=logging.DEBUG)

class AWS(BotPlugin):

    def get_configuration_template(self):
        """ configuration entries """
        config = {
            'access_id': None,
            'secret_key': None,
            'region': None
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
