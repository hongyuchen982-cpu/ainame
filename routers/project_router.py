from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.authtools import AuthHandler
from dependencies import get_session
from repository.project_repo import NamingProjectRepository
from schemas.project_schemas import (
    ProjectCreateIn,
    ProjectDetailOut,
    ProjectListOut,
    ProjectStatus,
    ProjectUpdateIn,
)


router = APIRouter(prefix="/projects", tags=["命名项目"])
auth_handler = AuthHandler()


def project_list_response(project, final_name: str | None = None) -> dict:
    return {
        "id": project.id,
        "title": project.title,
        "category": project.category,
        "status": project.status,
        "conditions": project.conditions or {},
        "thread_id": project.thread_id,
        "current_round": project.current_round,
        "final_name": final_name,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "archived_at": project.archived_at,
    }


def project_detail_response(project, rounds, selected) -> dict:
    data = project_list_response(project, selected.name if selected else None)
    data["rounds"] = [
        {
            "id": naming_round.id,
            "round_no": naming_round.round_no,
            "feedback": naming_round.feedback,
            "created_at": naming_round.created_at,
            "candidates": [
                {
                    "id": candidate.id,
                    "name": candidate.name,
                    "reference": candidate.reference,
                    "moral": candidate.moral,
                    "domain": candidate.domain,
                    "domain_status": candidate.domain_status,
                }
                for candidate in candidates
            ],
        }
        for naming_round, candidates in rounds
    ]
    data["final_selection"] = None if selected is None else {
        "id": selected.id,
        "name": selected.name,
        "reference": selected.reference,
        "moral": selected.moral,
        "logo_url": selected.logo_url,
        "logo_status": selected.logo_status,
        "can_generate_logo": selected.category == "企业名",
    }
    return data


@router.post("", response_model=ProjectListOut)
async def create_project(
    data: ProjectCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    conditions = data.conditions.model_dump(exclude={"project_id"})
    project = await NamingProjectRepository(session).create_draft(
        user_id=user_id,
        title=data.title,
        category=data.conditions.category,
        conditions=conditions,
    )
    return project_list_response(project)


@router.get("", response_model=list[ProjectListOut])
async def list_projects(
    status: ProjectStatus | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    rows = await NamingProjectRepository(session).list_for_user(
        user_id, status=status, limit=limit, offset=offset
    )
    return [project_list_response(project, final_name) for project, final_name in rows]


@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get_project(
    project_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    project, rounds, selected = await NamingProjectRepository(session).detail_parts(
        project_id, user_id
    )
    if project is None:
        raise HTTPException(status_code=404, detail="命名项目不存在")
    return project_detail_response(project, rounds, selected)


@router.patch("/{project_id}", response_model=ProjectListOut)
async def update_project(
    project_id: int,
    data: ProjectUpdateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    conditions = (
        data.conditions.model_dump(exclude={"project_id"})
        if data.conditions is not None else None
    )
    try:
        project = await NamingProjectRepository(session).update_project(
            project_id,
            user_id,
            title=data.title,
            conditions=conditions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if project is None:
        raise HTTPException(status_code=404, detail="命名项目不存在")
    _, _, selected = await NamingProjectRepository(session).detail_parts(project_id, user_id)
    return project_list_response(project, selected.name if selected else None)


@router.post("/{project_id}/archive", response_model=ProjectListOut)
async def archive_project(
    project_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    project = await NamingProjectRepository(session).set_archived(
        project_id, user_id, True
    )
    if project is None:
        raise HTTPException(status_code=404, detail="命名项目不存在")
    _, _, selected = await NamingProjectRepository(session).detail_parts(project_id, user_id)
    return project_list_response(project, selected.name if selected else None)


@router.post("/{project_id}/restore", response_model=ProjectListOut)
async def restore_project(
    project_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    project = await NamingProjectRepository(session).set_archived(
        project_id, user_id, False
    )
    if project is None:
        raise HTTPException(status_code=404, detail="命名项目不存在")
    _, _, selected = await NamingProjectRepository(session).detail_parts(project_id, user_id)
    return project_list_response(project, selected.name if selected else None)
