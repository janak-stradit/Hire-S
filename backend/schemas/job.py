from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobBase(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    department: str = Field(min_length=2, max_length=180)
    location: str = Field(min_length=2, max_length=180)
    employment_type: str = Field(min_length=2, max_length=80)
    experience_min: int | None = Field(default=None, ge=0)
    experience_max: int | None = Field(default=None, ge=0)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    description: str = Field(min_length=10)
    skills_required: list[str] = Field(min_length=1)
    preferred_skills: list[str] = Field(default_factory=list)
    education_requirements: str = ""
    mandatory_certifications: list[str] = Field(default_factory=list)
    status: str = Field(default="open", max_length=40)
    screening_pass_score: float | None = Field(default=75.0, ge=0.0, le=100.0)
    screening_review_score: float | None = Field(default=60.0, ge=0.0, le=100.0)

    @field_validator("experience_max")
    @classmethod
    def validate_experience_range(cls, value: int | None, info):
        minimum = info.data.get("experience_min")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("experience_max must be greater than or equal to experience_min")
        return value

    @field_validator("salary_max")
    @classmethod
    def validate_salary_range(cls, value: int | None, info):
        minimum = info.data.get("salary_min")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("salary_max must be greater than or equal to salary_min")
        return value


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    department: str | None = Field(default=None, min_length=2, max_length=180)
    location: str | None = Field(default=None, min_length=2, max_length=180)
    employment_type: str | None = Field(default=None, min_length=2, max_length=80)
    experience_min: int | None = Field(default=None, ge=0)
    experience_max: int | None = Field(default=None, ge=0)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, min_length=10)
    skills_required: list[str] | None = None
    preferred_skills: list[str] | None = None
    education_requirements: str | None = None
    mandatory_certifications: list[str] | None = None
    status: str | None = Field(default=None, max_length=40)
    screening_pass_score: float | None = Field(default=None, ge=0.0, le=100.0)
    screening_review_score: float | None = Field(default=None, ge=0.0, le=100.0)


class JobRead(BaseModel):
    job_id: str
    title: str
    department: str
    location: str
    employment_type: str
    experience_min: int | None
    experience_max: int | None
    salary_min: int | None
    salary_max: int | None
    description: str
    skills_required: list[str]
    preferred_skills: list[str]
    education_requirements: str
    mandatory_certifications: list[str]
    status: str
    created_by: str
    screening_pass_score: float | None
    screening_review_score: float | None

    model_config = ConfigDict(from_attributes=True)
