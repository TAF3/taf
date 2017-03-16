# Copyright (c) 2011 - 2017, Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""``pytest_heat_checker.py``

`Plugin is checking temperature`

"""

import pytest


def pytest_addoption(parser):
    """Describe plugin specified options.

    """
    group = parser.getgroup("heatchecker", "plugin heat checker")
    group.addoption("--heat_check", action="store", default='True',
                    choices=['False', 'True'],
                    help="Enable/Disable tool for temperature logging (False | True). '%default' by default.")


def pytest_configure(config):
    """Registering plugin.

    """
    if config.option.heat_check == 'True':
        config.pluginmanager.register(HeatCheckerPlugin(), "_heat_checker")


def pytest_unconfigure(config):
    """Unregistering plugin.

    """
    heat_checker = getattr(config, "_heat_checker", None)
    if heat_checker:
        del config._heat_checker
        config.pluginmanager.unregister(heat_checker)


class HeatChecker(object):
    """Base class for HeatChecker functionality.

    """

    def __init__(self, env, item):
        """Initialize HeatChecker instance.

        Args:
            env (testlib.common3.Environment): Environment instance.
            item (pytest.Item): Test case instance.

        """
        self.env = env
        self.logger = item.config.ctlogger

    def check_and_log_temperature(self):
        """Get temperature of device and log this info.

        """
        for switch in list(self.env.switch.values()):
            try:
                temp_table = switch.ui.get_temperature()
                for row in temp_table:
                    self.logger.info('[HEAT] Device %s \t %s \t %s' % (switch.name, row['type'], row['value']))
            except Exception as err:
                self.logger.info('[HEAT] Could not get information about temperature of device %s: %s' % (switch.name, err))


class HeatCheckerPlugin(object):
    """Log device's temperature.

    """

    @pytest.fixture(autouse=True)
    def heatcheck(self, request, env):
        """ Call heat checker on test case setup/teardown.

        Args:
            request (pytest.request): Pytest request instance.
            env (testlib.common3.Environment): 'env' pytest fixture from pytest_onsenv.py.

        """
        heat_checker = HeatChecker(env, request.node)
        request.addfinalizer(heat_checker.check_and_log_temperature)
        heat_checker.check_and_log_temperature()
