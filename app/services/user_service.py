"""
Servicio para gestión de usuarios
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.user_repository import user_repository
from app.models.user import User


class UserService:
    def __init__(self):
        self.repository = user_repository

    def authenticate_user(self, db: Session, phone_number: str) -> Optional[User]:
        """Autenticar usuario por número de teléfono"""
        # Limpiar formato del número
        clean_phone = self._clean_phone_number(phone_number)
        return self.repository.get_by_phone(db, clean_phone)

    def create_user(self, db: Session, phone_number: str, name: str, role: str = "employee") -> User:
        """Crear nuevo usuario"""
        clean_phone = self._clean_phone_number(phone_number)
        return self.repository.create_user(db, clean_phone, name, role)

    def is_authorized(self, db: Session, phone_number: str) -> bool:
        """Verificar si un usuario está autorizado"""
        clean_phone = self._clean_phone_number(phone_number)
        return self.repository.is_user_authorized(db, clean_phone)

    def get_user_by_phone(self, db: Session, phone_number: str) -> Optional[User]:
        """Obtener usuario por teléfono"""
        clean_phone = self._clean_phone_number(phone_number)
        return self.repository.get_by_phone(db, clean_phone)

    def _clean_phone_number(self, phone_number: str) -> str:
        """Limpiar y formatear número de teléfono"""
        # Remover espacios, guiones y caracteres especiales
        clean = ''.join(filter(str.isdigit, phone_number))
        
        # Si empieza con 521, es formato México con 52+1+número
        if clean.startswith('521') and len(clean) == 13:
            return clean
        
        # Si empieza con 52, agregar 1 para celulares mexicanos
        if clean.startswith('52') and len(clean) == 12:
            return f"521{clean[2:]}"
        
        # Si es número nacional de 10 dígitos, agregar código país
        if len(clean) == 10:
            return f"521{clean}"
        
        return clean


# Instancia global del servicio
user_service = UserService()