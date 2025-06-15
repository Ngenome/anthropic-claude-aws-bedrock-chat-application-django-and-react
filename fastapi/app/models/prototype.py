from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class DesignProject(Base):
    __tablename__ = "design_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="design_projects")
    groups = relationship("Group", back_populates="design_project", cascade="all, delete-orphan")
    prototypes = relationship("Prototype", back_populates="design_project", cascade="all, delete-orphan")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    design_project_id = Column(UUID(as_uuid=True), ForeignKey("design_projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    design_project = relationship("DesignProject", back_populates="groups")
    prototypes = relationship("Prototype", back_populates="group")

class Prototype(Base):
    __tablename__ = "prototypes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    design_project_id = Column(UUID(as_uuid=True), ForeignKey("design_projects.id"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True)
    title = Column(String(200), nullable=False)
    prompt = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    design_project = relationship("DesignProject", back_populates="prototypes")
    group = relationship("Group", back_populates="prototypes")
    variants = relationship("PrototypeVariant", back_populates="prototype", cascade="all, delete-orphan")

class PrototypeVariant(Base):
    __tablename__ = "prototype_variants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prototype_id = Column(UUID(as_uuid=True), ForeignKey("prototypes.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_original = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    prototype = relationship("Prototype", back_populates="variants")
    versions = relationship("PrototypeVersion", back_populates="variant", cascade="all, delete-orphan")

class PrototypeVersion(Base):
    __tablename__ = "prototype_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("prototype_variants.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    edit_prompt = Column(Text, nullable=True)
    html_content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    variant = relationship("PrototypeVariant", back_populates="versions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('variant_id', 'version_number', name='unique_variant_version'),
    ) 