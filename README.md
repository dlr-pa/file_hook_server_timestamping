# file hook server timestamping

`file_hook_server_timestamping.py` is a
[file hook](https://docs.gitlab.com/ee/administration/file_hooks.html)
for a [GitLab](https://docs.gitlab.com/) instance.

It creates empty commit for every push to the default branch
which are signed using a gpg key.
These commits are stored in the branch `server_timestamping`.

## config

If you provide a config file `~/.file_hook_server_timestamping.cfg` this will
be used.
An example config file is given as [`example_config.cfg`](example_config.cfg).
