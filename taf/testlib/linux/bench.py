"""
@copyright Copyright (c) 2016 - 2017, Intel Corporation.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@file: bench.py

"""

import os
from collections import ChainMap
import time
import json
from contextlib import suppress
from abc import ABC, abstractmethod

from taf.testlib.linux.etcd_helper import EtcdHelper
from plugins import loggers
from testlib.linux.utils import TimerContext, create_directory, recursive_format
from utils.ab_parser import AbParser, AbAggregator  # pylint: disable=no-name-in-module

from testlib.linux.kubernetes import Kubernetes


class BenchmarkException(Exception):
    pass


class Config(object):

    _ATTRIBUTES = {
        'debug': False,               # Additional debug messages TODO: seems it's unused
        'k8s_endpoint': None,         # Kubernetes endpoint for the KubernetesBenchmark
        'etcd_endpoint': None,        # Etcd endpoint
        'docker_registry': None,      # Registry where to pull the onp_benchmark image from
        'create': None,               # Should the pods be created or not TODO: taken from the original
                                      #     Shannon implementation, but I don't see a point here
        'numpairs': 1,                # number of client-server pairs
        'perfserverfile': None,       # json file defining the server and its parameters
        'perfclientfile': None,       # json file defining the client and its parameters
        'kubeserverfile': None,       # kubernetes json file defining the server
        'kubeclientfile': None,       # kubernetes json file defining the client
        'env': None,                  # environment -- information about VMs for the vm-vm test
        'test_type': None,            # VM-2-VM or Kubernetes test
        'remote': None,               # clients on different hosts than servers
        'local': None,                # clients on the same hosts as servers
        'clean': True,                # delete everything that was created on the hosts by the
                                      #     previous tests (TODO: seems unused)
        'start_timeout': 300,         # how long to wait for entities start
        'number_of_nodes': 1,         # number of Kubernetes nodes or VMs in case of VM-2-VM
        'countdown_time': 15,         # how long to wait before the test is started
        'wait_for_results_timeout': 600,  # how long to wait for the test results
    }

    CLASS_LOGGER = loggers.ClassLogger()

    def __getattr__(self, key):
        try:
            return self._config[key]
        except KeyError:
            raise AttributeError

    def __setattr__(self, key, value=None):
        if key == '_config':
            super(Config, self).__setattr__(key, value)
        elif key in self._ATTRIBUTES:
            self._config[key] = value
        else:
            raise AttributeError

    def load(self, config):
        if not set(config).issubset(self._ATTRIBUTES):
            raise AttributeError
        self._config = ChainMap(config, self._ATTRIBUTES)

    def __init__(self, config=None):
        super().__init__()
        self._config = {}
        self.load(config)


