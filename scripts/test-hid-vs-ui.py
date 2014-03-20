#!/usr/bin/env python
# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
#
# Parses all help files (.xhp) to check that hids referencing .ui are up-to-date
# From fdo#67350


import sys
import argparse
import os
import subprocess
import xml.etree.ElementTree as ET
import collections
import re
import smtplib
import email
import email.mime.text
import time
import datetime

# retrieve all hids related to .ui files
def init_hids():
    global args
    repo_dir='/var/tmp/help.git'
    if not os.path.exists(repo_dir):os.makedirs(repo_dir)
    os.chdir(repo_dir)

    if not os.path.exists(os.path.join(repo_dir,'config')):
        subprocess.call(['git','clone','--bare','git://gerrit.libreoffice.org/help',repo_dir])
    elif not args['git_static']:
        subprocess.call(['git','fetch','origin'])
    return subprocess.check_output(['git','grep','hid="[^"]*/[^"]*">','master','--'])

# retrieve .ui files list from the core
def init_core_files():
    global core_repo_dir
    core_repo_dir = args['core_repo_dir']
    if core_repo_dir is None: core_repo_dir = '/var/tmp/core.git'

    if not os.path.exists(core_repo_dir):os.makedirs(core_repo_dir)
    os.chdir(core_repo_dir)

    if not os.path.exists(os.path.join(core_repo_dir,'.git')):
        subprocess.call(['git','clone','git://gerrit.libreoffice.org/core',core_repo_dir])
    elif not args['git_static']:
        subprocess.call(['git','fetch','origin'])
    allfiles = subprocess.check_output(['git','ls-tree','--name-only','--full-name','-r','master'])
    return '\n'.join(re.findall('.*\.ui',allfiles))


if __name__ == "__main__":

    parser = argparse.ArgumentParser('hid for ui consistency parser')
    parser.add_argument('-s', '--send-to', action='append', help='email address to send the report to. Use one flag per address.', required=False)
    parser.add_argument('-g', '--git-static', action='store_true', help='to avoid contacting remote server to refresh repositories.', required=False)
    parser.add_argument('-r', '--core-repo-dir', help='enforce path to core repository when analyzing .ui files.', required=False)
    args=vars(parser.parse_args())
    
    rows = init_hids().splitlines()
    #<tree>:<relative_file>:<text>
    # handled as sets to remove duplicates (and we don't need an iterator)
    targets = collections.defaultdict(set)
    origin = collections.defaultdict(set)
    
    # fill all matching hids and their parent file
    for row in rows:
        fname, rawtext = row.split(':',2)[1:]
        hid = rawtext.split('hid="')[1].split('"')[0]
        if hid.startswith('.uno'): continue
        uifileraw, compname = hid.rsplit('/',1)
        uifile = uifileraw.split('/',1)[1] + ".ui"  # remove modules/ which exist only in install
        targets[uifile].add(compname.split(':')[0])
        origin[uifile].add(fname)  # help file(s)
    
    uifileslist = init_core_files()
    # allfiles = init_core_files()
    # uifileslist = '\n'.join(re.findall('.*\.ui',allfiles))
    errors = ''
    # search in all .ui files referenced in help
    # 2 possible errors: file not found in repo, id not found in file
    for uikey in dict.keys(targets):
        if uikey not in uifileslist: 
            if len(origin[uikey]) == 1:
                errors += '\nFrom ' + origin[uikey].pop()
            else:
                errors += '\nFrom one of ' + str(origin[uikey]).replace('set(','').replace(')','')
            errors += ', we did not found file '+ uikey+'.' 
            continue
        
        full_path = os.path.join(core_repo_dir,re.search('(.*'+uikey+')',uifileslist).group(1))
        # print full_path
        root = ET.parse(full_path).getroot()
        ids = [element.attrib['id'].split(':')[0] for element in root.findall('.//object[@id]') ]
        # print targets[uikey]
        missing_ids = [ element for element in targets[uikey] if element not in ids ]
        if missing_ids:
            if len(origin[uikey]) == 1:
                errors += '\nFrom ' + origin[uikey].pop()
            else:
                errors += '\nFrom one of ' + str(origin[uikey]).replace('set(','').replace(')','')
            errors += ', referenced items '+ str(missing_ids) + ' were not found inside '+ uikey+'.' 
        
    if not errors:
        errors = '\nall is clean\n'
   
    if args['send_to']:
        msg_from = os.path.basename(sys.argv[0]) + '@libreoffice.org'
        if isinstance(args['send_to'], basestring):
            msg_to = [args['send_to']]
        else:
            msg_to = args['send_to']
            print "send to array " + msg_to[0]
            
        server = smtplib.SMTP('localhost')
        body = '''
Hello,

Here is the report for wrong hids from help related to .ui files

'''
        body += errors
        body += '''

Best,

Your friendly LibreOffice Help-ids Checker 

Note: The bot generating this message can be found and improved here:
       https://gerrit.libreoffice.org/gitweb?p=dev-tools.git;a=blob;f=scripts/test-hid-vs-ui.py'''
        now = datetime.datetime.now()
        msg = email.mime.text.MIMEText(body, 'plain', 'UTF-8')
        msg['From'] = msg_from
        msg['To'] = msg_to[0]
        msg['Cc'] = ', '.join(msg_to[1:]) # Works only if at least 2 items in tuple
        msg['Date'] = email.utils.formatdate(time.mktime(now.timetuple()))
        msg['Subject'] = 'LibreOffice Gerrit News for python on %s' % (now.date().isoformat())
        msg['Reply-To'] = msg_to[0]
        msg['X-Mailer'] = 'LibreOfficeGerritDigestMailer 1.1'

        server.sendmail(msg_from, msg_to, str(msg))
    else:
        print errors

# vim: set et sw=4 ts=4:
