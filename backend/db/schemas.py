from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime, timezone, timedelta

# AUTH SCHEMAS
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class GoogleToken(BaseModel):
    token: str
    is_register: bool = False

# USER SCHEMAS
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    middle_initial: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    avatar_url: Optional[str] = None
    has_completed_tour: bool = False
    created_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    email: Optional[EmailStr] = None

# MEDICAL CONDITION SCHEMAS
class MedicalConditionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

# PROFILE SCHEMAS
class MedicalProfileBase(BaseModel):
    height_cm: float = Field(gt=0, allow_inf_nan=False)
    weight_kg: float = Field(gt=0, allow_inf_nan=False)
    target_weight_kg: float = Field(gt=0, allow_inf_nan=False)
    illnesses: Optional[str] = None
    allergies: Optional[str] = None

class MedicalProfileCreate(MedicalProfileBase):
    pass

class MedicalProfileResponse(MedicalProfileBase):
    id: str
    user_id: str
    bmi: float
    daily_calorie_goal: int
    
    class Config:
        orm_mode = True

# FOOD LOG SCHEMAS
class FoodLogBase(BaseModel):
    meal_type: str
    food_name: str
    calories: int = Field(ge=0)
    protein_g: float = Field(ge=0, allow_inf_nan=False)
    carbs_g: float = Field(ge=0, allow_inf_nan=False)
    fat_g: float = Field(ge=0, allow_inf_nan=False)
    vitamin_c_mg: Optional[float] = Field(default=0.0, ge=0, allow_inf_nan=False)
    calcium_mg: Optional[float] = Field(default=0.0, ge=0, allow_inf_nan=False)
    iron_mg: Optional[float] = Field(default=0.0, ge=0, allow_inf_nan=False)
    image_url: Optional[str] = None
    medical_caution: Optional[str] = None

class FoodLogCreate(FoodLogBase):
    eaten_at: Optional[datetime] = None

    @field_validator('eaten_at')
    @classmethod
    def validate_eaten_at(cls, value):
        if value is not None:
            if value.tzinfo is None:
                raise ValueError('Meal time must include a timezone.')
            if value > datetime.now(timezone.utc) + timedelta(minutes=5):
                raise ValueError('Meal time cannot be in the future.')
        return value

class FoodLogResponse(FoodLogBase):
    id: str
    user_id: str
    logged_at: datetime
    
    class Config:
        from_attributes = True

# WEIGHT HISTORY SCHEMAS
class WeightHistoryBase(BaseModel):
    weight_kg: float = Field(gt=0, allow_inf_nan=False)

class WeightHistoryCreate(WeightHistoryBase):
    pass

class WeightHistoryResponse(WeightHistoryBase):
    id: str
    user_id: str
    logged_at: datetime

    class Config:
        from_attributes = True

# PUSH SUBSCRIPTION SCHEMAS
class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str

class PushSubscriptionResponse(BaseModel):
    id: str
    user_id: str
    endpoint: str
    created_at: datetime

    class Config:
        from_attributes = True

# VERIFICATION SCHEMAS
class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str
