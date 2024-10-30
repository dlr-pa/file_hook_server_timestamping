# file hook server timestamping

## general information

This script, `file_hook_server_timestamping.py`, enables the automatic
creation of timestamped commits for a GitLab repository. Each time a push is
made to the default branch, the script creates an empty commit with a
timestamp that marks the time of the push event. This can be useful for a
number of purposes, including auditing, tracking changes to the repository,
and ensuring the integrity and authenticity of the data.

Cryptographic timestamping on the server prevents silent changes to the
history, whether by a user or otherwise. The cryptographic signature
represents the time at which the data reaches the server, and subsequent
changes to the history are not possible without the private GPG key stored
on the server. This provides an additional layer of security to ensure the
integrity and authenticity of the data.

The script uses GPG keys to sign commits, which helps to ensure the
authenticity and integrity of the timestamps. It can be easily customized
through a configuration file and can be used on a single GitLab instance.

In addition to being used in a standalone GitLab environment, this script
could also be used inside the riaf environment based on GitLab, as mentioned
in [doi.org/10.5281/zenodo.13987885](https://doi.org/10.5281/zenodo.13987885).

## introduction and overview

`file_hook_server_timestamping.py` is a
[file hook](https://docs.gitlab.com/ee/administration/file_hooks.html)
for a [GitLab](https://docs.gitlab.com/) instance. It is used to automatically
create timestamped commits for every push to the default branch of a
repository. This can be useful for a number of reasons, including:

* **tracking changes:** By creating a timestamped commit for every push,
  it is easy to see when changes were made to the repository and who made them.
* **ensuring the integrity of the data:** Timestamped commits provide an
  additional layer of security, as they make it difficult for anyone to
  silently alter the history of the repository.
* **auditing:** In certain industries, it may be necessary to keep detailed
  records of all changes to a repository. Timestamped commits can help meet
  these requirements.

The script uses GPG keys to sign commits, which adds an additional layer of
security and helps ensure the authenticity of the commits. It can be easily
customized through a configuration file, which is located at
"$HOME/.file\_hook\_server\_timestamping.cfg" by default.

To use the script, simply install it and optionally configure it with your
GPG key and other settings. The script will then run automatically on every
push to the default branch, creating a timestamped, signed commit in the
"server\_timestamping" branch.

For more information on how to install and configure the script, as well as
additional details, please see the following sections.

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

On first run the script will create a GPG key. Otherwise you can do this on
your own and provide the key in the configuration file -- see next subsection.

## configuration

If you provide a configuration file `~/.file_hook_server_timestamping.cfg` this
will be used.
An example configuration file is given as
[`example_config.cfg`](example_config.cfg).

The configuration file consists of two sections:

* **`logging`:** This section is used to configure the logger.
  It includes the following options:
    + **`name`:** The name of the logger.
    + **`filename`:** The name of the log file. If this option is not set,
                    no file logging will be done.
    + **`do_console_logging`:** Whether or not to log to the console/stdout.
    + **`log_level`:** The logging level. Possible values are
      "debug", "info", "warning", "error", and "critical".
* **`server_timestamping`:** This section is used to configure the server
  timestamping feature. It includes the following options:
    + **`branch_name`:** The name of the branch in which the server
      timestamping commits will be created.
    + **`gpgkey`:** The name of the GPG key to use for signing commits.
      If this option is not set, the script will create a new GPG key and
      store the name in another configuration file,
      `$HOME/.file_hook_server_timestamping_gpgkey.cfg`.
      However, if a value is set for this option, it will overwrite the
      configuration in the other file.

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
`/var/opt/gitlab/.file_hook_server_timestamping_gpgkey.cfg` the GPG key to use
is described. But you can also overwrite this in the configuration
`/var/opt/gitlab/.file_hook_server_timestamping.cfg`.
See example configuration [`example_config.cfg`](example_config.cfg) for
possible values and a short description.

## limitation and hints

`file_hook_server_timestamping.py` works only on a single note GitLab instance.

[GitLab UI signing commits](https://docs.gitlab.com/ee/administration/gitaly/configure_gitaly.html#configure-commit-signing-for-gitlab-ui-commits)
is not comparable. It only signs commits done by using the web interface.
