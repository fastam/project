# database.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Создаем движок для подключения к базе данных SQLite
engine = create_engine(
    "sqlite:///activity_registry.db", 
    echo=False,  # Отключаем вывод SQL-запросов в консоль
    connect_args={"check_same_thread": False}  # Для многопоточности
)

# Создаем базовый класс для всех моделей
Base = declarative_base()

# Создаем фабрику сессий для работы с базой
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# Модель для заявок на активность
class ActivityRequest(Base):
    __tablename__ = "activity_requests"
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)  # ФИО студента
    group_name = Column(String)  # Группа
    supervisor = Column(String)  # Руководитель
    activity = Column(String, nullable=False)  # Название активности
    file_name = Column(String)  # Имя файла
    file_content = Column(Text)  # Содержимое файла в base64
    file_type = Column(String)  # Тип файла
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)  # Дата создания

# Функция для инициализации базы данных
def init_db():
    # Создает таблицы в базе данных, если они еще не существуют
    Base.metadata.create_all(engine)

# Функция для получения сессии базы данных
def get_db():
    # Создает и возвращает сессию для работы с базой данных
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
