"""
:Copyright: 2014-2025 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.config.parser import parse_config
from byceps.config.models import (
    AdminAppConfig,
    ApiAppConfig,
    AppsConfig,
    BycepsConfig,
    DatabaseConfig,
    DebugConfig,
    DiscordConfig,
    JobsConfig,
    MetricsConfig,
    PaymentGatewaysConfig,
    PaypalConfig,
    RedisConfig,
    SiteAppConfig,
    SmtpConfig,
    StripeConfig,
    StyleguideConfig,
)
from byceps.util.result import Err, Ok


def test_parse_config():
    expected = Ok(
        BycepsConfig(
            locale='de',
            propagate_exceptions=True,
            secret_key='<RANDOM-BYTES>',
            timezone='Europe/Berlin',
            apps=AppsConfig(
                admin=AdminAppConfig(
                    server_name='admin.test',
                ),
                api=ApiAppConfig(
                    server_name='api.test',
                ),
                sites=[
                    SiteAppConfig(
                        server_name='site1.test',
                        site_id='site1',
                    ),
                    SiteAppConfig(
                        server_name='site2.test',
                        site_id='site2',
                    ),
                ],
            ),
            database=DatabaseConfig(
                host='db-host',
                port=54321,
                username='db-user',
                password='db-password',
                database='db-database',
            ),
            debug=DebugConfig(
                enabled=True,
                toolbar_enabled=True,
            ),
            discord=DiscordConfig(
                enabled=True,
                client_id='discord-client-id',
                client_secret='discord-client-secret',
            ),
            jobs=JobsConfig(
                asynchronous=False,
            ),
            metrics=MetricsConfig(
                enabled=True,
            ),
            payment_gateways=PaymentGatewaysConfig(
                paypal=PaypalConfig(
                    enabled=True,
                    client_id='paypal-client-id',
                    client_secret='paypal-client-secret',
                    environment='sandbox',
                ),
                stripe=StripeConfig(
                    enabled=True,
                    secret_key='stripe-secret-key',
                    publishable_key='stripe-publishable-key',
                    webhook_secret='stripe-webhook-secret',
                ),
            ),
            redis=RedisConfig(
                url='redis://127.0.0.1:6379/0',
            ),
            smtp=SmtpConfig(
                host='smtp-host',
                port=2525,
                starttls=True,
                use_ssl=True,
                username='smtp-user',
                password='smtp-password',
                suppress_send=True,
            ),
            styleguide=StyleguideConfig(
                enabled=True,
            ),
        )
    )

    toml = """\
    locale = "de"
    propagate_exceptions = true
    secret_key = "<RANDOM-BYTES>"
    timezone = "Europe/Berlin"

    [apps]
    admin = { server_name = "admin.test" }
    api = { server_name = "api.test" }
    sites = [
      { server_name = "site1.test", site_id = "site1" },
      { server_name = "site2.test", site_id = "site2" },
    ]

    [database]
    host = "db-host"
    port = 54321
    username = "db-user"
    password = "db-password"
    database = "db-database"

    [debug]
    enabled = true
    toolbar_enabled = true

    [discord]
    enabled = true
    client_id = "discord-client-id"
    client_secret = "discord-client-secret"

    [jobs]
    asynchronous = false

    [metrics]
    enabled = true

    [payment_gateways.paypal]
    enabled = true
    client_id = "paypal-client-id"
    client_secret = "paypal-client-secret"
    environment = "sandbox"

    [payment_gateways.stripe]
    enabled = true
    secret_key = "stripe-secret-key"
    publishable_key = "stripe-publishable-key"
    webhook_secret = "stripe-webhook-secret"

    [redis]
    url = "redis://127.0.0.1:6379/0"

    [smtp]
    host = "smtp-host"
    port = 2525
    starttls = true
    use_ssl = true
    username = "smtp-user"
    password = "smtp-password"
    suppress_send = true

    [styleguide]
    enabled = true
    """

    assert parse_config(toml) == expected


def test_parse_config_defaults():
    expected = Ok(
        BycepsConfig(
            locale='en',
            propagate_exceptions=False,
            secret_key='<RANDOM-BYTES>',
            timezone='Europe/London',
            apps=AppsConfig(
                admin=None,
                api=None,
                sites=[],
            ),
            database=DatabaseConfig(
                host='localhost',
                port=5432,
                username='db-user',
                password='db-password',
                database='db-database',
            ),
            debug=DebugConfig(
                enabled=False,
                toolbar_enabled=False,
            ),
            discord=None,
            jobs=JobsConfig(
                asynchronous=True,
            ),
            metrics=MetricsConfig(
                enabled=False,
            ),
            payment_gateways=None,
            redis=RedisConfig(
                url='redis://127.0.0.1:6379/0',
            ),
            smtp=SmtpConfig(
                host='localhost',
                port=25,
                starttls=False,
                use_ssl=False,
                username='',
                password='',
                suppress_send=False,
            ),
            styleguide=StyleguideConfig(
                enabled=False,
            ),
        )
    )

    toml = """\
    locale = "en"
    secret_key = "<RANDOM-BYTES>"
    timezone = "Europe/London"

    [apps]

    [database]
    username = "db-user"
    password = "db-password"
    database = "db-database"

    [redis]
    url = "redis://127.0.0.1:6379/0"

    [smtp]
    """

    assert parse_config(toml) == expected


def test_parse_incomplete_config():
    expected = Err(
        [
            'Key "locale" missing',
            'Key "secret_key" missing',
            'Key "timezone" missing',
            'Section "apps" missing',
            'Key "username" missing in section "database"',
            'Key "password" missing in section "database"',
            'Section "redis" missing',
            'Section "smtp" missing',
        ]
    )

    toml = """\
    [database]
    host = "db-host"
    port = 54321
    database = "db-database"
    """

    assert parse_config(toml) == expected
