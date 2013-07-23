#
# Copyright 2013 Red Hat, Inc.
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#
import neterrors

from testrunner import (VdsmTestCase as TestCaseBase,
                        expandPermutations, permutations)
from testValidation import RequireDummyMod, ValidateRunningAsRoot

from utils import cleanupNet, dummyIf, restoreNetConfig, SUCCESS, VdsProxy


NETWORK_NAME = 'test-network'
VLAN_ID = '27'
BONDING_NAME = 'bond0'


def setupModule():
    """Persists network configuration."""
    vdsm = VdsProxy()
    vdsm.save_config()


def tearDownModule():
    """Restores the network configuration previous to running tests."""
    restoreNetConfig()


@expandPermutations
class NetworkTest(TestCaseBase):

    def setUp(self):
        self.vdsm_net = VdsProxy()

    @cleanupNet
    @permutations([[True], [False]])
    @RequireDummyMod
    @ValidateRunningAsRoot
    def testSetupNetworksAddBondWithManyVlans(self, bridged):
        VLAN_COUNT = 5
        network_names = [NETWORK_NAME + str(tag) for tag in range(VLAN_COUNT)]
        with dummyIf(2) as nics:
            networks = dict((vlan_net,
                             {'vlan': str(tag), 'bonding': BONDING_NAME,
                              'bridged': bridged})
                            for tag, vlan_net in enumerate(network_names))
            bondings = {BONDING_NAME: {'nics': nics}}

            with self.vdsm_net.pinger():
                status, msg = self.vdsm_net.setupNetworks(networks, bondings,
                                                          {})
            self.assertEqual(status, SUCCESS, msg)
            for vlan_net in network_names:
                self.assertTrue(self.vdsm_net.networkExists(vlan_net, bridged))
                self.assertTrue(self.vdsm_net.bondExists(BONDING_NAME, nics))
                self.assertTrue(self.vdsm_net.vlanExists(BONDING_NAME + '.' +
                                networks[vlan_net]['vlan']))

            with self.vdsm_net.pinger():
                for vlan_net in network_names:
                    status, msg = self.vdsm_net.setupNetworks(
                        {vlan_net: {'remove': True}}, {}, {})
                    self.assertEqual(status, SUCCESS, msg)
                    self.assertFalse(self.vdsm_net.networkExists(vlan_net,
                                                                 bridged))
                    self.assertFalse(
                        self.vdsm_net.vlanExists(BONDING_NAME + '.' +
                                                 networks[vlan_net]['vlan']))

    @cleanupNet
    @permutations([[True], [False]])
    @RequireDummyMod
    @ValidateRunningAsRoot
    def testSetupNetworksAddDelBondedNetwork(self, bridged):
        with dummyIf(2) as nics:
            with self.vdsm_net.pinger():
                status, msg = self.vdsm_net.setupNetworks(
                    {NETWORK_NAME:
                        {'bonding': BONDING_NAME, 'bridged': bridged}},
                    {BONDING_NAME: {'nics': nics, 'options': 'mode=2'}}, {})
            self.assertEqual(status, SUCCESS, msg)
            self.assertTrue(self.vdsm_net.networkExists(NETWORK_NAME, bridged))
            self.assertTrue(self.vdsm_net.bondExists(BONDING_NAME, nics))

            with self.vdsm_net.pinger():
                status, msg = self.vdsm_net.setupNetworks(
                    {NETWORK_NAME: {'remove': True}}, {}, {})
            self.assertEqual(status, SUCCESS, msg)
            self.assertFalse(self.vdsm_net.networkExists(NETWORK_NAME))

    @cleanupNet
    @permutations([[True], [False]])
    @RequireDummyMod
    @ValidateRunningAsRoot
    def testSetupNetworksAddOverExistingBond(self, bridged=True):
        with dummyIf(2) as nics:
            status, msg = self.vdsm_net.setupNetworks(
                {}, {BONDING_NAME: {'nics': nics}},
                {'connectivityCheck': False})
            self.assertEqual(status, SUCCESS, msg)
            self.assertTrue(self.vdsm_net.bondExists(BONDING_NAME, nics))

            status, msg = self.vdsm_net.setupNetworks(
                {NETWORK_NAME:
                    {'bonding': BONDING_NAME, 'bridged': bridged,
                     'vlan': VLAN_ID}},
                {}, {'connectivityCheck': False})
            self.assertEqual(status, SUCCESS, msg)
            self.assertTrue(self.vdsm_net.networkExists(NETWORK_NAME, bridged))

            status, msg = self.vdsm_net.setupNetworks(
                {NETWORK_NAME: {'remove': True}},
                {}, {'connectivityCheck': False})
            self.assertEqual(status, SUCCESS, msg)
            self.assertTrue(self.vdsm_net.bondExists(BONDING_NAME, nics))

            status, msg = self.vdsm_net.setupNetworks(
                {},
                {BONDING_NAME: {'remove': True}}, {'connectivityCheck': False})
            self.assertEqual(status, SUCCESS, msg)

    @cleanupNet
    @permutations([[True], [False]])
    @RequireDummyMod
    @ValidateRunningAsRoot
    def testAddDelBondedNetwork(self, bridged):
        with dummyIf(2) as nics:
            status, msg = self.vdsm_net.addNetwork(NETWORK_NAME,
                                                   bond=BONDING_NAME,
                                                   nics=nics,
                                                   opts={'bridged': bridged})
            self.assertEqual(status, SUCCESS, msg)

            self.assertTrue(self.vdsm_net.networkExists(NETWORK_NAME, bridged))
            self.assertTrue(self.vdsm_net.bondExists(BONDING_NAME, nics))

            status, msg = self.vdsm_net.delNetwork(NETWORK_NAME)
            self.assertEqual(status, SUCCESS, msg)
            self.assertFalse(self.vdsm_net.networkExists(NETWORK_NAME))

    @cleanupNet
    @permutations([[True], [False]])
    @RequireDummyMod
    @ValidateRunningAsRoot
    def testAddDelNetwork(self, bridged):
        with dummyIf(1) as nics:
            status, msg = self.vdsm_net.addNetwork(NETWORK_NAME,
                                                   nics=nics,
                                                   opts={'bridged': bridged})
            self.assertEqual(status, SUCCESS, msg)
            self.assertTrue(self.vdsm_net.networkExists(NETWORK_NAME))

            status, msg = self.vdsm_net.delNetwork(NETWORK_NAME,
                                                   nics=nics,
                                                   opts={'bridged': bridged})
            self.assertEqual(status, SUCCESS, msg)
            self.assertFalse(self.vdsm_net.networkExists(NETWORK_NAME))

    @permutations([[True], [False]])
    @RequireDummyMod
    @ValidateRunningAsRoot
    def testFailWithInvalidBondingName(self, bridged):
        with dummyIf(1) as nics:
            invalid_bond_names = ('bond', 'bonda', 'bond0a', 'jamesbond007')
            for bond_name in invalid_bond_names:
                status, msg = self.vdsm_net.addNetwork(NETWORK_NAME,
                                                       bond=bond_name,
                                                       nics=nics,
                                                       opts={'bridged':
                                                             bridged})
                self.assertEqual(status, neterrors.ERR_BAD_BONDING, msg)

    def testFailWithInvalidBridgeName(self):
        invalid_bridge_names = ('a' * 16, 'a b', 'a\tb', 'a.b', 'a:b')
        for bridge_name in invalid_bridge_names:
            status, msg = self.vdsm_net.addNetwork(bridge_name)
            self.assertEqual(status, neterrors.ERR_BAD_BRIDGE, msg)

    def testFailWithInvalidIpConfig(self):
        invalid_ip_configs = (dict(IPADDR='1.2.3.4'), dict(NETMASK='1.2.3.4'),
                              dict(GATEWAY='1.2.3.4'),
                              dict(IPADDR='1.2.3', NETMASK='255.255.0.0'),
                              dict(IPADDR='1.2.3.256', NETMASK='255.255.0.0'),
                              dict(IPADDR='1.2.3.4', NETMASK='256.255.0.0'),
                              dict(IPADDR='1.2.3.4.5', NETMASK='255.255.0.0'),
                              dict(IPADDR='1.2.3.4', NETMASK='255.255.0.0',
                                   GATEWAY='1.2.3.256'),
                              )
        for ipconfig in invalid_ip_configs:
            status, msg = self.vdsm_net.addNetwork(NETWORK_NAME,
                                                   opts=ipconfig)
            self.assertEqual(status, neterrors.ERR_BAD_ADDR, msg)

    @permutations([[True], [False]])
    def testFailWithInvalidNic(self, bridged):
        status, msg = self.vdsm_net.addNetwork(NETWORK_NAME,
                                               nics=['nowaythisnicexists'],
                                               opts={'bridged': bridged})

        self.assertEqual(status, neterrors.ERR_BAD_NIC, msg)

    @permutations([[True], [False]])
    def testFailWithInvalidParams(self, bridged):
        status, msg = self.vdsm_net.addNetwork(NETWORK_NAME, VLAN_ID,
                                               opts={'bridged': bridged})
        self.assertEqual(status, neterrors.ERR_BAD_PARAMS, msg)

        status, msg = self.vdsm_net.addNetwork(NETWORK_NAME,
                                               bond=BONDING_NAME,
                                               opts={'bridged': bridged})
        self.assertEqual(status, neterrors.ERR_BAD_PARAMS, msg)

    @RequireDummyMod
    @ValidateRunningAsRoot
    def testQosNetwork(self):
        with dummyIf(1) as nics:
            qos = {'qosInbound': {'average': '1024', 'burst': '2048',
                                  'peak': '42'},
                   'qosOutbound': {'average': '2400', 'burst': '2048',
                                   'peak': '100'}}

            status, msg = self.vdsm_net.addNetwork(NETWORK_NAME,
                                                   nics=nics,
                                                   opts=qos)
            self.assertEqual(status, SUCCESS, msg)

            networkQos = self.vdsm_net.networkQos(NETWORK_NAME)
            self.assertEqual(qos['qosInbound'], networkQos.inbound)
            self.assertEqual(qos['qosOutbound'], networkQos.outbound)
