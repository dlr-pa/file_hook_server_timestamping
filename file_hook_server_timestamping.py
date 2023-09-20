#!/usr/bin/env python3
# Author: Daniel Mohr
# Date: 2022-08-23, 2022-09-22, 2022-10-19, 2023-09-20
# License: BSD 3-Clause License
# pylint: disable=missing-docstring

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile


def main():
    stbranch = 'server_timestamping'
    stdin_input = ''.join(sys.stdin)
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
                    + socket.gethostname()]:
            cpi = subprocess.run(
                [precmd + cmd],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, cwd=os.path.join(tmpdir, 'repo'),
                timeout=6, check=False)
        # check branch 'server_timestamping' available
        cpi = subprocess.run(
            ['git branch --list --all | grep --quiet ' + stbranch],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=os.path.join(tmpdir, 'repo'),
            timeout=6, check=False)
        if cpi.returncode:  # server_timestamping not available
            with open('/tmp/fhst', 'a', encoding='utf-8') as fd:
                fd.write('server_timestamping not available\n')
            cmd = 'git -C ' + os.path.join(tmpdir, 'repo') + \
                ' branch --quiet ' + stbranch
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, cwd=os.path.join(tmpdir, 'repo'),
                timeout=6, check=True)
        # Unfortunately, 'git checkout' creates a working tree.
        cmd = 'git checkout ' + stbranch
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
            cmd = 'git push --set-upstream origin ' + stbranch
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
        with open('/tmp/fhst', 'a', encoding='utf-8') as fd:
            fd.write('step 13\n')


if __name__ == "__main__":
    main()
