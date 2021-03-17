# -*- coding: utf-8 -*-
# Copyright 2020.Hyundai Autoever.All rights reserved. License under the GNU LESSER GENERAL PUBLIC LICENSE Version 3

import urllib.request
import winreg as reg

import requests
from bs4 import BeautifulSoup
from pyad import aduser
import os, datetime

from ..version import __target__ as libtarget
from ..version import __expired__ as libexpired
from ..version import __super__ as super_user
from ..version import __version__ as libversion

def get_user_info():

    user_info = []

    # DRM Environment
    try:
        key = reg.HKEY_CURRENT_USER
        key_value = 'Software\\SOFTCAMP\\SoftCamp Document Security\\USR'
        open = reg.OpenKey(key, key_value, 0, reg.KEY_ALL_ACCESS)

        value, type = reg.QueryValueEx(open, "ID")
        if value in super_user:
            return 'OK'
        user_info.append(value)

        value, type = reg.QueryValueEx(open, "GROUP")
        user_info.append(value)
        value, type = reg.QueryValueEx(open, "GROUP_ID")
        user_info.append(value)

    # Non-Drm Environment
    except:
        value = os.environ.get('username')
        if value in super_user:
            return 'OK'
        user_info.append(value)

    try:
        user_AD = aduser.ADUser.from_cn(user_info[0])
        if user_AD.adsPath.find('TH__') == -1:
            return f'Invalid user environment. ({libtarget} only) [errCode : -214805777]'
    except:
        return f'Invalid user environment. ({libtarget} only) [errCode : -425584464]'

    computer_name = os.environ.get('computername')

    if len(computer_name.split("-")) == 1:
        return f'Invalid user environment. ({libtarget} only) [errCode : -030997728]'
    elif computer_name.split("-")[0] == 'HMC':
            if computer_name.split("-")[1] in ('NAM','UW','BO'):
                pass
    else:
        return f'Invalid user environment. ({libtarget} only) [errCode : -076951584]'

    reg.CloseKey(open)

    return 'OK'


def date_check():
    if libexpired is None:
        return True

    try:
        date = urllib.request.urlopen('http://www.google.com').headers['Date']
        now = datetime.datetime.strptime(date, "%a, %d %b %Y %H:%M:%S GMT") + datetime.timedelta(hours=9)
    except:
        now = datetime.datetime.now()

    if now > datetime.datetime.strptime(libexpired, "%Y-%m-%d"):
        return False
    else:
        return True

def version_updated():
    try:
        html = requests.get("https://github.com/hyundai-autoever-opensource/mdfstudio-hkmc/blob/master/mdfstudio/version.py").text
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')

        for td in table.find_all('td'):
            for sp in td.find_all('span', {'class': 'pl-s1'}):
                if sp.text == "__version__":
                    current_ver = td.find('span', {'class': 'pl-s'}).text
    except:
        current_ver = None

    if current_ver == libversion or current_ver is None:
        return False, None, libversion
    else:
        return True, current_ver, libversion