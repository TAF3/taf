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

    def mount(self, nr_hugepages, per_node=None, mnt_dir='/mnt/huge', hugepage_size=DEFAULT_HUGEPAGE_SIZE):
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
        """
        self.cli_send_command("mkdir -p {}".format(mnt_dir))
        self.change_number(nr_hugepages, per_node=per_node, hugepage_size=hugepage_size)
        self.cli_send_command("mount -t hugetlbfs nodev {}".format(mnt_dir))

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
        if per_node is not None:
            output = self.cli_send_command(
                command='cat /sys/devices/system/node/node{}/hugepages/hugepages-{}kB/nr_hugepages'.format(per_node, hugepage_size)).stdout
        else:
            output = self.cli_send_command(
                command='cat /sys/kernel/mm/hugepages/hugepages-{}kB/nr_hugepages'.format(hugepage_size)).stdout
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
        if per_node is not None:
            output = self.cli_send_command(
                command='cat /sys/devices/system/node/node{}/hugepages/hugepages-{}kB/free_hugepages'.format(per_node, hugepage_size)).stdout
        else:
            output = self.cli_send_command(
                command='cat /sys/kernel/mm/hugepages/hugepages-{}kB/free_hugepages'.format(hugepage_size)).stdout
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
        if per_node is not None:
            self.cli_send_command(
                command='echo {} > /sys/devices/system/node/node{}/hugepages/hugepages-{}kB/nr_hugepages'.format(nr_hugepages,
                                                                                                                 per_node,
                                                                                                                 hugepage_size))
        else:
            self.cli_send_command(
                command='echo {} > /sys/kernel/mm/hugepages/hugepages-{}kB/nr_hugepages'.format(nr_hugepages,
                                                                                                hugepage_size))
