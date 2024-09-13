from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from . import models, schemas, auth
from .database import get_db

router = APIRouter()

def ensure_owner_role(db: Session, org_id: int):
    owner_role = db.query(models.Role).filter(models.Role.name == 'Owner').first()
    if not owner_role:
        new_role = models.Role(name='Owner', description='Organisation Owner', org_id=org_id)
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        return new_role
    return owner_role

@router.post('/signup', response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_org = models.Organisation(name=user.org_name, status=0)
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    owner_role = ensure_owner_role(db, new_org.id)
    if not owner_role:
        raise HTTPException(status_code=500, detail="Error creating 'Owner' role")

    new_member = models.Member(org_id=new_org.id, user_id=new_user.id, role_id=owner_role.id)
    db.add(new_member)
    db.commit()

    return schemas.UserResponse(
        id=new_user.id,
        email=new_user.email,
        profile=new_user.profile,
        status=new_user.status,
        settings=new_user.settings,  
        created_at=int(new_user.created_at.timestamp()) if new_user.created_at else None,
        updated_at=int(new_user.updated_at.timestamp()) if new_user.updated_at else None
    )

@router.post('/signin', response_model=schemas.Token)
def signin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/reset-password")
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Password reset email sent"}

@router.post("/reset-password-confirm")
def reset_password_confirm(body: schemas.ResetPasswordConfirm, db: Session = Depends(get_db)):
    reset_token = db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token == body.token).first()
    if not reset_token:
        raise HTTPException(status_code=404, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = auth.get_password_hash(body.new_password)
    user.password = hashed_password
    db.delete(reset_token)  
    db.commit()

    return {"message": "Password has been reset"}

@router.post("/invite-member")
def invite_member(org_id: int, email: str, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    

    return {"message": "Invitation sent"}

@router.delete("/delete-member/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db.delete(member)
    db.commit()

    return {"message": "Member removed"}

@router.put("/update-member-role/{member_id}")
def update_member_role(member_id: int, new_role: str, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    role = db.query(models.Role).filter(models.Role.name == new_role).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    member.role_id = role.id
    db.commit()

    return {"message": "Member role updated"}

@router.get("/some-protected-route", response_model=schemas.UserResponse)
def protected_route(user: schemas.UserResponse = Depends(auth.get_current_user)):
    return {"message": "This is a protected route"}
