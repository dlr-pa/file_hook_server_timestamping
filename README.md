# file hook server timestamping

`file_hook_server_timestamping.py` is a
[file hook](https://docs.gitlab.com/ee/administration/file_hooks.html)
for a [GitLab](https://docs.gitlab.com/) instance.

It creates an empty commit for every push to the default branch
which are signed using a gpg key.
As default these commits are stored in the branch `server_timestamping`.
But you can define the branch in the configuration file -- see later.

## installation

Sometimes gpg cannot create `/var/opt/gitlab/.gnupg` due to permissions.
Workaround:

```sh
install --directory --group=git --owner=git --mode=700 /var/opt/gitlab/.gnupg
```

Sometimes `/var/opt/gitlab/` is owned by root and the configuration files cannot
be created due to permissions.
Workaround:

```sh
touch /var/opt/gitlab/.file_hook_server_timestamping_gpgkey.cfg
chown git:git /var/opt/gitlab/.file_hook_server_timestamping_gpgkey.cfg
chmod 640 /var/opt/gitlab/.file_hook_server_timestamping_gpgkey.cfg
```

And finally you have to install the script, e. g.:

```sh
install --group=git --owner=git --mode=700 file_hook_server_timestamping.py /opt/gitlab/embedded/service/gitlab-rails/file_hooks/file_hook_server_timestamping.py
```

On first run the script will create a gpg key. Otherwise you can do this on
your own and provide the key in the configuration file -- see next subsection.

## configuration

If you provide a configuration file `~/.file_hook_server_timestamping.cfg` this
will be used.
An example configuration file is given as
[`example_config.cfg`](example_config.cfg).

Hint: Sometimes `/var/opt/gitlab/` is owned by root.
Workaround:

```sh
touch /var/opt/gitlab/.file_hook_server_timestamping.cfg
chown git:git /var/opt/gitlab/.file_hook_server_timestamping.cfg
chmod 640 /var/opt/gitlab/.file_hook_server_timestamping.cfg
```

Or you can directly install the `example_config.cfg` and edit it afterwards:

```sh
install --group=git --owner=git --mode=640 example_config.cfg /var/opt/gitlab/.file_hook_server_timestamping.cfg
```

Typically in the configuration
`/var/opt/gitlab/.file_hook_server_timestamping_gpgkey.cfg` the gpg to use
is described. But you can also overwrite this in the configuration
`/var/opt/gitlab/.file_hook_server_timestamping.cfg`.
See example configuration for possible values and a short description.

## limitation and hints

`file_hook_server_timestamping.py` works only on a single note GitLab instance.

[GitLab UI signing commits](https://docs.gitlab.com/ee/administration/gitaly/configure_gitaly.html#configure-commit-signing-for-gitlab-ui-commits)
is not comparable. It only signs commits done by using the web interface.
