from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base

class VapiConfig(Base):
    __tablename__ = "vapi_configurations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    transcriber_model: Mapped[str] = mapped_column(String(100), default="assemblyai")
    voice_provider: Mapped[str] = mapped_column(String(100), default="vapi")
    voice_id: Mapped[str] = mapped_column(String(100), default="naina")
    llm_model: Mapped[str] = mapped_column(String(100), default="anthropic-bedrock")
    
    # Advanced Transcriber Settings
    transcriber_language: Mapped[str] = mapped_column(String(50), default="en")
    transcriber_background_denoising: Mapped[bool] = mapped_column(Boolean, default=False)
    transcriber_confidence_threshold: Mapped[float] = mapped_column(Float, default=1.0)
    transcriber_keyterms: Mapped[str] = mapped_column(Text, default="")
    transcriber_end_of_turn_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    transcriber_min_end_of_turn_silence: Mapped[int] = mapped_column(Integer, default=160)
    transcriber_max_turn_silence: Mapped[int] = mapped_column(Integer, default=400)
    transcriber_smart_endpointing: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Fallback Transcriber Settings
    transcriber_fallback_provider: Mapped[str] = mapped_column(String(100), default="deepgram")
    transcriber_fallback_language: Mapped[str] = mapped_column(String(50), default="en")
    transcriber_fallback_model: Mapped[str] = mapped_column(String(100), default="nova-2-general")

    # Advanced LLM Settings
    llm_temperature: Mapped[float] = mapped_column(Float, default=0.7)
    llm_max_tokens: Mapped[int] = mapped_column(Integer, default=250)
    llm_emotion_recognition_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    llm_num_fast_turns: Mapped[int] = mapped_column(Integer, default=1)

    # Advanced Voice Settings
    voice_speed: Mapped[float] = mapped_column(Float, default=1.0)
    voice_stability: Mapped[float] = mapped_column(Float, default=0.5)
    voice_similarity_boost: Mapped[float] = mapped_column(Float, default=0.75)
    voice_optimize_streaming_latency: Mapped[int] = mapped_column(Integer, default=3)
    voice_filler_injection_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    voice_background_sound: Mapped[str] = mapped_column(String(50), default="off")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
