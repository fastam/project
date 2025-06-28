# main.py
from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import base64
from database import ActivityRequest, init_db, get_db

# Создаем экземпляр приложения FastAPI
app = FastAPI(title="Activity Registry API")

# Инициализируем базу данных при запуске
init_db()

# Модели для валидации данных
class ActivityRequestCreate(BaseModel):
    full_name: str
    group_name: Optional[str] = ""
    supervisor: Optional[str] = ""
    activity: str

class ActivityRequestResponse(BaseModel):
    id: int
    full_name: str
    group_name: str
    supervisor: str
    activity: str
    file_name: str
    file_type: str
    status: str
    created_at: str

class AdminLogin(BaseModel):
    password: str

class UpdateStatus(BaseModel):
    status: str  # "approved" или "rejected"

# Настройка CORS для взаимодействия с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Константы
ADMIN_PASSWORD = "1234"

@app.get("/")
def read_root():
    """Главная страница API"""
    return {"message": "Activity Registry API работает!"}

@app.post("/api/requests")
async def create_request(
    full_name: str = Form(...),
    group_name: str = Form(""),
    supervisor: str = Form(""),
    activity: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Создание новой заявки на активность"""
    try:
        # Проверяем тип файла
        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="Разрешены только файлы JPG, PNG и PDF"
            )
        
        # Читаем файл и кодируем в base64
        file_content = await file.read()
        file_base64 = base64.b64encode(file_content).decode()
        
        # Создаем новую заявку
        new_request = ActivityRequest(
            full_name=full_name,
            group_name=group_name,
            supervisor=supervisor,
            activity=activity,
            file_name=file.filename,
            file_content=file_base64,
            file_type=file.content_type,
            status="pending"
        )
        
        # Добавляем в базу данных
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        return {"message": "Заявка успешно отправлена!", "id": new_request.id}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании заявки: {str(e)}")

@app.post("/api/admin/login")
def admin_login(login_data: AdminLogin):
    """Авторизация администратора"""
    if login_data.password == ADMIN_PASSWORD:
        return {"success": True, "message": "Успешная авторизация"}
    else:
        raise HTTPException(status_code=401, detail="Неверный пароль")

@app.get("/api/admin/requests/pending")
def get_pending_requests(db: Session = Depends(get_db)):
    """Получение всех заявок на рассмотрении"""
    requests = db.query(ActivityRequest).filter(
        ActivityRequest.status == "pending"
    ).order_by(ActivityRequest.created_at.desc()).all()
    
    return [
        {
            "id": req.id,
            "full_name": req.full_name,
            "group_name": req.group_name,
            "supervisor": req.supervisor,
            "activity": req.activity,
            "file_name": req.file_name,
            "file_type": req.file_type,
            "file_content": req.file_content,
            "status": req.status,
            "created_at": req.created_at.isoformat()
        }
        for req in requests
    ]

@app.get("/api/admin/requests/approved")
def get_approved_requests(db: Session = Depends(get_db)):
    """Получение всех одобренных заявок"""
    requests = db.query(ActivityRequest).filter(
        ActivityRequest.status == "approved"
    ).order_by(ActivityRequest.created_at.desc()).all()
    
    return [
        {
            "id": req.id,
            "full_name": req.full_name,
            "group_name": req.group_name,
            "supervisor": req.supervisor,
            "activity": req.activity,
            "file_name": req.file_name,
            "file_type": req.file_type,
            "file_content": req.file_content,
            "status": req.status,
            "created_at": req.created_at.isoformat()
        }
        for req in requests
    ]

@app.put("/api/admin/requests/{request_id}")
def update_request_status(
    request_id: int, 
    status_update: UpdateStatus, 
    db: Session = Depends(get_db)
):
    """Обновление статуса заявки (одобрить/отклонить)"""
    request = db.query(ActivityRequest).filter(
        ActivityRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if status_update.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Неверный статус")
    
    request.status = status_update.status
    db.commit()
    
    return {"message": f"Заявка {status_update.status}"}

@app.delete("/api/admin/requests/{request_id}")
def delete_request(request_id: int, db: Session = Depends(get_db)):
    """Удаление заявки"""
    request = db.query(ActivityRequest).filter(
        ActivityRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    db.delete(request)
    db.commit()
    
    return {"message": "Заявка удалена"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)