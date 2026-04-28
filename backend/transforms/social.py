"""
Social Media Transforms
  - UsernameSearch:   Username -> SocialMedia profiles (public check)
  - SocialToEmail:    SocialMedia -> EmailAddress (where exposed)
"""
import asyncio
import httpx

from transforms.base import BaseTransform
from models import Entity, Edge, EntityType, TransformResult

# Sites to check for username availability
USERNAME_SITES = {
    "GitHub": "https://github.com/{username}",
    "Twitter/X": "https://x.com/{username}",
    "Instagram": "https://www.instagram.com/{username}/",
    "Reddit": "https://www.reddit.com/user/{username}",
    "TikTok": "https://www.tiktok.com/@{username}",
    "Twitch": "https://www.twitch.tv/{username}",
    "YouTube": "https://www.youtube.com/@{username}",
    "Medium": "https://medium.com/@{username}",
    "Dev.to": "https://dev.to/{username}",
    "HackerNews": "https://news.ycombinator.com/user?id={username}",
    "GitLab": "https://gitlab.com/{username}",
    "Keybase": "https://keybase.io/{username}",
    "Mastodon": "https://mastodon.social/@{username}",
    "Telegram": "https://t.me/{username}",
}


class UsernameSearch(BaseTransform):
    NAME = "username_search"
    DISPLAY_NAME = "Username Search"
    DESCRIPTION = "Search for a username across popular platforms (checks HTTP 200)."
    INPUT_TYPES = [EntityType.USERNAME]
    OUTPUT_TYPES = [EntityType.SOCIAL_MEDIA, EntityType.URL]
    OPTIONS_SCHEMA = {
        "timeout": {"type": "integer", "default": 8, "description": "Request timeout per site (seconds)"}
    }

    async def run(self, entity: dict, options: dict, api_keys: dict) -> TransformResult:
        username = entity["value"]
        timeout = int(options.get("timeout", 8))
        entities: list[Entity] = []
        edges: list[Edge] = []
        found: list[str] = []

        async def check_site(platform: str, url_template: str):
            url = url_template.format(username=username)
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True,
                                              headers={"User-Agent": "Mozilla/5.0"}) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        sm = self._make_entity(
                            EntityType.SOCIAL_MEDIA, url,
                            platform=platform,
                            username=username,
                            source="username_search",
                        )
                        entities.append(sm)
                        edges.append(self._make_edge(entity["id"], sm.id, "profile_found"))
                        found.append(platform)
            except Exception:
                pass  # Timeout or network error – not found

        await asyncio.gather(*[check_site(p, t) for p, t in USERNAME_SITES.items()])

        messages = [f"Found on: {', '.join(found)}"] if found else ["No profiles found"]
        return self._result(entity["id"], entities, edges, messages)
