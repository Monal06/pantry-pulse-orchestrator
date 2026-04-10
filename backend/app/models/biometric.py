from __future__ import annotations

from pydantic import BaseModel, Field

class BiometricData(BaseModel):
    heart_rate_bpm: int = Field(default=70, description="Resting heart rate in beats per minute")
    hrv_ms: float = Field(default=55.0, description="Heart rate variability in milliseconds")
    sleep_score_100: int = Field(default=85, description="Sleep quality score from 0 to 100")
    steps_today: int = Field(default=4000, description="Steps taken today")
    readiness_score: int = Field(default=80, description="Daily readiness/recovery score 0 to 100")
    stress_level: str = Field(default="medium", description="Perceived or measured stress: 'low', 'medium', 'high'")

    def to_prompt_string(self) -> str:
        return (
            f"Biometrics -> "
            f"Resting HR: {self.heart_rate_bpm} BPM, "
            f"HRV: {self.hrv_ms} ms, "
            f"Sleep Score: {self.sleep_score_100}/100, "
            f"Steps Today: {self.steps_today}, "
            f"Readiness: {self.readiness_score}/100, "
            f"Stress Level: {self.stress_level}."
        )
