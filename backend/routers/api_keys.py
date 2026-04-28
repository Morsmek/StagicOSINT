"""
API Key management routes
GET    /api-keys       - list stored keys (masked)
POST   /api-keys       - add or update a key
DELETE /api-keys/{id}  - remove a key
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from database import get_db, db_set_api_key, db_list_api_keys, db_delete_api_key
from models import ApiKeyCreate, ApiKey

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKey])
async def list_keys(db: aiosqlite.Connection = Depends(get_db)):
    return await db_list_api_keys(db)


@router.post("", response_model=ApiKey, status_code=201)
async def add_key(body: ApiKeyCreate, db: aiosqlite.Connection = Depends(get_db)):
    key_id = str(uuid.uuid4())
    await db_set_api_key(db, key_id, body.name, body.key, body.description)
    key = body.key
    masked = f"{'*' * (len(key) - 4)}{key[-4:]}" if len(key) > 4 else "****"
    return ApiKey(id=key_id, name=body.name, key_masked=masked, description=body.description)


@router.delete("/{key_id}", status_code=204)
async def delete_key(key_id: str, db: aiosqlite.Connection = Depends(get_db)):
    await db_delete_api_key(db, key_id)
