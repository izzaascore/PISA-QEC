from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
import uuid

import models, schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="EduMaster API")

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Frontend static asset mounts
os.makedirs("static/teacher/assets", exist_ok=True)
os.makedirs("static/student/assets", exist_ok=True)
app.mount("/teacher/assets", StaticFiles(directory="static/teacher/assets"), name="teacher-assets")
app.mount("/student/assets", StaticFiles(directory="static/student/assets"), name="student-assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def serve_root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return RedirectResponse(url="/docs")

@app.get("/teacher", include_in_schema=False)
@app.get("/teacher/{full_path:path}", include_in_schema=False)
def serve_teacher(full_path: str = ""):
    file_path = os.path.join("static", "teacher", full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    teacher_index = os.path.join("static", "teacher", "index.html")
    if os.path.exists(teacher_index):
        return FileResponse(teacher_index)
    return RedirectResponse(url="/")

@app.get("/student", include_in_schema=False)
@app.get("/student/{full_path:path}", include_in_schema=False)
def serve_student(full_path: str = ""):
    file_path = os.path.join("static", "student", full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    student_index = os.path.join("static", "student", "index.html")
    if os.path.exists(student_index):
        return FileResponse(student_index)
    return RedirectResponse(url="/")



def init_db(db: Session):
    settings = db.query(models.Settings).first()
    if not settings:
        default_settings = models.Settings(
            name="Jasur O'qituvchi",
            email="jasur@edumaster.uz",
            password="admin", # Default password for teacher
            avatar_url="https://placehold.co/100x100/6366f1/ffffff?text=Teacher",
            logo_url="https://placehold.co/100x100/6366f1/ffffff?text=EM",
            theme="light"
        )
        db.add(default_settings)
        db.commit()

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    init_db(db)

# ========================================
# AUTH ENDPOINTS
# ========================================

@app.post("/api/auth/login")
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    # 1. Check if Teacher
    settings = db.query(models.Settings).first()
    # Let's say teacher username is always 'admin' or their email
    if (login_data.username == "admin" or login_data.username == settings.email) and login_data.password == settings.password:
        return {"role": "teacher", "id": 1, "name": settings.name}
    
    # 2. Check if Student
    student = db.query(models.Student).filter(models.Student.username == login_data.username, models.Student.password == login_data.password).first()
    if student:
        return {"role": "student", "id": student.id, "name": student.name}
        
    raise HTTPException(status_code=401, detail="Login yoki parol noto'g'ri")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join("uploads", filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/uploads/{filename}"}

# ========================================
# TEACHER PANEL ENDPOINTS
# ========================================

@app.get("/api/teacher/settings", response_model=schemas.Settings)
def get_settings(db: Session = Depends(get_db)):
    return db.query(models.Settings).first()

@app.put("/api/teacher/settings", response_model=schemas.Settings)
def update_settings(settings: schemas.SettingsBase, db: Session = Depends(get_db)):
    db_settings = db.query(models.Settings).first()
    if not db_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    db_settings.name = settings.name
    db_settings.email = settings.email
    db_settings.avatar_url = settings.avatar_url
    db_settings.logo_url = settings.logo_url
    db_settings.theme = settings.theme
    
    db.commit()
    db.refresh(db_settings)
    return db_settings

@app.get("/api/teacher/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    total_students = db.query(models.Student).count()
    active_groups = db.query(models.Group).count()
    total_blocks = db.query(models.Block).count()
    
    students = db.query(models.Student).all()
    avg_score = sum(s.score for s in students) / len(students) if students else 0

    return {
        "students": total_students,
        "groups": active_groups,
        "blocks": total_blocks,
        "avg_score": round(avg_score, 1)
    }

@app.get("/api/teacher/blocks", response_model=List[schemas.Block])
def get_blocks(db: Session = Depends(get_db)):
    return db.query(models.Block).order_by(models.Block.id.desc()).all()

@app.post("/api/teacher/blocks", response_model=schemas.Block)
def create_block(block: schemas.BlockCreate, db: Session = Depends(get_db)):
    db_block = models.Block(
        title=block.title,
        category=block.category,
        desc=block.desc,
        badge=block.badge,
        badge_class=block.badge_class
    )
    
    # Assign to groups
    if block.group_ids:
        groups = db.query(models.Group).filter(models.Group.id.in_(block.group_ids)).all()
        db_block.groups = groups

    db.add(db_block)
    db.commit()
    db.refresh(db_block)
    return db_block

@app.delete("/api/teacher/blocks/{block_id}")
def delete_block(block_id: int, db: Session = Depends(get_db)):
    db_block = db.query(models.Block).filter(models.Block.id == block_id).first()
    if not db_block:
        raise HTTPException(status_code=404, detail="Block not found")
    db.delete(db_block)
    db.commit()
    return {"message": "Block deleted successfully"}

@app.get("/api/teacher/groups", response_model=List[schemas.Group])
def get_groups(db: Session = Depends(get_db)):
    return db.query(models.Group).all()

@app.post("/api/teacher/groups", response_model=schemas.Group)
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    db_group = models.Group(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.post("/api/teacher/groups/{group_id}/students", response_model=schemas.Student)
def create_student_in_group(group_id: int, student: schemas.StudentCreate, db: Session = Depends(get_db)):
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # check if username exists
    existing = db.query(models.Student).filter(models.Student.username == student.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ushbu login allaqachon band")

    db_student = models.Student(**student.dict(), group_id=group_id)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.put("/api/teacher/students/{student_id}", response_model=schemas.Student)
def update_student_credentials(student_id: int, update_data: schemas.StudentUpdate, db: Session = Depends(get_db)):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if update_data.username != db_student.username:
        existing = db.query(models.Student).filter(models.Student.username == update_data.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ushbu login band")

    db_student.username = update_data.username
    db_student.password = update_data.password
    db.commit()
    db.refresh(db_student)
    return db_student

@app.get("/api/teacher/results", response_model=List[schemas.Student])
def get_results(db: Session = Depends(get_db)):
    return db.query(models.Student).order_by(models.Student.score.desc()).all()


# ========================================
# STUDENT PANEL ENDPOINTS
# ========================================

@app.get("/api/results/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    students = db.query(models.Student).order_by(models.Student.score.desc()).all()
    result = []
    for s in students:
        group_name = s.group.name if s.group else "Noma'lum"
        result.append({
            "id": s.id,
            "name": s.name,
            "initials": s.initials,
            "color": s.color,
            "score": s.score,
            "group_name": group_name
        })
    return result

@app.get("/api/student/{student_id}/dashboard")
def get_student_dashboard(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    group = student.group
    blocks_count = len(group.blocks) if group else 0
    
    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "score": student.score,
            "group_name": group.name if group else "Noma'lum"
        },
        "stats": {
            "active_blocks": blocks_count,
            "completed_tasks": 0,
            "total_score": student.score,
            "rank": 1 
        }
    }

@app.get("/api/student/{student_id}/blocks", response_model=List[schemas.Block])
def get_student_blocks(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if not student.group:
        return []
        
    return student.group.blocks

# ========================================
# TOPIC ENDPOINTS (SHARED & TEACHER)
# ========================================

@app.get("/api/blocks/{block_id}/topics", response_model=List[schemas.Topic])
def get_topics_for_block(block_id: int, db: Session = Depends(get_db)):
    block = db.query(models.Block).filter(models.Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    return db.query(models.Topic).filter(models.Topic.block_id == block_id).order_by(models.Topic.order_index).all()

@app.get("/api/topics/{topic_id}", response_model=schemas.Topic)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return db_topic

@app.post("/api/teacher/blocks/{block_id}/topics", response_model=schemas.Topic)
def create_topic(block_id: int, topic: schemas.TopicCreate, db: Session = Depends(get_db)):
    block = db.query(models.Block).filter(models.Block.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    db_topic = models.Topic(
        **topic.dict(),
        block_id=block_id
    )
    db.add(db_topic)
    
    # Update block's topic count
    block.topics = db.query(models.Topic).filter(models.Topic.block_id == block_id).count() + 1
    
    db.commit()
    db.refresh(db_topic)
    return db_topic

@app.put("/api/teacher/topics/{topic_id}", response_model=schemas.Topic)
def update_topic(topic_id: int, topic: schemas.TopicCreate, db: Session = Depends(get_db)):
    db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    for key, value in topic.dict().items():
        setattr(db_topic, key, value)
        
    db.commit()
    db.refresh(db_topic)
    return db_topic

@app.delete("/api/teacher/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    block = db_topic.block
    db.delete(db_topic)
    
    if block:
        block.topics = max(0, db.query(models.Topic).filter(models.Topic.block_id == block.id).count() - 1)
        
    db.commit()
    return {"message": "Topic deleted"}
