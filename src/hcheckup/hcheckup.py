"""
hcheckup.py -- Check Blue Iris security camera status and ping healthchecks.io with results

Created on February 11, 2025

References:
    https://healthchecks.io/about/
    https://toml.io/en/ -- TOML: A config file format for humans


"""

__author__ = "Keith Gorlen"

import sys
from datetime import datetime
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import tomllib
import smtplib
from typing import Any, NoReturn
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SCRIPT_DIR: Path = Path(__file__).absolute().parent
"""Path to directory containing this Python script."""
sys.path.append(str(SCRIPT_DIR))
"""Allow hcheckup CLI to import modules from script directory."""

# pylint: disable=wrong-import-position
from __init__ import __version__  # pylint: disable=no-name-in-module
import keyring
from platformdirs import user_config_dir, user_data_dir, user_log_dir
import requests  # type: ignore

# pylint: enable=wrong-import-position


# Global Constants


SCRIPT_NAME: str = Path(__file__).stem
"""Name of this script without .py extension."""
DATE_FMT: str = "%Y-%m-%d %H:%M:%S"
"""Format for dates in messages."""

# Global Variables

logging.basicConfig(
    handlers=[],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(SCRIPT_NAME)
"""Logging facility."""
hcheckup_log: Path = (
    Path(user_log_dir("hcheckup", appauthor=False, ensure_exists=True)) / "hcheckup.log"
)
"""hcheckup log file."""
rotating_handler = RotatingFileHandler(hcheckup_log, maxBytes=5 * 1024 * 1024, backupCount=3)
"""Rotating log file handler."""
rotating_handler.setLevel(logging.INFO)
rotating_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
        datefmt=DATE_FMT,  # Custom date format
    )
)
logging.getLogger().addHandler(rotating_handler)

hc_ping_url: str = ""
"""healthchecks.io URL"""


def exit_with_status(status: int) -> NoReturn:
    """Exit with status.

    Args:
        status (int): exit status
    """
    logger.info(f'{"=" * 60}')
    logging.shutdown()
    sys.exit(status)


def ping(url: str, msg: str = "") -> None:
    """Ping healthchecks.io.

    Args:
        url (str): healthchecks.io URL
        msg (str): message to log (default: "")

    Raises:
        requests.RequestException: If the request fails or returns a bad status code.
        requests.exceptions.Timeout: If the request times out after retries.

    """
    logger.info(f'Sending ping to {url} data="{msg}" ...')
    timeouts = (5, 10, 15)
    for i, timeout in enumerate(timeouts, 1):
        try:
            response = requests.post(url, timeout=timeout, data=msg)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx, 5xx)
            logger.info(f"Ping to {url} successful.")
            return
        except requests.exceptions.Timeout:
            msg = (f"Ping to {url} timed out after {timeout}s"
                   + ("." if i == len(timeouts) else ", retrying ..."))
            logger.info(msg)
    raise requests.exceptions.Timeout(f"Ping to {url} timed out after {len(timeouts)} attempts")


def send_mail(
    subject: str, body: str, mail_to: str, mail_from: str, smtp_config: dict[str, Any]
) -> None:
    """Send email message.

    Args:
        subject (str): Email Subject:
        mail_to (str): Email To: address
        mail_from (str): Email From: address
        smtp_config (dict[str, Any]): SMTP server configuration
    """
    logger.info(f'Sending email to "{mail_to}" ...')
    msg: MIMEMultipart = MIMEMultipart()
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as smtp:
        smtp.starttls()
        smtp.login(smtp_config["user"] or mail_from, smtp_config["password"])
        smtp.sendmail(mail_from, mail_to, msg.as_string())

    logger.info(f'Email sent to "{mail_to}".')


def main() -> None:
    """Ping healthchecks.io and send email on failure.

    Raises:
        FileNotFoundError: Configuration file not found
        ValueError: Error reading configuration file.
        KeyError: Key not found in configuration .toml file.
        ValueError: User password not found in keyring.
    """
    global hc_ping_url  # pylint: disable=global-statement

    logger.info(f'{"=" * 60}')
    logger.info(f"{SCRIPT_NAME} version {__version__} starting ...")

    config_dir: Path = Path(user_config_dir("hcheckup", appauthor=False, roaming=True))
    """Configuration directory"""
    config_file: Path = config_dir / "hcheckup.toml"
    """User-specific configuration file."""
    config_data: dict[str, Any]
    """Data from hcheckup.toml file."""
    alert_sent_file: Path = (
        Path(user_data_dir("hcheckup", appauthor=False, ensure_exists=True)) / "alert_sent"
    )
    """File exists if alert email sent."""

    if not config_file.exists():
        raise FileNotFoundError(f'Configuration file not found: "{config_file}"')

    try:
        with config_file.open("rb") as f:
            config_data = tomllib.load(f)
    except Exception as e:
        raise ValueError(
            f"Error reading configuration file {
                            config_file}: {e}"
        ) from e

    logger.info(f'Configuration loaded from "{config_file}".')

    if "hc_ping_url" in config_data:
        hc_ping_url = config_data["hc_ping_url"]
        """healthchecks.io URL for Blue Iris."""

    for key in ["hc_ping_url", "mail_from", "mail_to", "smtp"]:
        if key not in config_data:
            raise KeyError(f'"{key}" not found in {config_file}')

    smtp_config: dict[str, Any] = config_data["smtp"]
    for key in ["server", "port", "user"]:
        if key not in smtp_config:
            raise KeyError(f'"{key}" not found in {config_file}')

    # Get password from keyring
    password: str | None = keyring.get_password("smtp", smtp_config["user"])
    if not password:
        raise ValueError(f"No SMTP password found in keyring for user {smtp_config["user"]}")
    smtp_config["password"] = password

    try:
        ping(hc_ping_url)
        # Ping successful: remove alert flag file if it exists
        if alert_sent_file.exists():
            alert_sent_file.unlink()
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Failed to ping {hc_ping_url}: {e}")
        if alert_sent_file.exists():
            logger.info("Alert email already sent, skipping.")
            raise

        send_mail(
            "healthchecks.io ping failure",
            f"Ping to {hc_ping_url} failed:\n"
            f'"{e}"\n\n'
            f"Email via {smtp_config["server"]} OK; expect false alerts.",
            config_data["mail_to"],
            config_data["mail_from"],
            smtp_config,
        )
        alert_sent_file.touch()  # Create zero-length file to indicate alert sent
        raise

    exit_with_status(0)


def cli() -> None:
    """Command line interface for hcheckup."""
    try:
        main()
    except Exception as e:  # pylint: disable=broad-exception-caught
        """Log a CRITICAL message and sys.exit(1)."""
        print(
            f"{datetime.now().strftime(DATE_FMT)} - CRITICAL - {e}; exiting.",
            file=sys.stderr,
        )
        logger.critical(f"{e}; exiting.")
        exit_with_status(1)


if __name__ == "__main__":
    cli()
