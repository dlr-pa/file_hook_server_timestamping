#!/usr/bin/env python3
# Author: Daniel Mohr
# Date: 2022-08-23, 2022-09-22, 2022-10-19, 2023-09-20, 2023-09-21
# License: BSD 3-Clause License
# pylint: disable=missing-docstring

import configparser
import hashlib
import json
import logging
import logging.handlers
import os
import re
import socket
import subprocess
import sys
import tempfile

DEFAULT_CONFIG_FILE = os.path.join(
    os.environ['HOME'], '.file_hook_server_timestamping.cfg')
DEFAULT_GPGKEY_FILE = os.path.join(
    os.environ['HOME'], '.file_hook_server_timestamping_gpgkey.cfg')


def analyse_stdin_input(log):
    stdin_input = ''.join(sys.stdin)
    log.debug('stdin_input: %s', stdin_input)
    stdin_data = json.loads(stdin_input)
    project = {}
    if stdin_data['event_name'] == 'push':
        project['id'] = stdin_data['project_id']
        project['ref'] = stdin_data['ref']
    else:
        # other event, not interesting for us
        sys.exit(0)
    project['default_branch'] = stdin_data['project']['default_branch']
    if project['ref'] != 'refs/heads/' + project['default_branch']:
        # nothing done on default branch
        sys.exit(0)
    project['path_with_namespace'] = \
        stdin_data['project']['path_with_namespace']
    return project


def check_gpg_key_available(log, config):
    if config.has_option('server_timestamping', 'gpgkey'):
        log.debug('gpg key %s can be used',
                  config['server_timestamping']['gpgkey'])
    else:
        log.info('no gpg key available, will create one')
        cmd = 'gpg --batch --quick-generate-key --passphrase "" ' + \
            '"$USER@$(hostname)" future-default default never'
        cpi = subprocess.run(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True,
            timeout=6, check=True)
        gpgkey = re.search(
            rb'revocation certificate stored as \'.*/([0-9A-Z]+).rev\'',
            cpi.stderr).group(1).decode()
        keyconfig = configparser.ConfigParser()
        keyconfig['server_timestamping'] = {'gpgkey': gpgkey}
        with open(DEFAULT_GPGKEY_FILE, 'w', encoding='utf8') as configfile:
            keyconfig.write(configfile)
        config.read(DEFAULT_GPGKEY_FILE)
        log.debug('created gpg key %s',
                  config['server_timestamping']['gpgkey'])


