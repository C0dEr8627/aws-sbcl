from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Builder:
    alias: str
    display_name: str
    location: str
    followers: int
    following: int
    profile_url: str
    email: str | None = None
    scraped_at: str = ""

    @property
    def is_target(self) -> bool:
        return (
            self.location.strip().casefold().endswith("india")
            and self.followers == 0
            and self.following == 0
        )
