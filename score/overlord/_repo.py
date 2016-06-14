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

import os
import subprocess
import sys
import abc
import re


class Repository:

    @staticmethod
    def is_repository(folder):
        raise NotImplemented()

    @staticmethod
    def checkout(url, folder, revision=None):
        raise NotImplemented()

    @staticmethod
    def canonical_revision(url, revision):
        raise NotImplemented()

    @staticmethod
    def latest_revision(url):
        raise NotImplemented()

    def __init__(self, folder):
        self.folder = folder

    @property
    def url(self):
        if not hasattr(self, '__url'):
            self.__url = self.read_url().rstrip('/')
        return self.__url

    @abc.abstractmethod
    def read_url(self):
        pass

    @property
    def revision(self):
        # TODO: can't cache this without implementing some of the abstract
        # functions in this class for cache invalidation
        return self.read_revision()

    @abc.abstractmethod
    def read_revision(self):
        pass

    @abc.abstractmethod
    def clear(self):
        pass

    @abc.abstractmethod
    def update(self, revision=None):
        pass


class MercurialRepository(Repository):

    @staticmethod
    def is_repository(folder):
        return os.path.isdir(os.path.join(folder, '.hg'))

    @staticmethod
    def checkout(url, folder, revision=None):
        if revision:
            subprocess.check_call(
                ['hg', 'clone', '--rev', revision, url, folder],
                stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        else:
            subprocess.check_call(
                ['hg', 'clone', url, folder],
                stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

    @staticmethod
    def canonical_revision(url, revision):
        output = str(subprocess.check_output(
            ['hg', '--debug', 'identify', '--rev', revision, url]
        ), 'UTF-8').strip()
        return output.splitlines()[-1]

    @staticmethod
    def latest_revision(url):
        output = str(subprocess.check_output(
            ['hg', '--debug', 'identify', url]), 'UTF-8').strip()
        return output.splitlines()[-1]

    def read_url(self):
        return str(subprocess.check_output(
            ['hg', 'paths', 'default'],
            cwd=self.folder), 'UTF-8').strip()

    def read_revision(self):
        output = str(subprocess.check_output(
            ['hg', '--debug', 'id'],
            cwd=self.folder), 'UTF-8').strip()
        return re.sub(r'^([0-9a-z]{40}).*$', r'\1', output.splitlines()[-1])

    def clear(self):
        hg_reset = \
            'hg st --no-status --unknown --print0 --color false | ' \
            'xargs -0 rm --force && ' \
            'hg up --clean'
        subprocess.check_call(hg_reset, cwd=self.folder, shell=True)

    def update(self, revision=None):
        command = ['hg', 'up', '--clean']
        if revision:
            command.append(revision)
        try:
            subprocess.check_call(command, cwd=self.folder)
        except subprocess.CalledProcessError:
            # did not work, maybe we need to pull first
            subprocess.check_call(['hg', 'pull'], cwd=self.folder)
            subprocess.check_call(command, cwd=self.folder)


class GitRepository(Repository):

    @staticmethod
    def is_repository(folder):
        return os.path.isdir(os.path.join(folder, '.git'))

    @staticmethod
    def checkout(url, folder, revision=None):
        subprocess.check_call(
            ['git', 'clone', url, folder],
            stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        if revision:
            subprocess.check_call(
                ['git', '--git-dir', folder, 'reset', '--hard', revision],
                stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

    @staticmethod
    def canonical_revision(url, revision):
        if re.match(r'^[0-9a-z]{40}$', revision):
            return revision
        output = str(subprocess.check_output(
            ['git', 'ls-remote', '-h', '-t', revision, url]), 'UTF-8').strip()
        return re.sub(r'^([0-9a-z]{40}).*$', r'\1', output)

    @staticmethod
    def latest_revision(url):
        output = str(subprocess.check_output(
            ['git', 'ls-remote', '-h', '-t', 'master', url]), 'UTF-8').strip()
        return re.sub(r'^([0-9a-z]).*', r'\1', output)

    def read_url(self):
        return str(subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url']), 'UTF-8').strip()

    def read_revision(self):
        raise NotImplemented()

    def clear(self, revision):
        raise NotImplemented()

    def update(self, revision=None):
        raise NotImplemented()
