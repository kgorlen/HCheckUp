<!--
Markdown Guide: https://www.markdownguide.org/basic-syntax/
-->
<!--
Disable markdownlint errors:
fenced-code-language MD040
no-inline-html MD033
-->
<!-- markdownlint-disable MD040 MD033-->

# HCheckUp

Ping [healthchecks.io](https://healthchecks.io/about/) and send an email alert if the ping fails.  

## Features

- Pings a configurable [healthchecks.io](https://healthchecks.io/) endpoint.
- Sends an email alert if the ping fails.
- Uses TOML configuration file for easy setup.
- Stores SMTP credentials securely using [keyring](https://pypi.org/project/keyring/).
- Rotating log file support.
- CLI entry point: `hcheckup`

## Prerequisites

[Install python 3.12 or later version](https://www.python.org/downloads/).

Install [pipx](https://pipx.pypa.io/stable/):

```
pip install pipx
```

Install [keyring](https://pypi.org/project/keyring/):

```
pipx install keyring
```

## Install **hcheckup** FROM `.whl` package

<pre>
<code>pipx install <i>path</i>\hcheckup-<i>version</i>-py3-none-any.whl</code>
</pre>

For example:

<pre>
<code>pipx install <i>path</i>\hcheckup-1.0.0-py3-none-any.whl</code>
</pre>

## Install **hcheckup** FROM `.tar.gz` package

Alternatively, install **hcheckup** from a `.tar.gz` package file:

<pre>
<code>pipx install <i>path</i>\hcheckup-<i>version</i>.tar.gz</code>
</pre>

For example:

<pre>
<code>pipx install <i>path</i>\hcheckup-1.0.0-.tar.gz</code>
</pre>

## Configuration

1. **Create a config file:**

   Place a `hcheckup.toml` file in your user config directory (see [platformdirs](https://pypi.org/project/platformdirs/)).  
   Example (`~/.config/hcheckup/hcheckup.toml` on Linux):

   ```toml
   hc_ping_url = "https://hc-ping.com/your-uuid"
   mail_from = "your.email@gmail.com"
   mail_to = "your.email@gmail.com"

   [smtp]
   server = "smtp.gmail.com"
   port = 587
   user = "your.email@gmail.com"
   # Set password: keyring set smtp <user>
   ```

2. **Set SMTP password in keyring:**

   ```sh
   keyring set smtp your.email@gmail.com
   ```

## Usage

Run from the command line:

```sh
hcheckup
```

- On success, the script pings healthchecks.io and exits.
- On failure, it sends an email alert and logs the error.

## Logging

Logs are written to your user log directory (see
[platformdirs](https://pypi.org/project/platformdirs/)), e.g.,
`C:\Users\`*`Username`*`\AppData\Local\CamPing\Logs` on Windows.

## Requirements

- Python 3.12+
- [keyring](https://pypi.org/project/keyring/)
- [platformdirs](https://pypi.org/project/platformdirs/)
- [requests](https://pypi.org/project/requests/)

## License

GPL-3.0-or-later. See [LICENSE.txt](LICENSE.txt).

## Author

Keith Gorlen (<kgorlen@gmail.com>)
