from pydantic import BaseModel, Field
from typing import List, Union


class FamilyMemberInput(BaseModel):
    nickname: str
    gender: str
    age: int = Field(..., ge=1, le=120)
    height: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)


class PersonaProfileBuildInput(BaseModel):
    id: int | str
    household_type: str
    family_count: int = Field(..., ge=1)
    monthly_budget: int = Field(..., gt=0)
    meals_per_day: int = Field(..., ge=1, le=5)
    purpose: List[str] = Field(..., min_length=1)
    activity_level: Union[int, str]
    family_members: List[FamilyMemberInput] = Field(..., min_length=1)
