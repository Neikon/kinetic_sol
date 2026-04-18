# networking.py
#
# Copyright 2026 neikon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
import ipaddress
import shlex
import socket


def build_status_curl_command(base_url: str | None, token: str, status_path: str):
    token = token.strip()
    if base_url is None or not token:
        return None

    url = f'{base_url}{status_path}'
    return (
        f'curl -i '
        f'-H {shlex.quote("Accept: application/json")} '
        f'-H {shlex.quote(f"Authorization: Bearer {token}")} '
        f'{shlex.quote(url)}'
    )


def build_android_base_url_subtitle(port: int, primary_url: str | None) -> str:
    urls = android_base_urls(port)
    if not urls:
        return _(
            'No LAN IPv4 address could be detected automatically. Use this PC network address with port %(port)s.'
        ) % {'port': port}

    if primary_url is None:
        primary_url = urls[0]

    if len(urls) == 1:
        return _('Use %(url)s. Android and this PC must be on the same local network.') % {
            'url': primary_url,
        }

    alternates = ', '.join(urls[1:])
    return _(
        'Use %(url)s. Android and this PC must be on the same local network. Other detected addresses: %(others)s'
    ) % {
        'url': primary_url,
        'others': alternates,
    }


def primary_android_base_url(port: int):
    addresses = candidate_ipv4_addresses()
    if not addresses:
        return None

    return f'http://{addresses[0]}:{port}'


def android_base_urls(port: int) -> list[str]:
    return [f'http://{address}:{port}' for address in candidate_ipv4_addresses()]


def candidate_ipv4_addresses() -> list[str]:
    private_candidates: list[str] = []
    other_candidates: list[str] = []

    primary_address = _detect_primary_ipv4_address()
    if primary_address is not None:
        _append_candidate_ip(primary_address, private_candidates, other_candidates)

    hostname = socket.gethostname()
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
    except OSError:
        infos = []

    for family, _socktype, _proto, _canonname, sockaddr in infos:
        if family != socket.AF_INET:
            continue

        address = sockaddr[0]
        _append_candidate_ip(address, private_candidates, other_candidates)

    return private_candidates + other_candidates


def _append_candidate_ip(address: str, private_candidates: list[str], other_candidates: list[str]):
    if not _is_candidate_lan_ipv4(address):
        return

    target = private_candidates if _is_private_lan_ipv4(address) else other_candidates
    if address not in private_candidates and address not in other_candidates:
        target.append(address)


def _detect_primary_ipv4_address():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This does not send traffic, but lets the OS reveal the preferred outbound IP.
        sock.connect(('8.8.8.8', 80))
        address = sock.getsockname()[0]
        if _is_candidate_lan_ipv4(address):
            return address
    except OSError:
        return None
    finally:
        sock.close()

    return None


def _is_candidate_lan_ipv4(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False

    return (
        isinstance(ip, ipaddress.IPv4Address)
        and not ip.is_loopback
        and not ip.is_link_local
        and not ip.is_unspecified
    )


def _is_private_lan_ipv4(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False

    return isinstance(ip, ipaddress.IPv4Address) and ip.is_private
