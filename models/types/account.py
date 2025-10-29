import uuid
from pydantic import BaseModel, Field, EmailStr
from typing import List, Any, Dict
from functions.hash_password import hash_password

class AccountObject(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    username: str
    email: EmailStr | None = None
    password_hash: str | None = None
    optional_value: Dict[str, Any] | None = None


def NewUser(username: str, password: str, email: EmailStr | None = None) -> AccountObject:

    hashed_pw = hash_password(password)

    new_account = AccountObject(
        username=username,
        email=email,
        password_hash=hashed_pw
    )

    return new_account