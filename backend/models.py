"""
OGI Data Models
Entity types, graph nodes, edges, and transforms.
"""
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# ---------------------------------------------------------------------------
# Entity Types
# ---------------------------------------------------------------------------

class EntityType(str, Enum):
    PERSON = "Person"
    USERNAME = "Username"
    DOMAIN = "Domain"
    IP_ADDRESS = "IPAddress"
    EMAIL = "EmailAddress"
    PHONE = "PhoneNumber"
    ORGANIZATION = "Organization"
    URL = "URL"
    SOCIAL_MEDIA = "SocialMedia"
    HASH = "Hash"
    DOCUMENT = "Document"
    LOCATION = "Location"
    AS_NUMBER = "ASNumber"
    NETWORK = "Network"
    MX_RECORD = "MXRecord"
    NS_RECORD = "NSRecord"
    NAMESERVER = "Nameserver"
    SSL_CERTIFICATE = "SSLCertificate"
    SUBDOMAIN = "Subdomain"
    HTTP_HEADER = "HTTPHeader"


# ---------------------------------------------------------------------------
# Graph Node / Entity
# ---------------------------------------------------------------------------

class EntityBase(BaseModel):
    type: EntityType
    value: str
    label: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

class EntityCreate(EntityBase):
    pass

class Entity(EntityBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Graph position
    x: float = 0.0
    y: float = 0.0

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Graph Edge / Link
# ---------------------------------------------------------------------------

class EdgeBase(BaseModel):
    source_id: str
    target_id: str
    relation: str = "related_to"
    properties: dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0

class EdgeCreate(EdgeBase):
    pass

class Edge(EdgeBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class Graph(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    entities: list[Entity] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GraphCreate(BaseModel):
    name: str
    description: Optional[str] = None

class GraphSummary(BaseModel):
    id: str
    name: str
    description: Optional[str]
    entity_count: int
    edge_count: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------

class TransformInput(BaseModel):
    entity_id: str
    graph_id: str
    transform_name: str
    options: dict[str, Any] = Field(default_factory=dict)

class TransformResult(BaseModel):
    entities: list[Entity] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    transform_name: str
    input_entity_id: str
    success: bool = True
    error: Optional[str] = None

class TransformInfo(BaseModel):
    name: str
    display_name: str
    description: str
    input_types: list[EntityType]
    output_types: list[EntityType]
    requires_api_key: bool = False
    api_key_name: Optional[str] = None
    options_schema: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------

class ApiKeyCreate(BaseModel):
    name: str
    key: str
    description: Optional[str] = None

class ApiKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    key_masked: str  # Only show last 4 chars
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# AI Investigator
# ---------------------------------------------------------------------------

class InvestigateRequest(BaseModel):
    graph_id: str
    prompt: str
    max_steps: int = 10
    require_approval: bool = True

class InvestigateStep(BaseModel):
    step: int
    action: str
    reasoning: str
    approved: Optional[bool] = None

class InvestigateResponse(BaseModel):
    session_id: str
    steps: list[InvestigateStep] = Field(default_factory=list)
    summary: Optional[str] = None
    completed: bool = False
