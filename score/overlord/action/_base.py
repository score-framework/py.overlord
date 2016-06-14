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


import abc
import math
from concurrent.futures import ThreadPoolExecutor


class Action(abc.ABC):

    @abc.abstractmethod
    def start(self):
        pass

    def __call__(self):
        self.start()

    def ascii_graph(self):
        lines = self.__str__().splitlines()
        width = max(map(len, lines))
        format_ = '{:<%d}' % width
        lines = map(format_.format, lines)
        border = '+' + ('-' * (2 + width)) + '+'
        return border + '\n| ' + ' |\n| '.join(lines) + ' |\n' + border


class ActionSequence(Action):

    def __init__(self, actions):
        self.actions = actions

    def start(self):
        for action in self.actions:
            action.start()

    def ascii_graph(self):
        actions_lines = []
        height = 0
        for action in self.actions:
            actions_lines.append(action.ascii_graph().splitlines())
            height = max(height, len(actions_lines[-1]))
        for lines in actions_lines:
            append = True
            while len(lines) < height:
                if append:
                    lines.append(' ' * len(lines[0]))
                else:
                    lines.insert(0, ' ' * len(lines[0]))
                append = not append
        arrow_line = math.ceil(height / 2)
        result_lines = []
        for i in range(height):
            lines = [lines[i] for lines in actions_lines]
            if i == arrow_line - 1:
                result_lines.append(' -> '.join(lines))
            else:
                result_lines.append('    '.join(lines))
        return '\n'.join(result_lines)


class ParallellActions(Action):

    def __init__(self, actions):
        self.actions = actions

    def start(self):
        with ThreadPoolExecutor(max_workers=len(self.actions)) as executor:
            for action in self.actions:
                executor.submit(action)

    def ascii_graph(self):
        if len(self.actions) == 1:
            return self.actions[0].ascii_graph()
        actions_lines = []
        width = 0
        for action in self.actions:
            actions_lines.append(action.ascii_graph().splitlines())
            width = max(width, len(actions_lines[-1][0]))
        format_ = '{:<%d}' % width
        border = '+' + ('-' * (2 + width)) + '+'
        result_lines = [border]
        for lines in actions_lines:
            for line in lines:
                result_lines.append('| ' + format_.format(line) + ' |')
            result_lines.append(border)
        return '\n'.join(result_lines)
