# file hook server timestamping

`file_hook_server_timestamping.py` is a
[file hook](https://docs.gitlab.com/ee/administration/file_hooks.html)
for a [GitLab](https://docs.gitlab.com/) instance.

It creates empty commit for every push to the default branch
which are signed using a gpg key.
These commits are stored in the branch `server_timestamping`.

## installation

Hint: Sometimes gpg cannot create `/var/opt/gitlab/.gnupg` due to permissions.
Workaround:

```sh
mkdir /var/opt/gitlab/.gnupg
chown git:git /var/opt/gitlab/.gnupg
```

Hint: Sometimes `/var/opt/gitlab/` is owned by root.
Workaround:

```sh
touch /var/opt/gitlab/.file_hook_server_timestamping_gpgkey.cfg
chown git:git /var/opt/gitlab/.file_hook_server_timestamping_gpgkey.cfg
```

## config

If you provide a config file `~/.file_hook_server_timestamping.cfg` this will
be used.
An example config file is given as [`example_config.cfg`](example_config.cfg).

Hint: Sometimes `/var/opt/gitlab/` is owned by root.
Workaround:

```sh
touch /var/opt/gitlab/.file_hook_server_timestamping.cfg
chown git:git /var/opt/gitlab/.file_hook_server_timestamping.cfg
```