def do_server_timestamping(log, config):
    project = analyse_stdin_input(log)
    check_gpg_key_available(log, config)
    # repos in
    #   os.path.join(os.environ['HOME'], 'git-data', 'repositories', '@hashed')
    # /var/opt/gitlab/git-data/repositories/@hashed/
    # we need the hash of project['path_with_namespace']
    # https://docs.gitlab.com/ee/administration/repository_storage_types.html
    dohash = hashlib.sha256()
    dohash.update(str(project['id']).encode())
    gitlabhash = dohash.hexdigest()
    repopath = os.path.join(
        os.environ['HOME'],
        'git-data', 'repositories', '@hashed',
        gitlabhash[0:2], gitlabhash[2:4], gitlabhash + '.git')
    # now we should have everything and we can do the job:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Unfortunately, since we do not know how many commits were done,
        # we have to get the full history.
        # Maybe we should use a better tmpdir to allow hardlinking (--local).
        # Further, we can skip the working tree (--no-checkout).
        subprocess.run(
            ['git clone --no-checkout ' + repopath + ' repo'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=tmpdir,
            timeout=6, check=True)
        # prepare git environment
        # git -C tmpdir config user.name os.environ['USER']
        precmd = 'git -C ' + os.path.join(tmpdir, 'repo') + ' config '
        for cmd in ['user.name ' + os.environ.get('USER', 'filehook'),
                    'user.email ' + os.environ.get('USER', 'filehook') + '@'
                    + socket.gethostname(),
                    'user.signingkey ' +
                    config['server_timestamping']['gpgkey'],
                    'commit.gpgSign 1']:
            cpi = subprocess.run(
                [precmd + cmd],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, cwd=os.path.join(tmpdir, 'repo'),
                timeout=6, check=False)
        # check branch 'server_timestamping' available
        cmd = 'git branch --list --all | grep --quiet ' + \
            config['server_timestamping']['branch_name']
        cpi = subprocess.run(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=os.path.join(tmpdir, 'repo'),
            timeout=6, check=False)
        if cpi.returncode:  # server_timestamping not available
            log.debug('branch server_timestamping not available')
            cmd = 'git -C ' + os.path.join(tmpdir, 'repo') + \
                ' branch --quiet ' + \
                config['server_timestamping']['branch_name']
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, cwd=os.path.join(tmpdir, 'repo'),
                timeout=6, check=True)
        # Unfortunately, 'git checkout' creates a working tree.
        cmd = 'git checkout ' + config['server_timestamping']['branch_name']
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=os.path.join(tmpdir, 'repo'),
            timeout=6, check=False)
        cmd = 'git branch --list --all'
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=os.path.join(tmpdir, 'repo'),
            timeout=6, check=False)
        cmd = 'git merge --no-commit --quiet remotes/origin/HEAD'
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=os.path.join(tmpdir, 'repo'),
            timeout=6, check=True)
        cmd = 'git commit --allow-empty -m "signing commit"'
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=os.path.join(tmpdir, 'repo'),
            timeout=6, check=True)
        if cpi.returncode:  # server_timestamping was not available
            cmd = 'git push --set-upstream origin ' + \
                config['server_timestamping']['branch_name']
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, cwd=os.path.join(tmpdir, 'repo'),
                timeout=6, check=True)
        else:
            cmd = 'git push'
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, cwd=os.path.join(tmpdir, 'repo'),
                timeout=6, check=True)
        log.debug('finished file_hook_server_timestamping.py')


def call_server_timestamping():
    config = configparser.ConfigParser()
    config['logging'] = {'name': 'server_timestamping',
                         'do_console_logging': 'no',
                         'log_level': 'info'}
    config['server_timestamping'] = {'branch_name': 'server_timestamping'}
    config.read([DEFAULT_GPGKEY_FILE, DEFAULT_CONFIG_FILE])
    log = logging.getLogger(config['logging']['name'])
    if config['logging'].getboolean('do_console_logging'):
        consolehandler = logging.StreamHandler()  # create console handler
        consolehandler.setFormatter(
            logging.Formatter(
                '%(asctime)s %(name)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S %Z'))
        log.addHandler(consolehandler)
    loglevels = {'debug': logging.DEBUG, 'info': logging.INFO,
                 'warning': logging.WARNING, 'error': logging.ERROR,
                 'critical': logging.CRITICAL}
    if config['logging']['log_level'] in loglevels:
        log.setLevel(loglevels[config['logging']['log_level']])
    else:
        log.setLevel(logging.DEBUG)
    if config.has_option('logging', 'filename'):
        fhandler = logging.handlers.WatchedFileHandler(
            config['logging']['filename'])
        fhandler.setFormatter(
            logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s',
                              datefmt='%Y-%m-%dT%H:%M:%S_%Z'))
        log.addHandler(fhandler)
    log.info('start file_hook_server_timestamping.py')
    if os.path.exists(DEFAULT_CONFIG_FILE):
        log.info('config file "%s" read', DEFAULT_CONFIG_FILE)
    do_server_timestamping(log, config)
    if config['logging'].getboolean('do_console_logging'):
        consolehandler.flush()
    if config.has_option('logging', 'filename'):
        fhandler.flush()
    # exit
    sys.exit(0)


if __name__ == "__main__":
    call_server_timestamping()
