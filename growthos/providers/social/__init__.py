from .base import (
    Capabilities,
    MediaItem,
    MediaKind,
    NotConfiguredError,
    PostDraft,
    ProviderError,
    PublishResult,
    PublishStatus,
    SocialProvider,
)
from .meta import FacebookPageProvider, InstagramProvider, ThreadsProvider
from .reddit import RedditAssistedProvider
from .telegram import TelegramProvider
from .tiktok import TikTokProvider
from .x import XProvider
from .youtube import YouTubeProvider

PROVIDERS: dict[str, type[SocialProvider]] = {
    "telegram": TelegramProvider,
    "instagram": InstagramProvider,
    "facebook": FacebookPageProvider,
    "threads": ThreadsProvider,
    "x": XProvider,
    "youtube": YouTubeProvider,
    "tiktok": TikTokProvider,
    "reddit": RedditAssistedProvider,
}


def get_provider(name: str) -> SocialProvider:
    try:
        return PROVIDERS[name]()
    except KeyError:
        raise ProviderError(f"unknown platform '{name}', known: {', '.join(PROVIDERS)}") from None


__all__ = [
    "PROVIDERS", "get_provider", "Capabilities", "MediaItem", "MediaKind", "NotConfiguredError",
    "PostDraft", "ProviderError", "PublishResult", "PublishStatus", "SocialProvider",
]
