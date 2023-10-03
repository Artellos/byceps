"""
byceps.services.guest_server.guest_server_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select

from byceps.database import db
from byceps.events.guest_server import GuestServerRegisteredEvent
from byceps.services.orga_team import orga_team_service
from byceps.services.party.models import Party, PartyID
from byceps.services.ticketing import ticket_service
from byceps.services.user import user_service
from byceps.services.user.models.user import User, UserID
from byceps.util.result import Err, Ok, Result

from . import guest_server_domain_service
from .dbmodels import DbGuestServer, DbGuestServerAddress, DbGuestServerSetting
from .errors import QuantityLimitReachedError, UserUsesNoTicketError
from .models import (
    Address,
    AddressData,
    AddressID,
    IPAddress,
    Server,
    ServerID,
    Setting,
)


# -------------------------------------------------------------------- #
# setting


def get_setting_for_party(party_id: PartyID) -> Setting:
    """Return the setting for the party."""
    db_setting = _get_db_setting(party_id)

    if db_setting is None:
        return Setting(
            party_id=party_id,
            netmask=None,
            gateway=None,
            dns_server1=None,
            dns_server2=None,
            domain=None,
        )

    return _db_entity_to_setting(db_setting)


def update_setting(
    party: Party,
    netmask: IPAddress | None,
    gateway: IPAddress | None,
    dns_server1: IPAddress | None,
    dns_server2: IPAddress | None,
    domain: str | None,
) -> Setting:
    """Update the setting for the party."""
    db_setting = _get_db_setting(party.id) or DbGuestServerSetting(party.id)

    db_setting.netmask = netmask
    db_setting.gateway = gateway
    db_setting.dns_server1 = dns_server1
    db_setting.dns_server2 = dns_server2
    db_setting.domain = domain

    db.session.add(db_setting)
    db.session.commit()

    return _db_entity_to_setting(db_setting)


def _get_db_setting(party_id: PartyID) -> DbGuestServerSetting | None:
    return db.session.execute(
        select(DbGuestServerSetting).filter_by(party_id=party_id)
    ).scalar_one_or_none()


def _db_entity_to_setting(db_setting: DbGuestServerSetting) -> Setting:
    return Setting(
        party_id=db_setting.party_id,
        netmask=db_setting.netmask,
        gateway=db_setting.gateway,
        dns_server1=db_setting.dns_server1,
        dns_server2=db_setting.dns_server2,
        domain=db_setting.domain,
    )


# -------------------------------------------------------------------- #
# server


def ensure_user_may_register_server(
    party: Party, user: User
) -> Result[None, QuantityLimitReachedError | UserUsesNoTicketError]:
    """Return an error if the user is not allowed to register a(nother)
    guest server for a party.
    """
    user_uses_ticket_for_party = ticket_service.uses_any_ticket_for_party(
        user.id, party.id
    )

    user_is_orga_for_party = orga_team_service.is_orga_for_party(
        user.id, party.id
    )

    already_registered_server_quantity = count_servers_for_owner_and_party(
        user.id, party.id
    )

    return guest_server_domain_service.ensure_user_may_register_server(
        user_uses_ticket_for_party,
        user_is_orga_for_party,
        already_registered_server_quantity,
    )


def register_server(
    party: Party,
    creator: User,
    owner: User,
    address_data: AddressData,
    *,
    description: str | None = None,
    notes_owner: str | None = None,
    notes_admin: str | None = None,
    approved: bool = False,
) -> tuple[Server, GuestServerRegisteredEvent]:
    """Register a server for a party."""
    server, event = guest_server_domain_service.register_server(
        party,
        creator,
        owner,
        address_data,
        description=description,
        notes_owner=notes_owner,
        notes_admin=notes_admin,
        approved=approved,
    )

    _persist_server_registration(server)

    return server, event


def _persist_server_registration(server: Server) -> None:
    db_server = DbGuestServer(
        server.id,
        server.party_id,
        server.created_at,
        server.creator.id,
        server.owner.id,
        description=server.description,
        notes_owner=server.notes_owner,
        notes_admin=server.notes_admin,
        approved=server.approved,
    )
    db.session.add(db_server)

    for address in server.addresses:
        db_address = DbGuestServerAddress(
            address.id,
            server.id,
            server.created_at,
            ip_address=address.ip_address,
            hostname=address.hostname,
        )
        db.session.add(db_address)

    db.session.commit()


def update_server(
    server_id: ServerID,
    notes_admin: str | None,
    approved: bool,
) -> Server:
    """Update the server."""
    db_server = _get_db_server(server_id)

    db_server.notes_admin = notes_admin
    db_server.approved = approved

    db.session.commit()

    creator = user_service.get_user(db_server.creator_id)
    owner = user_service.get_user(db_server.owner_id)

    return _db_entity_to_server(db_server, creator, owner)


def find_server(server_id: ServerID) -> Server | None:
    """Return the server, if found."""
    db_server = _find_db_server(server_id)

    if db_server is None:
        return None

    creator = user_service.get_user(db_server.creator_id)
    owner = user_service.get_user(db_server.owner_id)

    return _db_entity_to_server(db_server, creator, owner)


def get_all_servers_for_party(party_id: PartyID) -> list[Server]:
    """Return all servers for the party."""
    db_servers = (
        db.session.scalars(
            select(DbGuestServer)
            .filter_by(party_id=party_id)
            .join(DbGuestServerAddress)
        )
        .unique()
        .all()
    )

    creator_ids = {db_server.creator_id for db_server in db_servers}
    creators_by_id = user_service.get_users_indexed_by_id(
        creator_ids, include_avatars=True
    )

    owner_ids = {db_server.owner_id for db_server in db_servers}
    owners_by_id = user_service.get_users_indexed_by_id(
        owner_ids, include_avatars=True
    )

    return [
        _db_entity_to_server(
            db_server,
            creators_by_id[db_server.creator_id],
            owners_by_id[db_server.owner_id],
        )
        for db_server in db_servers
    ]


def get_servers_for_owner_and_party(
    owner_id: UserID, party_id: PartyID
) -> list[Server]:
    """Return the servers owned by the user for the party."""
    db_servers = (
        db.session.scalars(
            select(DbGuestServer)
            .filter_by(owner_id=owner_id)
            .filter_by(party_id=party_id)
            .join(DbGuestServerAddress)
        )
        .unique()
        .all()
    )

    creator_ids = {db_server.creator_id for db_server in db_servers}
    creators_by_id = user_service.get_users_indexed_by_id(
        creator_ids, include_avatars=True
    )

    owner_ids = {db_server.owner_id for db_server in db_servers}
    owners_by_id = user_service.get_users_indexed_by_id(
        owner_ids, include_avatars=True
    )

    return [
        _db_entity_to_server(
            db_server,
            creators_by_id[db_server.creator_id],
            owners_by_id[db_server.owner_id],
        )
        for db_server in db_servers
    ]


def count_servers_for_owner_and_party(
    owner_id: UserID, party_id: PartyID
) -> int:
    """Return the number of servers owned by the user for the party."""
    return db.session.scalar(
        select(db.func.count(DbGuestServer.id))
        .filter_by(owner_id=owner_id)
        .filter_by(party_id=party_id)
    )


def delete_server(server_id: ServerID) -> None:
    """Delete a server and its addresses."""
    db.session.execute(
        delete(DbGuestServerAddress).where(
            DbGuestServerAddress.server_id == server_id
        )
    )

    db.session.execute(
        delete(DbGuestServer).where(DbGuestServer.id == server_id)
    )

    db.session.commit()


def _find_db_server(server_id: ServerID) -> DbGuestServer | None:
    return db.session.execute(
        select(DbGuestServer).filter_by(id=server_id)
    ).scalar_one_or_none()


def _get_db_server(server_id: ServerID) -> DbGuestServer:
    db_server = _find_db_server(server_id)

    if db_server is None:
        raise ValueError(f'Unknown server ID "{server_id}"')

    return db_server


def _db_entity_to_server(
    db_server: DbGuestServer, creator: User, owner: User
) -> Server:
    addresses = {
        _db_entity_to_address(db_address) for db_address in db_server.addresses
    }

    return Server(
        id=db_server.id,
        party_id=db_server.party_id,
        created_at=db_server.created_at,
        creator=creator,
        owner=owner,
        description=db_server.description,
        notes_owner=db_server.notes_owner,
        notes_admin=db_server.notes_admin,
        approved=db_server.approved,
        addresses=addresses,
    )


# -------------------------------------------------------------------- #
# address


def find_address(address_id: AddressID) -> Address | None:
    """Return the address, if found."""
    db_address = _find_db_address(address_id)

    if db_address is None:
        return None

    return _db_entity_to_address(db_address)


def create_address(
    server_id: ServerID,
    ip_address: IPAddress | None = None,
    hostname: str | None = None,
    netmask: IPAddress | None = None,
    gateway: IPAddress | None = None,
) -> Address:
    """Append an address to a server."""
    db_server = _get_db_server(server_id)

    created_at = datetime.utcnow()

    address = guest_server_domain_service._build_address(
        db_server.id,
        created_at,
        ip_address=ip_address,
        hostname=hostname,
        netmask=netmask,
        gateway=gateway,
    )

    db_address = DbGuestServerAddress(
        address.id,
        address.server_id,
        address.created_at,
        ip_address=address.ip_address,
        hostname=address.hostname,
        netmask=address.netmask,
        gateway=address.gateway,
    )
    db.session.add(db_address)

    db.session.commit()

    return _db_entity_to_address(db_address)


def update_address(
    address_id: AddressID,
    ip_address: IPAddress | None,
    hostname: str | None,
    netmask: IPAddress | None = None,
    gateway: IPAddress | None = None,
) -> Result[Address, str]:
    """Update the address."""
    db_address = _find_db_address(address_id)

    if db_address is None:
        return Err(f'Unknown address ID "{address_id}"')

    db_address.ip_address = ip_address
    db_address.hostname = hostname
    db_address.netmask = netmask
    db_address.gateway = gateway

    db.session.commit()

    address = _db_entity_to_address(db_address)

    return Ok(address)


def _find_db_address(address_id: AddressID) -> DbGuestServerAddress | None:
    return db.session.execute(
        select(DbGuestServerAddress).filter_by(id=address_id)
    ).scalar_one_or_none()


def _db_entity_to_address(db_address: DbGuestServerAddress) -> Address:
    return Address(
        id=db_address.id,
        server_id=db_address.server_id,
        created_at=db_address.created_at,
        ip_address=db_address.ip_address,
        hostname=db_address.hostname,
        netmask=db_address.netmask,
        gateway=db_address.gateway,
    )
