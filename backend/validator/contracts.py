from pydantic import BaseModel, ConfigDict, Field, model_validator


class ParsedResumeData(BaseModel):
    skills: list[str] = Field(default_factory=list)
    total_experience_years: float = 0
    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    sections: dict[str, str] = Field(default_factory=dict)
    raw_text: str = ""


class ParsedJobDescriptionData(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_min: int | None = None
    experience_max: int | None = None
    education_requirements: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    raw_text: str = ""


class ScoreWeights(BaseModel):
    skills: float = 0.40
    experience: float = 0.25
    education: float = 0.10
    certifications: float = 0.10
    keywords: float = 0.15

    def normalized(self) -> "ScoreWeights":
        total = self.skills + self.experience + self.education + self.certifications + self.keywords
        return ScoreWeights(
            skills=self.skills / total,
            experience=self.experience / total,
            education=self.education / total,
            certifications=self.certifications / total,
            keywords=self.keywords / total,
        )


class Thresholds(BaseModel):
    pass_score: float = 75
    review_score: float = 60

    @model_validator(mode="after")
    def validate_order(self) -> "Thresholds":
        if not 0 <= self.review_score < self.pass_score <= 100:
            raise ValueError("Thresholds must satisfy 0 <= review_score < pass_score <= 100")
        return self


class SkillMatchResult(BaseModel):
    score: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    evidence: dict[str, list[str]] = Field(default_factory=dict)


class ScoreBreakdown(BaseModel):
    skill_score: float
    experience_score: float
    education_score: float
    certification_score: float
    keyword_score: float
    final_score: float


class DecisionResult(BaseModel):
    decision: str
    queue_target: str


class ValidatorEvaluation(BaseModel):
    validator_result_id: str
    application_id: str
    candidate_id: str
    job_id: str
    parsed_resume_id: str
    parsed_jd_id: str
    scores: ScoreBreakdown
    decision: str
    queue_target: str
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    skill_evidence: dict[str, list[str]] = Field(default_factory=dict)
    explanation: str

    model_config = ConfigDict(from_attributes=True)


class EvaluateRequest(BaseModel):
    application_id: str
    weights: ScoreWeights | None = None
    thresholds: Thresholds | None = None


class BulkEvaluateRequest(BaseModel):
    application_ids: list[str] = Field(min_length=1, max_length=5000)
    weights: ScoreWeights | None = None
    thresholds: Thresholds | None = None


class BulkEvaluateResponse(BaseModel):
    total_requested: int
    evaluated: int
    results: list[ValidatorEvaluation]