class Test(ABC):

    PARSERS = {
        'ab': AbParser,
    }

    AGGREGATORS = {
        'ab': AbAggregator,
    }

    CLASS_LOGGER = loggers.ClassLogger()

    @abstractmethod
    def clean_up(self):
        pass

    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self._test_type = None

        self.etcd = EtcdHelper(config.etcd_endpoint)

        self.id = self.etcd.latest_id + 1
        self.CLASS_LOGGER.debug("Creating a new test id = %d", self.id)
        self.etcd.change_dir('test-{0.id}'.format(self))

        self.root_dir = 'test-{0.id}'
        create_directory(self.root_dir)

    @abstractmethod
    def _start_servers(self):
        pass

    @abstractmethod
    def _start_clients(self):
        pass

    def _start_and_wait_for_entity(self, timer, thing, start_method, key):
        with timer:
            timer.thing = thing
            start_method()
            self.CLASS_LOGGER.info("Waiting for %s", thing)
            self.etcd.wait_for_key_count(key, self.config.numpairs, self.config.start_timeout)

    def prepare(self):
        if not self.config.create:
            return

        self.etcd.rootvalue__latest = self.id
        self.etcd.rootvalue__numpairs = self.config.numpairs

        self.etcd.value__inputdata__server = json.dumps(self.config.perfserverfile)
        self.etcd.value__inputdata__client = json.dumps(self.config.perfclientfile)
        self.etcd.value__inputdata__start = "0"
        time.sleep(1)

        def log_time(context):
            self.CLASS_LOGGER.info(
                "Time to create {0.thing} was {0.delta:4.2} seconds".format(context))

        timer = TimerContext(log_time)

        self._start_and_wait_for_entity(timer, 'servers', self._start_servers,
                                        self.etcd.key__outputdata__server)
        self._start_and_wait_for_entity(timer, 'clients', self._start_clients,
                                        self.etcd.key__outputdata__state)

    def run(self):

        self.etcd.value__inputdata__starttime = int(time.time()) + self.config.countdown_time
        self.etcd.value__inputdata__start = "1"

        self.CLASS_LOGGER.info("Starting test in %d seconds", self.config.countdown_time)
        time.sleep(self.config.countdown_time)

        def log_time(context):
            self.CLASS_LOGGER.info("Test time was %d seconds", context.delta)

        with TimerContext(log_time):
            self.CLASS_LOGGER.info("Waiting for results.")
            self.etcd.wait_for_key_count(self.etcd.key__outputdata__result,
                                         self.config.numpairs,
                                         timeout=self.config.wait_for_results_timeout)

    @property
    def test_type(self):
        if self._test_type is None:
            client_file = self.etcd.value__inputdata__client
            client_file = json.loads(client_file.value)  # pylint: disable=no-member
            for test_type in self.PARSERS:
                with suppress(KeyError):
                    client_file[test_type]  # pylint: disable=W0104
                    self._test_type = test_type
                    return self._test_type
            raise BenchmarkException('Unknown test type')
        return self._test_type

    def collect(self):
        try:
            parser_type = self.PARSERS[self.test_type]
            aggregate_type = self.AGGREGATORS[self.test_type]
        except KeyError:
            raise BenchmarkException('Unknown test type')
        else:
            parser = parser_type()
            aggregator = aggregate_type()

        for a_result in self.etcd.value__outputdata__result.leaves:
            fname = "{}/raw_output_{}.txt".format(self.root_dir, os.path.basename(a_result.key))
            with open(fname, 'w') as stream:
                stream.write(a_result.value)
            aggregator += parser.parse(a_result.value)

        return aggregator


class KubernetesBenchmark(Test):
    def clean_up(self):
        if not self.config.clean:
            return

        def log_time(context):
            self.CLASS_LOGGER.debug("Cleaning took %d seconds", context.delta)

        with TimerContext(log_time):
            self.CLASS_LOGGER.info("Cleaning pods...")
            self.k8s_client.deletecollection_namespaced_pod(namespace='default')
            # TODO: timeout
            while self.k8s_client.helper.number_of_pods > 0:
                time.sleep(1)

    def __init__(self, config):
        super().__init__(config)
        self.k8s_client = Kubernetes(self.config.k8s_endpoint)
        self.clean_up()
        self.fmt_obj = {
            'etcd_ip': self.etcd.etcd_config['host'],
            'etcd_port': self.etcd.etcd_config['port'],
            'docker_registry': self.config.docker_registry,
        }

    def _start_pod(self, body):
        self.k8s_client.create_namespaced_pod(
            body=body,
            namespace='default')

    def _recursive_format(self, container):
        return recursive_format(container, self.fmt_obj)

    def _start_entity(self, entity_type, kube_file):
        for index in range(1, int(self.config.numpairs) + 1):
            self.fmt_obj['id_num'] = index
            manifest = self._recursive_format(kube_file)
            self.CLASS_LOGGER.debug("Starting %s: %s", entity_type, manifest)
            self._start_pod(manifest)
            time.sleep(0.25)

    def _start_servers(self):
        self._start_entity("server", self.config.kubeserverfile)

    def _start_clients(self):
        self._start_entity("client", self.config.kubeclientfile)
