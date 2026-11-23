
from sqlalchemy.orm import Session

from app.database.models import Plugin
from app.schemas.plugin import PluginCreate


def create_plugin(db: Session, plugin_data: PluginCreate):
    plugin = Plugin(
        name=plugin_data.name,
        description=plugin_data.description,
        configuration=plugin_data.configuration,
    )

    db.add(plugin)
    db.commit()
    db.refresh(plugin)

    return plugin


def get_all_plugins(db: Session):
    return db.query(Plugin).all()


def get_plugin_by_name(db: Session, plugin_name: str):
    return db.query(Plugin).filter(
        Plugin.name == plugin_name
    ).first()
