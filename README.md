# file hook server timestamping

`file_hook_server_timestamping.py` is a
[file hook](https://docs.gitlab.com/ee/administration/file_hooks.html)
for a [GitLab](https://docs.gitlab.com/) instance.

It creates empty commit for every push to the default branch
which are signed using a gpg key.
These commits are stored in the branch `server_timestamping`.
