from datetime import datetime

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import iso8601
from models import ItemAsset
from utils import (
    HANDLE,
    api_post,
    datelong,
    get_playback,
    strftime_polyfill,
    timestamp,
)

addon = xbmcaddon.Addon()


def slideshow():
    a = xbmcgui.Dialog().input(
        heading=addon.getLocalizedString(30012), type=xbmcgui.INPUT_DATE
    )
    b = xbmcgui.Dialog().input(
        heading=addon.getLocalizedString(30013), type=xbmcgui.INPUT_DATE
    )
    if not a or not b:
        xbmcplugin.endOfDirectory(HANDLE)
        return

    a = datetime.strptime(a.replace(" ", "0"), "%d/%m/%Y")
    b = datetime.strptime(b.replace(" ", "0"), "%d/%m/%Y")
    if a > b:
        a, b = b, a

    resp = api_post(
        "/api/search/metadata",
        {
            "takenBefore": b.strftime("%Y-%m-%dT23:59:59.000Z"),
            "takenAfter": a.strftime("%Y-%m-%dT00:00:00.000Z"),
            "page": 1,
            "withExif": True,
        },
    )
    assets = [
        ItemAsset.from_api_response(i) for i in resp["assets"].get("items", [])
    ]

    playlist = xbmc.PlayList(1)
    for asset in assets:
        playlist.add(
            get_playback(asset.id, asset.type),
            xbmcgui.ListItem(
                strftime_polyfill(
                    iso8601.parse_date(asset.localDateTime),
                    datelong + " " + timestamp,
                )
            ),
            False,
        )
