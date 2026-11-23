"""
Python will interact with PostgreSQL directly without any FastAPI endpoints or routes.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 1. Get Database url from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Create Engine - The road to the DataBase
"""
PostgreSQL method:
    1 .all() : returns all rows
    2 .first() : return only the first row
    3 .scaler() : return only the first value of the first row
"""


engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    version = conn.execute(text("SELECT version()")).scalar()
    print(f"Connected to {version.split(',')[0]}")


# 3. Define Schema for the database
"""
DeclarativeBase gives any class the power to create a table. To be precise python only understand objects and classes, and sql understand columns, rows, and table. It is a Python helper used to connect object-oriented Python code to relational database tables.

We create our own base once, and every table inherits from it. Like Pydantic : BaseModel gives any class to perform validation operations on tables.
"""


class Base(DeclarativeBase):
    """
    Any class that inherits from this base (commonly named Base) is automatically linked to a database table using its __tablename__ and column attributes.
    """

    pass


class StudentDB(Base):
    __tablename__ = "student_records"
    id = Column(String, primary_key=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    course = Column(String(50), nullable=False)
    marks = Column(Integer, nullable=False)
    email = Column(String, unique=True, nullable=False)


# bind = engine -> Attached to: Create the table inside This Database
Base.metadata.create_all(bind=engine)
print("Table ready")


# 4. Session = One Visit, Open, do work, commit, close
"""
You go to postgre, open it, do something, the close the connection.
"""
SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()

if not db.get(StudentDB, "S001"):
    db.add(
        StudentDB(
            id="S001",
            name="Aarav Sharma",
            age=25,
            course="Python",
            marks=80,
            email="aarav@example.com",
        )
    )
    db.commit()

# 4. read it back
# for i in db.query(StudentDB).all():  # .all() will return an object
#     print(i.id, i.name, i.age, i.course, i.marks, i.email)

# 5. Update
aarav = db.get(StudentDB, "S001")
aarav.marks = 90
aarav.course = "Django"
db.commit()
