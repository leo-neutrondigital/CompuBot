"""
Repositorio para gestión de usuarios
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.core.repository import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository[User, dict, dict]):
    def __init__(self):
        super().__init__(User)

    def get_by_phone(self, db: Session, phone_number: str) -> Optional[User]:
        """Obtener usuario por número de teléfono"""
        return db.query(User).filter(User.phone_number == phone_number).first()

    def get_active_users(self, db: Session, skip: int = 0, limit: int = 100):
        """Obtener usuarios activos"""
        return db.query(User).filter(User.active == True).offset(skip).limit(limit).all()

    def create_user(self, db: Session, phone_number: str, name: str, role: str = "employee") -> User:
        """Crear un nuevo usuario"""
        user_data = {
            "phone_number": phone_number,
            "name": name,
            "role": role,
            "active": True
        }
        return self.create(db, obj_in=user_data)

    def deactivate_user(self, db: Session, user_id: str) -> Optional[User]:
        """Desactivar un usuario"""
        user = self.get(db, user_id)
        if user:
            return self.update(db, db_obj=user, obj_in={"active": False})
        return None

    def is_user_authorized(self, db: Session, phone_number: str) -> bool:
        """Verificar si un usuario está autorizado y activo"""
        user = self.get_by_phone(db, phone_number)
        return user is not None and user.active


# Instancia global del repositorio
user_repository = UserRepository()