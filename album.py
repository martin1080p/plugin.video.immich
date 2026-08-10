import sys

import xbmcgui
import xbmcplugin

import iso8601
from models import Album, ItemAsset
from utils import (
    api_get,
    api_post,
    get_asset_name,
    get_original,
    get_playback,
    get_url,
    getThumbUrl,
)

HANDLE = int(sys.argv[1])

# Maximum allowed by /api/search/metadata
PAGE_SIZE = 1000


def list_albums():
    res = api_get("/api/albums")
    res = [Album.from_api_response(i) for i in res]

    items = [
        (get_url(action="album", id=album.id), xbmcgui.ListItem(album.albumName), True)
        for album in res
    ]
    for item, album in zip(items, res):
        if album.startDate:
            item[1].setDateTime(
                iso8601.parse_date(album.startDate).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        if album.albumThumbnailAssetId:
            item[1].setArt({"thumb": getThumbUrl(album.albumThumbnailAssetId)})
    xbmcplugin.addSortMethod(HANDLE, sortMethod=xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(HANDLE, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addDirectoryItems(HANDLE, items, len(items))
    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)


def get_album_assets(id):
    """Return every asset of an album.

    Immich 3.0.0 dropped the embedded ``assets`` list from the album response,
    so the assets are searched for separately. Older servers still ship them
    inline and are answered from that list.
    """
    info = Album.from_api_response(api_get(f"/api/albums/{id}"))
    if info.assets:
        return info.assets

    body = {"albumIds": [id], "withExif": True, "size": PAGE_SIZE, "page": 1}
    order = (info.order or "").lower()
    if order in ("asc", "desc"):
        body["order"] = order

    assets = []
    while body["page"]:
        res = api_post("/api/search/metadata", body)["assets"]
        assets.extend(ItemAsset.from_api_response(i) for i in res.get("items", []))
        next_page = res.get("nextPage")
        body["page"] = int(next_page) if next_page else None
    return assets


def album(id):
    xbmcplugin.setContent(HANDLE, "images")

    res = get_album_assets(id)

    for i in res:
        if not i.exifInfo.dateTimeOriginal:
            i.exifInfo.dateTimeOriginal = iso8601.parse_date(
                i.fileModifiedAt
            ).strftime("%Y-%m-%dT%H:%M:%S%z")

    items = [
        (
            get_original(asset.id) if asset.is_image else get_playback(asset.id),
            xbmcgui.ListItem(get_asset_name(asset)),
            False,
        )
        for asset in res
    ]
    for item, asset in zip(items, res):
        item[1].setArt({"thumb": getThumbUrl(asset.id)})
        if asset.originalMimeType:
            item[1].setProperty("MimeType", asset.originalMimeType)
        item[1].setDateTime(asset.exifInfo.dateTimeOriginal)
    xbmcplugin.addDirectoryItems(HANDLE, items, len(items))
    xbmcplugin.addSortMethod(HANDLE, sortMethod=xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
