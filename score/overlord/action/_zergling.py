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


from ._base import Action
import os
from .._repo import MercurialRepository, GitRepository
from score.projects import Project, ProjectNotFound
from ..zergling import Zergling
import random


phonetics = {
    "a": "alfa",
    "b": "bravo",
    "c": "charlie",
    "d": "delta",
    "e": "echo",
    "f": "foxtrot",
    "g": "golf",
    "h": "hotel",
    "i": "india",
    "j": "juliett",
    "k": "kilo",
    "l": "lima",
    "m": "mike",
    "n": "november",
    "o": "oscar",
    "p": "papa",
    "q": "quebec",
    "r": "romeo",
    "s": "sierra",
    "t": "tango",
    "u": "uniform",
    "v": "victor",
    "w": "whiskey",
    "x": "xray",
    "y": "yankee",
    "z": "zulu",
    "0": "zero",
    "1": "wun",
    "2": "too",
    "3": "tree",
    "4": "fower",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "ait",
    "9": "niner",
}


def mkname():
    words = list(phonetics.values())
    return '%s-%s' % (random.choice(words), random.choice(words))


class CreateZergling(Action):

    def __init__(self, overlord, conf):
        self.overlord = overlord
        self.conf = conf
        self.folderspec = self.conf['folder']
        self.result = None

    def __str__(self):
        return 'CreateZergling:\n%s' % self.folderspec

    def start(self):
        self.result = Zergling(self.overlord, self.allocate_project())

    def allocate_project(self):
        if os.path.isdir(self.folderspec):
            folder = self.folderspec
            name = os.path.basename(folder)
            try:
                return self.overlord.projects.get(name)
            except ProjectNotFound:
                return self.overlord.projects.create(name, folder)
        try:
            url, revision = self.folderspec.split('#', 1)
        except ValueError:
            url = self.folderspec
            revision = None
        url.rstrip('/')
        if url.startswith('hg+'):
            return self.allocate_repo_project(
                MercurialRepository, url[3:], revision)
        elif url.startswith('git+'):
            return self.allocate_repo_project(GitRepository, url[4:], revision)
        elif url.startswith('git:'):
            return self.allocate_repo_project(GitRepository, url, revision)
        else:
            raise ValueError('Could not determine how to handle %s' %
                             self.folderspec)

    def allocate_repo_project(self, repocls, url, revision):
        candidates = []
        for project in self.overlord.projects:
            if not repocls.is_repository(project.folder):
                continue
            repo = repocls(project.folder)
            if repo.url != url:
                continue
            try:
                next(z
                     for z in self.overlord.zerglings
                     if z.project.folder == repo.folder)
                continue
            except StopIteration:
                candidates.append((project, repo))
        if candidates:
            target_revision = revision
            if target_revision is None:
                target_revision = repocls.latest_revision(url)
            for project, repo in candidates:
                if repo.revision == target_revision:
                    return project
            project, repo = candidates[0]
            repo.clear()
            repo.update(revision=target_revision)
            project.install()
            return project
        else:
            # TODO: create human-recognizable folder name
            name = mkname()
            folder = os.path.join(self.overlord.rootdir, name)
            while os.path.exists(folder):
                name = mkname()
                folder = os.path.join(self.overlord.rootdir, name)
            repocls.checkout(url, folder, revision=revision)
            return self.overlord.projects.register(name, folder)


class StartZergling(Action):

    def __init__(self, zergling):
        self.zergling = zergling

    def __str__(self):
        if isinstance(self.zergling, CreateZergling):
            return 'Start zergling from\n%s' % self.zergling.folderspec
        else:
            return 'Start zergling %s' % self.zergling.name

    def start(self):
        zergling = self.zergling
        if isinstance(self.zergling, CreateZergling):
            zergling = zergling.result
            assert isinstance(zergling, Zergling)
        zergling.start()
