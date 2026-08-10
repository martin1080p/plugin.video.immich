"""Data models mirroring the Immich REST API (target: Immich 3.1.0).

Every field is optional so that a response missing a key (older server) or
carrying extra keys (newer server) never breaks the plugin.  Unrecognised keys
are collected in ``unknown_fields`` to make debugging easier.
"""

from dataclasses import dataclass, fields
from typing import Any, List, Optional


class ApiModel:
    """Mixin giving dataclasses a lenient constructor for API payloads."""

    @classmethod
    def from_api_response(cls, data: Optional[dict]):
        """Create an instance from an API response, ignoring unknown fields."""
        if not data:
            return cls()
        known_fields = {f.name for f in fields(cls)}
        known_fields.discard("unknown_fields")
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        unknown = {k: v for k, v in data.items() if k not in known_fields}
        if unknown:
            filtered_data["unknown_fields"] = unknown
        return cls(**filtered_data)


def _at(values: Optional[list], index: int, default=None):
    """Read ``values[index]`` from one of the parallel arrays of a time bucket."""
    if not values or index >= len(values):
        return default
    value = values[index]
    return default if value is None else value


@dataclass
class User(ApiModel):
    """UserResponseDto"""

    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    profileImagePath: Optional[str] = None
    avatarColor: Optional[str] = None
    profileChangedAt: Optional[str] = None
    unknown_fields: Optional[dict] = None


@dataclass
class AssetStack(ApiModel):
    """AssetStackResponseDto"""

    id: Optional[str] = None
    primaryAssetId: Optional[str] = None
    assetCount: int = 0
    unknown_fields: Optional[dict] = None


@dataclass
class ExifInfo(ApiModel):
    """ExifResponseDto"""

    make: Optional[str] = None
    model: Optional[str] = None
    exifImageWidth: Optional[int] = None
    exifImageHeight: Optional[int] = None
    fileSizeInByte: Optional[int] = None
    orientation: Optional[str] = None
    dateTimeOriginal: Optional[str] = None
    modifyDate: Optional[str] = None
    timeZone: Optional[str] = None
    lensModel: Optional[str] = None
    fNumber: Optional[float] = None
    focalLength: Optional[float] = None
    iso: Optional[int] = None
    exposureTime: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    projectionType: Optional[str] = None
    rating: Optional[int] = None
    unknown_fields: Optional[dict] = None


@dataclass
class ItemAsset(ApiModel):
    """AssetResponseDto"""

    id: Optional[str] = None
    ownerId: Optional[str] = None
    owner: Optional[User] = None
    type: Optional[str] = None
    visibility: Optional[str] = None
    originalPath: Optional[str] = None
    originalFileName: Optional[str] = None
    originalMimeType: Optional[str] = None
    thumbhash: Optional[str] = None
    checksum: Optional[str] = None
    fileCreatedAt: Optional[str] = None
    fileModifiedAt: Optional[str] = None
    localDateTime: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    # Milliseconds since Immich 3.0.0 (a "H:MM:SS.SSS" string on older servers)
    duration: Optional[Any] = None
    width: Optional[int] = None
    height: Optional[int] = None
    isFavorite: bool = False
    isArchived: bool = False
    isTrashed: bool = False
    isOffline: bool = False
    isEdited: bool = False
    hasMetadata: bool = True
    resized: bool = False
    libraryId: Optional[str] = None
    livePhotoVideoId: Optional[str] = None
    duplicateId: Optional[str] = None
    stack: Optional[AssetStack] = None
    people: Optional[List[dict]] = None
    tags: Optional[List[dict]] = None
    exifInfo: Optional[ExifInfo] = None
    unknown_fields: Optional[dict] = None

    def __post_init__(self):
        # exifInfo is omitted entirely for assets without metadata
        if isinstance(self.exifInfo, dict):
            self.exifInfo = ExifInfo.from_api_response(self.exifInfo)
        elif self.exifInfo is None:
            self.exifInfo = ExifInfo()
        if isinstance(self.owner, dict):
            self.owner = User.from_api_response(self.owner)
        if isinstance(self.stack, dict):
            self.stack = AssetStack.from_api_response(self.stack)

    @property
    def is_image(self) -> bool:
        return (self.type or "IMAGE").upper() == "IMAGE"


@dataclass
class AlbumUser(ApiModel):
    """AlbumUserResponseDto"""

    user: Optional[User] = None
    role: Optional[str] = None
    unknown_fields: Optional[dict] = None

    def __post_init__(self):
        if isinstance(self.user, dict):
            self.user = User.from_api_response(self.user)


@dataclass
class Album(ApiModel):
    """AlbumResponseDto"""

    id: Optional[str] = None
    albumName: Optional[str] = None
    description: Optional[str] = None
    albumThumbnailAssetId: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    lastModifiedAssetTimestamp: Optional[str] = None
    albumUsers: Optional[List[AlbumUser]] = None
    contributorCounts: Optional[List[dict]] = None
    assetCount: int = 0
    shared: bool = False
    hasSharedLink: bool = False
    isActivityEnabled: bool = True
    order: Optional[str] = None
    # Dropped from AlbumResponseDto in Immich 3.0.0, kept for older servers
    ownerId: Optional[str] = None
    owner: Optional[User] = None
    assets: Optional[List[ItemAsset]] = None
    unknown_fields: Optional[dict] = None

    def __post_init__(self):
        if isinstance(self.owner, dict):
            self.owner = User.from_api_response(self.owner)
        if self.albumUsers:
            self.albumUsers = [
                AlbumUser.from_api_response(user) if isinstance(user, dict) else user
                for user in self.albumUsers
            ]
        if self.assets:
            self.assets = [
                ItemAsset.from_api_response(asset) if isinstance(asset, dict) else asset
                for asset in self.assets
            ]


@dataclass
class TimelineBucket(ApiModel):
    """TimeBucketsResponseDto - one entry per month of the timeline."""

    timeBucket: Optional[str] = None
    count: int = 0
    unknown_fields: Optional[dict] = None


@dataclass
class TimeBucket(ApiModel):
    """TimeBucketAssetResponseDto - parallel arrays, one entry per asset."""

    id: Optional[List[str]] = None
    ownerId: Optional[List[str]] = None
    visibility: Optional[List[str]] = None
    isFavorite: Optional[List[bool]] = None
    isImage: Optional[List[bool]] = None
    isTrashed: Optional[List[bool]] = None
    livePhotoVideoId: Optional[List[Optional[str]]] = None
    thumbhash: Optional[List[Optional[str]]] = None
    fileCreatedAt: Optional[List[str]] = None
    createdAt: Optional[List[str]] = None
    localOffsetHours: Optional[List[float]] = None
    duration: Optional[List[Optional[int]]] = None
    ratio: Optional[List[float]] = None
    projectionType: Optional[List[Optional[str]]] = None
    stack: Optional[List[Optional[List[str]]]] = None
    city: Optional[List[Optional[str]]] = None
    country: Optional[List[Optional[str]]] = None
    latitude: Optional[List[Optional[float]]] = None
    longitude: Optional[List[Optional[float]]] = None
    unknown_fields: Optional[dict] = None

    def __len__(self) -> int:
        return len(self.id or [])

    def assets(self):
        """Yield ``(asset_id, is_image)`` for every asset in the bucket."""
        for index, asset_id in enumerate(self.id or []):
            yield asset_id, bool(_at(self.isImage, index, True))
