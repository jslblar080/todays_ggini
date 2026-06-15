import json

from schemas.persona_profile_schema import PersonaProfileBuildInput
from services.persona.persona_service import build_persona_profile_response


sample_request = {
    "id": 4,
    "household_type": "1인 가구",
    "family_count": 1,
    "monthly_budget": 300000,
    "meals_per_day": 3,
    "purpose": ["다이어트", "간편식"],
    "activity_level": 2,
    "family_members": [
        {
            "nickname": "본인",
            "gender": "남",
            "age": 26,
            "height": 178.0,
            "weight": 75.5,
        }
    ],
}

validated = PersonaProfileBuildInput(**sample_request)
response = build_persona_profile_response(validated.model_dump())

print(json.dumps(response, ensure_ascii=False, indent=2))
