from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()

class LoginRequest(BaseModel):
    username: str = Field(..., example="admin", description="Nombre de usuario o correo")
    password: str = Field(..., example="123456", description="Contraseña de acceso")

@router.post("/login", tags=["Autenticación"])
def login_usuario(credenciales: LoginRequest):
    if credenciales.username == "admin" and credenciales.password == "123456":
        return {
            "access_token": "token_jwt_ejemplo_abc123",
            "token_type": "bearer",
            "mensaje": "Login exitoso"
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuario o contraseña incorrectos"
    )