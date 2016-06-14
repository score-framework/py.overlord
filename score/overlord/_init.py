# Copyright © 2016 STRG.AT GmbH, Vienna, Austria
#
# This file is part of the The SCORE Framework.
#
# The SCORE Framework and all its parts are free software: you can redistribute
# them and/or modify them under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation which is in the
# file named COPYING.LESSER.txt.
#
# The SCORE Framework and all its parts are distributed without any WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. For more details see the GNU Lesser General Public
# License.
#
# If you have not received a copy of the GNU Lesser General Public License see
# http://www.gnu.org/licenses/.
#
# The License-Agreement realised between you as Licensee and STRG.AT GmbH as
# Licenser including the issue of its valid conclusion and its pre- and
# post-contractual effects is governed by the laws of Austria. Any disputes
# concerning this License-Agreement including the issue of its valid conclusion
# and its pre- and post-contractual effects are exclusively decided by the
# competent court, in whose district STRG.AT GmbH has its registered seat, at
# the discretion of STRG.AT GmbH also the competent court, in whose district the
# Licensee has his registered seat, an establishment or assets.

from score.init import (
    ConfiguredModule, InitializationError, parse_bool, parse_config_file)
from .action import (
    CreateZergling, StartZergling, ParallellActions, ActionSequence)
import os
import logging
from score.cli.conf import rootdir as confroot

log = logging.getLogger('score.overlord')


defaults = {
    'conf': None,
    'rootdir': None,
    'name': None,
}


def init(confdict, projects):
    conf = defaults.copy()
    conf.update(confdict)
    if not conf['name']:
        import score.overlord
        raise InitializationError(
            score.overlord, 'No unique name specified')
    if conf['conf'] and not os.path.exists(conf['conf']):
        import score.overlord
        raise InitializationError(
            score.overlord, 'Config file does not exist:\n%s' % conf['conf'])
    rootdir = conf['rootdir']
    if not rootdir:
        rootdir = os.path.join(confroot(), 'overlord')
    if not os.path.exists(rootdir):
        os.makedirs(rootdir)
    elif not os.path.isdir(rootdir):
        import score.overlord
        raise InitializationError(
            score.overlord, 'Configured rootdir is not a folder: ' % rootdir)
    return ConfiguredOverlordModule(
        conf['name'], conf['conf'], rootdir, projects)


class ConfiguredOverlordModule(ConfiguredModule):

    def __init__(self, name, file, rootdir, projects):
        import score.overlord
        super().__init__(score.overlord)
        self.name = name
        self.file = file
        self.rootdir = rootdir
        self.projects = projects
        self.zerglings = []

    def start(self, file=None):
        actions = []
        startups = []
        for name, conf in self._readconf(file).items():
            creation = CreateZergling(self, conf)
            startup = StartZergling(creation)
            actions.append(creation)
            startups.append(startup)
        actions.append(ParallellActions(startups))
        action = ActionSequence(actions)
        action.start()

    def _readconf(self, file):
        if not file:
            if not self.file:
                raise ValueError('No zergling configuration provided')
            file = self.file
        result = {}
        defaults = {'pause': True}
        confdict = parse_config_file(self.file)
        for section in confdict:
            if section in ['DEFAULT', 'score.init']:
                continue
            result[section] = defaults.copy()
            result[section].update(confdict[section])
            result[section]['name'] = section
            result[section]['pause'] = parse_bool(result[section]['pause'])
        return result
