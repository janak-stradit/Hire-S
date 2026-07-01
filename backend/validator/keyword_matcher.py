from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.validator.skill_matcher import match_skills

VECTORIZER = HashingVectorizer(
    stop_words="english", ngram_range=(1, 2), n_features=2**14, alternate_sign=False, norm="l2"
)


def keyword_relevance_score(resume_text: str, job_text: str, resume_skills: list[str], job_skills: list[str]) -> float:
    tfidf_score = _tfidf_score(resume_text, job_text)
    concept_coverage = match_skills(resume_skills, job_skills, resume_text).score
    return round((tfidf_score * 0.40) + (concept_coverage * 0.60), 2)


def _tfidf_score(resume_text: str, job_text: str) -> float:
    if not resume_text.strip() or not job_text.strip():
        return 0.0
    matrix = VECTORIZER.transform([resume_text, job_text])
    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100)


def _overlap_score(left: list[str], right: list[str]) -> float:
    if not right:
        return 100.0
    intersection = set(left).intersection(right)
    return (len(intersection) / len(set(right))) * 100
