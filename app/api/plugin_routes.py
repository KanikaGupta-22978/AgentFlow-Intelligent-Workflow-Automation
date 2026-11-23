
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.plugin import PluginCreate, PluginResponse
from app.services.plugin_service import (
    create_plugin,
    get_all_plugins,
    get_plugin_by_name,
)

router = APIRouter(prefix="/plugins", tags=["Plugins"])


@router.post("/", response_model=PluginResponse)
def register_plugin(
    plugin_data: PluginCreate,
    db: Session = Depends(get_db),
):
    existing_plugin = get_plugin_by_name(db, plugin_data.name)

    if existing_plugin:
        raise HTTPException(
            status_code=400,
            detail="Plugin already exists",
        )

    return create_plugin(db, plugin_data)


@router.get("/", response_model=list[PluginResponse])
def list_plugins(db: Session = Depends(get_db)):
    return get_all_plugins(db)
