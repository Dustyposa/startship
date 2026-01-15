"""
User data API routes for collections, tags, and notes.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import time

from .utils import get_db, ensure_success, ensure_entity_exists, build_response

router = APIRouter(prefix="/api/user", tags=["user-data"])


def _generate_id(prefix: str) -> str:
    """Generate a unique ID with given prefix."""
    return f"{prefix}-{int(time.time() * 1000)}"


# ==================== Request/Response Models ====================

class CollectionCreate(BaseModel):
    """Request model for creating a collection."""
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None


class CollectionUpdate(BaseModel):
    """Request model for updating a collection."""
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    position: Optional[int] = None


class CollectionResponse(BaseModel):
    """Response model for a collection."""
    id: str
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    position: int
    created_at: str
    updated_at: str


class TagCreate(BaseModel):
    """Request model for creating a tag."""
    name: str
    color: str = "#3B82F6"


class TagUpdate(BaseModel):
    """Request model for updating a tag."""
    name: Optional[str] = None
    color: Optional[str] = None


class TagResponse(BaseModel):
    """Response model for a tag."""
    id: str
    name: str
    color: str
    created_at: str
    updated_at: str


class NoteUpsert(BaseModel):
    """Request model for upserting a note."""
    note: Optional[str] = None
    rating: Optional[int] = None


class NoteResponse(BaseModel):
    """Response model for a note."""
    repo_id: str
    note: Optional[str] = None
    rating: Optional[int] = None
    created_at: str
    updated_at: str


class RepoToCollection(BaseModel):
    """Request model for adding a repo to a collection."""
    repo_id: str
    position: Optional[int] = None


class RepoToTag(BaseModel):
    """Request model for adding a tag to a repo."""
    repo_id: str


# ==================== Collections Endpoints ====================

@router.get("/collections", response_model=List[CollectionResponse])
async def get_collections(db = Depends(get_db)):
    """Get all collections."""
    collections = await db.get_collections()
    return [CollectionResponse(**c) for c in collections]


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
async def get_collection(collection_id: str, db = Depends(get_db)):
    """Get a collection by ID."""
    collection = await db.get_collection(collection_id)
    ensure_entity_exists(collection, "Collection not found")
    return CollectionResponse(**collection)


@router.post("/collections", response_model=CollectionResponse, status_code=201)
async def create_collection(data: CollectionCreate, db = Depends(get_db)):
    """Create a new collection."""
    collection_id = _generate_id("coll")
    position = len(await db.get_collections())

    ensure_success(
        await db.create_collection(collection_id, data.name, data.icon, data.color, position),
        "Failed to create collection"
    )

    return CollectionResponse(**await db.get_collection(collection_id))


@router.put("/collections/{collection_id}", response_model=CollectionResponse)
async def update_collection(collection_id: str, data: CollectionUpdate, db = Depends(get_db)):
    """Update a collection."""
    if await db.get_collection(collection_id) is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    ensure_success(
        await db.update_collection(collection_id, data.name, data.icon, data.color, data.position),
        "Failed to update collection"
    )

    return CollectionResponse(**await db.get_collection(collection_id))


@router.delete("/collections/{collection_id}", status_code=204)
async def delete_collection(collection_id: str, db = Depends(get_db)):
    """Delete a collection."""
    if await db.get_collection(collection_id) is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    ensure_success(await db.delete_collection(collection_id), "Failed to delete collection")


# ==================== Collection-Repo Operations ====================

@router.post("/collections/{collection_id}/repos", status_code=201)
async def add_repo_to_collection(collection_id: str, data: RepoToCollection, db = Depends(get_db)):
    """Add a repository to a collection."""
    if await db.get_collection(collection_id) is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    position = data.position if data.position is not None else len(await db.get_repos_in_collection(collection_id))

    ensure_success(
        await db.add_repo_to_collection(data.repo_id, collection_id, position),
        "Failed to add repo to collection"
    )

    return {"message": "Repo added to collection"}


@router.delete("/collections/{collection_id}/repos/{repo_id:path}", status_code=204)
async def remove_repo_from_collection(collection_id: str, repo_id: str, db = Depends(get_db)):
    """Remove a repository from a collection."""
    ensure_success(
        await db.remove_repo_from_collection(repo_id, collection_id),
        "Failed to remove repo from collection"
    )


@router.get("/collections/{collection_id}/repos", response_model=List[str])
async def get_repos_in_collection(collection_id: str, db = Depends(get_db)):
    """Get all repository IDs in a collection."""
    if await db.get_collection(collection_id) is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    return await db.get_repos_in_collection(collection_id)


# ==================== Tags Endpoints ====================

@router.get("/tags", response_model=List[TagResponse])
async def get_tags(db = Depends(get_db)):
    """Get all tags."""
    tags = await db.get_tags()
    return [TagResponse(**t) for t in tags]


@router.get("/tags/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: str, db = Depends(get_db)):
    """Get a tag by ID."""
    tag = await db.get_tag(tag_id)
    ensure_entity_exists(tag, "Tag not found")
    return TagResponse(**tag)


@router.post("/tags", response_model=TagResponse, status_code=201)
async def create_tag(data: TagCreate, db = Depends(get_db)):
    """Create a new tag."""
    tag_id = _generate_id("tag")

    ensure_success(
        await db.create_tag(tag_id, data.name, data.color),
        "Failed to create tag"
    )

    return TagResponse(**await db.get_tag(tag_id))


@router.put("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: str, data: TagUpdate, db = Depends(get_db)):
    """Update a tag."""
    if await db.get_tag(tag_id) is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    ensure_success(
        await db.update_tag(tag_id, data.name, data.color),
        "Failed to update tag"
    )

    return TagResponse(**await db.get_tag(tag_id))


@router.delete("/tags/{tag_id}", status_code=204)
async def delete_tag(tag_id: str, db = Depends(get_db)):
    """Delete a tag."""
    if await db.get_tag(tag_id) is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    ensure_success(await db.delete_tag(tag_id), "Failed to delete tag")


# ==================== Tag-Repo Operations ====================

@router.post("/tags/{tag_id}/repos", status_code=201)
async def add_tag_to_repo(tag_id: str, data: RepoToTag, db = Depends(get_db)):
    """Add a tag to a repository."""
    if await db.get_tag(tag_id) is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    ensure_success(
        await db.add_tag_to_repo(data.repo_id, tag_id),
        "Failed to add tag to repo"
    )

    return {"message": "Tag added to repo"}


@router.delete("/tags/{tag_id}/repos/{repo_id:path}", status_code=204)
async def remove_tag_from_repo(tag_id: str, repo_id: str, db = Depends(get_db)):
    """Remove a tag from a repository."""
    ensure_success(
        await db.remove_tag_from_repo(repo_id, tag_id),
        "Failed to remove tag from repo"
    )


@router.get("/repos/{repo_id:path}/tags", response_model=List[TagResponse])
async def get_tags_for_repo(repo_id: str, db = Depends(get_db)):
    """Get all tags for a repository."""
    tags = await db.get_tags_for_repo(repo_id)
    return [TagResponse(**t) for t in tags]


@router.get("/repos/{repo_id:path}/collection", response_model=Optional[CollectionResponse])
async def get_collection_for_repo(repo_id: str, db = Depends(get_db)):
    """Get the collection a repository belongs to."""
    collection = await db.get_collection_for_repo(repo_id)
    return CollectionResponse(**collection) if collection else None


# ==================== Notes Endpoints ====================

@router.get("/repos/{repo_id:path}/note", response_model=Optional[NoteResponse])
async def get_note(repo_id: str, db = Depends(get_db)):
    """Get a note for a repository."""
    note = await db.get_note(repo_id)
    return NoteResponse(**note) if note else None


@router.put("/repos/{repo_id:path}/note", response_model=NoteResponse)
async def upsert_note(repo_id: str, data: NoteUpsert, db = Depends(get_db)):
    """Create or update a note for a repository."""
    ensure_success(
        await db.upsert_note(repo_id, data.note, data.rating),
        "Failed to upsert note"
    )

    note = await db.get_note(repo_id)
    return NoteResponse(**note)


@router.delete("/repos/{repo_id:path}/note", status_code=204)
async def delete_note(repo_id: str, db = Depends(get_db)):
    """Delete a note for a repository."""
    ensure_success(await db.delete_note(repo_id), "Failed to delete note")


@router.get("/notes", response_model=List[NoteResponse])
async def get_all_notes(db = Depends(get_db)):
    """Get all notes."""
    notes = await db.get_all_notes()
    return [NoteResponse(**n) for n in notes]
