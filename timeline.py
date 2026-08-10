import sys
from datetime import timedelta

import xbmcgui
import xbmcplugin

import iso8601
from models import ItemAsset, TimeBucket, TimelineBucket
from utils import (
    api_get,
    datelong,
    get_asset_name,
    get_playback,
    get_url,
    getThumbUrl,
    strftime_polyfill,
)

HANDLE = int(sys.argv[1])


def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def get_asset_info(id):
    return ItemAsset.from_api_response(api_get(f"/api/assets/{id}"))


def time(bucket, video):
    xbmcplugin.setContent(HANDLE, "images")

    # Buckets are always months since Immich 2.0.0, the size parameter is gone
    res = TimeBucket.from_api_response(
        api_get("/api/timeline/bucket", {"timeBucket": bucket})
    )

    items = []

    for asset_id, is_image in res.assets():
        # The bucket already tells us the type, so skip the fetch for photos
        if video and is_image:
            continue

        item = get_asset_info(asset_id)
        if not item.exifInfo.dateTimeOriginal:
            item.exifInfo.dateTimeOriginal = iso8601.parse_date(
                item.fileModifiedAt
            ).strftime("%Y-%m-%dT%H:%M:%S%z")

        items.append(
            (
                get_playback(item.id, item.type),
                xbmcgui.ListItem(get_asset_name(item)),
                False,
            )
        )
        items[-1][1].setArt({"thumb": getThumbUrl(item.id)})
        if item.originalMimeType:
            items[-1][1].setProperty("MimeType", item.originalMimeType)
        items[-1][1].setDateTime(item.exifInfo.dateTimeOriginal.replace("Z", "+00:00"))

    xbmcplugin.addDirectoryItems(HANDLE, items, len(items))
    xbmcplugin.addSortMethod(HANDLE, sortMethod=xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)


def timeline(video):
    video = "1" if video else ""

    res = api_get("/api/timeline/buckets")
    res = [TimelineBucket.from_api_response(i) for i in res]

    xbmcplugin.setContent(HANDLE, "files")

    items = [
        (
            get_url(action="time", id=i.timeBucket, video=video),
            xbmcgui.ListItem(
                strftime_polyfill(iso8601.parse_date(i.timeBucket), datelong)
            ),
            True,
        )
        for i in res
    ]
    for item, timeline in zip(items, res):
        item[1].setDateTime(
            last_day_of_month(iso8601.parse_date(timeline.timeBucket)).strftime(
                "%Y-%m-%dT00:00:00Z"
            )
        )

    xbmcplugin.addDirectoryItems(HANDLE, items, len(items))
    xbmcplugin.addSortMethod(HANDLE, sortMethod=xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
