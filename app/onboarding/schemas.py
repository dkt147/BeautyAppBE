from pydantic import BaseModel


class OnboardingRequest(BaseModel):
    has_used_before: bool
    permissions_granted: bool
