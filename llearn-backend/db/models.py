from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    lessons: Mapped[list["Lesson"]] = relationship(back_populates="course", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(120), primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    course: Mapped[Course | None] = relationship(back_populates="lessons")
    objectives: Mapped[list["LearningObjective"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="LearningObjective.position",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")


class LearningObjective(Base):
    __tablename__ = "learning_objectives"
    __table_args__ = (UniqueConstraint("lesson_id", "position", name="uq_objective_lesson_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    lesson: Mapped[Lesson] = relationship(back_populates="objectives")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(120), primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    student: Mapped[Student] = relationship(back_populates="enrollments")
    lesson: Mapped[Lesson] = relationship(back_populates="enrollments")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), nullable=False, index=True)
    scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    student: Mapped[Student] = relationship(back_populates="assessments")
    lesson: Mapped[Lesson] = relationship(back_populates="assessments")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    student: Mapped[Student] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat_session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chat_session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    chat_session: Mapped[ChatSession] = relationship(back_populates="messages")
