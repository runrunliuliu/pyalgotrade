# -*- coding: utf-8 -*-
# PyAlgoTrade
#
# Copyright 2015- liuliu.tju@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""


def get_change_percentage(actual, prev):
    if actual is None or prev is None or prev == 0:
        raise Exception("Invalid values")

    diff = actual-prev
    ret = diff / float(abs(prev))
    return ret


def safe_min(left, right):
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return min(left, right)


def safe_max(left, right):
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return max(left, right)


def getStockCate(stockid):
    ret = 'NULL'
    f3 = stockid[:3]
    if f3 == '300':
        ret = 'CYB'
    if f3 == '600' or f3 == '601' or f3 == '603':
        ret = 'HUA'
    if f3 == '000':
        ret = 'SHENA'
    if f3 == '002' or f3 == '001':
        ret = 'ZXB'
    return ret


def getWinRate(keys, win, lose):
    winrate = []
    for k in keys:
        if k in lose:
            rate = win[k] / (win[k] + lose[k] + 0.000000001)
        else:
            rate = 1.0
        winrate.append(rate)
    return winrate
#
