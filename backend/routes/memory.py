"""Memory Routes — client profiles, finance, and project memory management."""

import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services import vault

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["Memory"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ClientProfileCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    tags: list[str] = []
    notes: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "Active"


# ── Client endpoints ─────────────────────────────────────────────────────────

@router.get("/clients")
async def list_clients():
    """List all client profiles in Memory/Clients/."""
    files = vault.list_memory_files("Clients")
    return {"count": len(files), "clients": files}


@router.post("/clients")
async def create_client(body: ClientProfileCreate):
    """Create a new client profile."""
    slug = _slugify(body.name)
    filename = f"{slug}.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Check if already exists
    try:
        vault.read_memory_file("Clients", filename)
        raise HTTPException(status_code=409, detail=f"Client profile already exists: {slug}")
    except FileNotFoundError:
        pass

    tags_str = ", ".join(body.tags) if body.tags else "New Customer"
    content = f"""# Client Profile: {body.name}

> **Created:** {now}
> **Last Contact:** {now}

## Contact
- **Name:** {body.name}
- **Email:** {body.email}
"""
    if body.phone:
        content += f"- **Phone:** {body.phone}\n"

    content += f"""
## Tags
- {tags_str}

## Interaction History

| Date | Type | Summary |
|------|------|---------|
| {now} | Profile Created | New client profile created |
"""

    if body.notes:
        content += f"\n## Notes\n\n{body.notes}\n"

    path = vault.write_memory_file("Clients", filename, content)
    return {"status": "created", "slug": slug, "path": path}


@router.get("/clients/{slug}")
async def get_client(slug: str):
    """Read a client profile by slug."""
    filename = f"{slug}.md"
    try:
        content = vault.read_memory_file("Clients", filename)
        return {"slug": slug, "filename": filename, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Client not found: {slug}")


# ── Finance endpoints ────────────────────────────────────────────────────────

@router.get("/finance")
async def list_finance():
    """List all finance memory files."""
    files = vault.list_memory_files("Finance")
    return {"count": len(files), "files": files}


@router.get("/finance/{name}")
async def get_finance_file(name: str):
    """Read a finance memory file by name."""
    filename = f"{name}.md" if not name.endswith(".md") else name
    try:
        content = vault.read_memory_file("Finance", filename)
        return {"filename": filename, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Finance file not found: {name}")


# ── Project endpoints ────────────────────────────────────────────────────────

@router.get("/projects")
async def list_projects():
    """List all project memory files."""
    files = vault.list_memory_files("Projects")
    return {"count": len(files), "projects": files}


@router.post("/projects")
async def create_project(body: ProjectCreate):
    """Create a new project memory file."""
    slug = _slugify(body.name)
    filename = f"{slug}.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    try:
        vault.read_memory_file("Projects", filename)
        raise HTTPException(status_code=409, detail=f"Project already exists: {slug}")
    except FileNotFoundError:
        pass

    content = f"""# Project: {body.name}

> **Created:** {now}
> **Status:** {body.status}

## Description

{body.description or 'No description provided.'}

## Timeline

| Date | Milestone | Status |
|------|-----------|--------|
| {now} | Project Created | Active |

## Tasks

- [ ] Define scope
- [ ] Assign resources
- [ ] Set deadlines

## Notes

_(Add project notes here)_
"""

    path = vault.write_memory_file("Projects", filename, content)
    return {"status": "created", "slug": slug, "path": path}


@router.get("/projects/{slug}")
async def get_project(slug: str):
    """Read a project memory file by slug."""
    filename = f"{slug}.md"
    try:
        content = vault.read_memory_file("Projects", filename)
        return {"slug": slug, "filename": filename, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {slug}")


# ── Helper ────────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    return slug.strip('-')
