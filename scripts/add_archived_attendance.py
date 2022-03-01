#!/usr/bin/env python

"""Add the attendance of a user at a party to the archive.

:Copyright: 2014-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import click
from flask.cli import with_appcontext

from byceps.services.ticketing import attendance_service
from byceps.services.user import service as user_service

from _validators import validate_party, validate_user_id


@click.command()
@click.argument('user', callback=validate_user_id)
@click.argument('party', callback=validate_party)
@with_appcontext
def execute(user, party) -> None:
    click.echo(
        f'Adding attendance of user "{user.screen_name}" '
        f'at party "{party.title}" ... ',
        nl=False,
    )

    attendance_service.create_archived_attendance(user.id, party.id)

    click.secho('done.', fg='green')


if __name__ == '__main__':
    execute()
