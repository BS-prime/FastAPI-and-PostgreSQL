import os
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Query
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
)
from sqlalchemy import Column, Integer, String, create_engine, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ==============================================================================
# --- Phase I: Database
# ==============================================================================

"""
part 1: load DATABASE_URL from the .env file
"""
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

"""
Part 2: Create the engine (connection to PostgreSQL)
"""
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    version = conn.execute(text("SELECT version()")).scalar()
    print(f"Connected from python to postgresql: {version.split(',')[0]}")

"""
part 3: Create SessionLocal 
"""
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

"""
Part 4: Create Base for creating Tables inside the Database
"""


class Base(DeclarativeBase): ...


class StudentDB(Base):
    __tablename__ = "student_records"
    id = Column(String, primary_key=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    course = Column(String(50), nullable=False)
    marks = Column(Integer, nullable=False)
    email = Column(String, unique=True, nullable=False)


Base.metadata.create_all(
    bind=engine
)  # bind = engine -> Create the table inside This Database
print("Table ready")

# ==============================================================================
# --- Phase II: Schemas
# ==============================================================================

"""
Part 5: Pydantic schemas for input (StudentCreate, StudentUpdate)
"""


class StudentCreate(BaseModel):
    id: str = Field(..., examples=["S001", "S002"])
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., gt=0, le=100)
    email: EmailStr
    course: str = Field(..., min_length=3, max_length=50)
    marks: int = Field(..., ge=0, le=100)

    # create a custom validator
    @field_validator("name")
    @classmethod
    def check_name(cls, value: Any):
        if not value.replace(" ", "").isalpha():
            raise HTTPException("Numbers are not allowed in the field name")

        return value.title()  # e.g.: Varun varma -> Varun Verma


class StudentUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50)
    age: int | None = Field(None, gt=0, le=100)
    email: EmailStr | None = None
    course: str = Field(None, min_length=3, max_length=50)
    marks: int = Field(None, ge=0, le=100)

    # create a custom validator
    @field_validator("name")
    @classmethod
    def check_name(cls, value: Any):
        if not value.replace(" ", "").isalpha():
            raise HTTPException("Numbers are not allowed in the field name")

        return value.title()


"""
Part 6: Pydantic Schemas for Output (StudentResponse, StudentPage, Message)
"""


class StudentResponse(StudentCreate):
    # `from_attributes = True` lets pydantic read a dictionary or json like an object students.marks (an object), we are converting the dictionary to a object because then we can do `self.mark` to calculate grade with dictionary we can't access the marks that way.

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def grade(self) -> str:
        if self.marks >= 90:
            return "S"
        elif self.marks >= 80:
            return "A"
        elif self.marks >= 70:
            return "B"
        elif self.marks >= 60:
            return "C"
        elif self.marks >= 50:
            return "D"
        else:
            return "F"


"""
Part 7: get_db() - One Session per request

Opens a session, gives it to the endpoint, always closes it replace the load_data / save_data.

Opens a session, pauses at yield while the the endpoint perfroms it's did, once the endpoint has completed it's work the session will be closed.
"""


def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()


# ==============================================================================
# --- Phase III: API Endpoints
# ==============================================================================

"""
Part 8: Create the FastAPI app
"""
app = FastAPI()


"""
Step 9: Get one Student

Depends(get_db) before running this endpoint run get_db function and give me what it returns
"""


@app.get("/student/{student_id}", response_model=StudentResponse, tags=["get_route"])
def get_student(
    student_id: str = Path(..., description="The id of the student"),
    db: Session = Depends(get_db),
):
    """
    db.get is an orm operation which get us the, this is sql equivalent of

    ```sql
    SELECT
        *
    FROM
        StudentDB
    WHERE
        id = student_id;
    ```
    """
    student = db.get(StudentDB, student_id)
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student with id {student_id} is not in the database, recheck your id.",
        )

    return student


"""
Step 10: POST - Create a new Student
"""


@app.post(
    "/create_student",
    response_model=StudentResponse,
    status_code=201,
    tags=["post_routes"],
)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):

    # 1. check if the student is already in our database
    if db.get(StudentDB, student.id):
        raise HTTPException(
            status_code=400, detail=f"Student with id {student.id} is already exists."
        )

    # 2. Takes the incoming Pydantic student request, converts it to a regular dictionary with model_dump(), then uses ** to pass that dictionary’s fields as keyword arguments to create a SQLAlchemy StudentDB object.
    new_student = StudentDB(**student.model_dump())
    db.add(new_student)  # add on the local session not on the database

    # 3. Now saving the data from local session to Database
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Email {student.email} is already exist, try with a different email.",
        )

    db.refresh(new_student)
    return new_student


"""
Step 11: PUT - update a student
"""


@app.put("/update_student/{student_id}", tags=["put_route"])
def update_student(
    student_update: StudentUpdate,
    student_id: str = Path(..., description="The id of the student"),
):

    student = db.get(StudentDB, student_id)
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student with the the id {student_id} does not exists.",
        )

    changes = student_update.model_dump(
        exclude_unset=True
    )  # only send the attribute that are given

    for key, value in changes.items():
        setattr(student, key, value)  # setattr update the attributes of the student

    # 3. Now saving the data from local session to Database
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Email {student.email} is already exist, try with a different email.",
        )

    db.refresh(student)
    return student


"""
Part 12: DELETE - Delete any student record
"""


@app.delete("/delete_student/{student_id}", tags=["delete_route"])
def delete_student(student_id: str = Path(..., description="The id of the student")):

    student = db.get(StudentDB, student_id)

    if not student:
        raise HTTPException(
            status_code=404, detail=f"Student with id: {student_id} does not exists."
        )

    db.delete(student)
    db.commit()

    return {"message": f"Student with {student_id} has been deleted."}


"""
Part 13: Get all students (filter + sort + paginate)
"""
SORT_FIELDS = ["marks", "age", "name"]
SORT_ORDER = ["asc", "desc"]


@app.get("/students", tags=["get_route"])
def get_all(
    course: str | None = Query(
        None,
        description="show only the students that are appeared for this course",
        examples=["Python"],
    ),
    sort_by: str | None = Query(None, description="Sort by marks, age, or name"),
    order: str | None = Query(
        "asc",
        description="Sort the values by ascending or descending order",
        examples=["desc"],
    ),
    page: int | None = Query(1, ge=1, description="which page do you want"),
    limit: int | None = Query(
        2, ge=1, le=100, description="How many students you want to show on each paget"
    ),
    db: Session = Depends(get_db),
):
    if sort_by is not None and sort_by not in SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by {sort_by}, Choose from {SORT_FIELDS}",
        )

    if order is not None and order not in SORT_ORDER:
        raise HTTPException(
            status_code=400, detail=f"Invalid order {order}, Choose from {SORT_ORDER}"
        )

    query = db.query(StudentDB)  # SELECT * FROM student_records

    if course:
        query = query.filter(
            func.lower(StudentDB.course) == course.lower()
        )  # WHERE -> SELECT * FROM student_records WHERE course == "Python"

    total_student = query.count()

    if sort_by:
        column = getattr(StudentDB, sort_by)  # sort_by: "marks" -> StudentDB.marks

        if order == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    else:
        query = query.order_by(StudentDB.id)

    start = (page - 1) * limit
    student = query.offset(start).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total_students": total_student,
        "students": student,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
