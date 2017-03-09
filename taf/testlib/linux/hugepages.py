"""
@copyright Copyright (c) 2016-2017, Intel Corporation.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@file hugepages.py

@summary Class to abstract hugepages operations
"""
DEFAULT_HUGEPAGE_SIZE = 2048


class HugePages(object):

    def __init__(self, cli_send_command):
        """
        @brief Initialize Hugepages class.
        """
        super(HugePages, self).__init__()
        self.cli_send_command = cli_send_command

    def _hugepages_helper(self, kwargs):
        """
        @brief  Helper function for getting and setting hugepages
        @param kwargs: Arguments to pass
        @type kwargs: dict
        @rtype tuple(str, str, int) | CmdStatus
        @return  Returns CmdStatus namedtuple of stdout, stderr, return code
        """
        if kwargs.get('per_node') is not None:
            template = '{mode} /sys/devices/system/node/node{per_node}/hugepages/hugepages-{hugepage_size}kB/{param_name}'
        else:
            template = '{mode} /sys/kernel/mm/hugepages/hugepages-{hugepage_size}kB/{param_name}'

        command = template.format(**kwargs)
        return self.cli_send_command(command)

    def mount(self, nr_hugepages, per_node=None, mnt_dir='/mnt/huge', hugepage_size=DEFAULT_HUGEPAGE_SIZE, **kwargs):
        """
        @brief  Mount hugepages
        @param nr_hugepages: Number of hugepages
        @type nr_hugepages: int
        @param per_node: Mount per node or per system
        @type per_node: int
        @param mnt_dir: Mount dir
        @type mnt_dir: str
        @param hugepage_size: Current hugepage allocated size
        @type hugepage_size: int
        @param kwargs: Additional arguments to pass to commandline
        @type kwargs: dict
        """
        self.cli_send_command("mkdir -p {}".format(mnt_dir))
        self.change_number(nr_hugepages, per_node=per_node, hugepage_size=hugepage_size)
        cmd = ['mount', '-t', 'hugetlbfs', 'nodev', mnt_dir]
        if kwargs:
            cmd.append(' '.join('--{} {}'.format(x, y) for x, y in kwargs.items()))
        cmd = ' '.join(cmd)
        self.cli_send_command(cmd)

    def umount(self, mnt_dir='/mnt/huge', **kwargs):
        """
        @brief  Unmount hugepages
        @param mnt_dir: Dir to unmount
        @type mnt_dir: str
        @param kwargs: Additional arguments to pass to commandline
        @type kwargs: dict
        """
        cmd = ['umount', mnt_dir]
        if kwargs:
            cmd.append(' '.join('--{} {}'.format(x, y) for x, y in kwargs.items()))
        cmd = ' '.join(cmd)
        self.cli_send_command(cmd)

    def get_number(self, per_node=None, hugepage_size=DEFAULT_HUGEPAGE_SIZE):
        """
        @brief  Get number of hugepages
        @param per_node: Get number of hugepages per node or per system
        @type per_node: int
        @param hugepage_size: Current hugepage allocated size
        @type hugepage_size: int
        @rtype:  int
        @return:  Returns number of hugepages
        """
        output = self._hugepages_helper({'mode': 'cat', 'per_node': per_node, 'hugepage_size': hugepage_size,
                                         'param_name': 'nr_hugepages'}).stdout
        return int(output)

    def get_free_memory(self, per_node=None, hugepage_size=DEFAULT_HUGEPAGE_SIZE):
        """
        @brief  Get free hugepages
        @param per_node: Get number of free hugepages per node or per system
        @type per_node: int
        @param hugepage_size: Current hugepage allocated size
        @type hugepage_size: int
        @rtype:  int
        @return:  Returns number of free hugepages
        """
        output = self._hugepages_helper({'mode': 'cat', 'per_node': per_node, 'hugepage_size': hugepage_size,
                                         'param_name': 'free_hugepages'}).stdout
        return int(output)

    def change_number(self, nr_hugepages, per_node=None, hugepage_size=DEFAULT_HUGEPAGE_SIZE):
        """
        @brief  Change number of hugepages
        @param nr_hugepages: Number of hugepages
        @type nr_hugepages: int
        @param per_node: Number of hugepages per node or per system
        @type per_node: int
        @param hugepage_size: Current hugepage allocated size
        @type hugepage_size: int
        """
        self._hugepages_helper({'mode': 'echo {} >'.format(nr_hugepages), 'per_node': per_node,
                                'hugepage_size': hugepage_size, 'param_name': 'nr_hugepages'})
