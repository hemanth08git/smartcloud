from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SensorSample:
    temperature: float
    humidity: Optional[float] = None


@dataclass
class EnvironmentProfile:
    avg_temp: float
    avg_humidity: float
    max_temp: float
    max_humidity: float
    sample_count: int

    @classmethod
    def from_samples(cls, samples: List[SensorSample]) -> "EnvironmentProfile":
        if not samples:
            return cls(avg_temp=0.0, avg_humidity=0.0, max_temp=0.0, max_humidity=0.0, sample_count=0)
        temps = [s.temperature for s in samples]
        hums = [s.humidity for s in samples if s.humidity is not None]
        avg_temp = sum(temps) / len(temps)
        avg_humidity = sum(hums) / len(hums) if hums else 0.0
        max_temp = max(temps)
        max_humidity = max(hums) if hums else 0.0
        return cls(
            avg_temp=avg_temp,
            avg_humidity=avg_humidity,
            max_temp=max_temp,
            max_humidity=max_humidity,
            sample_count=len(samples),
        )


@dataclass
class RiskResult:
    score: float
    level: str
    explanation: str


class SpoilageRiskModel:
    """Very simple rule-based risk model for demo purposes."""

    def __init__(
        self,
        max_safe_temp: float = 5.0,
        warning_temp: float = 8.0,
        max_safe_humidity: float = 70.0,
        weight_temp: float = 0.7,
        weight_humidity: float = 0.3,
    ):
        self.max_safe_temp = max_safe_temp
        self.warning_temp = warning_temp
        self.max_safe_humidity = max_safe_humidity
        self.weight_temp = weight_temp
        self.weight_humidity = weight_humidity

    def evaluate(self, profile: EnvironmentProfile) -> RiskResult:
        if profile.sample_count == 0:
            return RiskResult(score=0.0, level="UNKNOWN", explanation="No sensor data available.")

        # Temperature contribution
        temp_score = 0.0
        if profile.max_temp <= self.max_safe_temp:
            temp_score = 10.0
        elif profile.max_temp <= self.warning_temp:
            temp_score = 40.0
        else:
            temp_score = 80.0

        # Humidity contribution
        hum_score = 0.0
        if profile.max_humidity <= self.max_safe_humidity:
            hum_score = 10.0
        else:
            hum_score = 60.0

        combined = self.weight_temp * temp_score + self.weight_humidity * hum_score

        if combined < 25:
            level = "LOW"
        elif combined < 60:
            level = "MEDIUM"
        else:
            level = "HIGH"

        explanation = (
            f"Max temp: {profile.max_temp:.1f}°C, max humidity: {profile.max_humidity:.1f}%. "
            f"Combined risk score {combined:.1f}."
        )

        return RiskResult(score=combined, level=level, explanation=explanation)
