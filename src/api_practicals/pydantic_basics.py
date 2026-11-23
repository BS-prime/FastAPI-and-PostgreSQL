"""
PYDANTIC FOUNDATION
"""

"""
Step: 1 - The problem

    A normal dictionary accepts anything, and nobody checks the data
"""

bad_student: dict[str, int | str] = {
    "name": "",
    "age": "Twenty",
    "marks": 150,
    "email": "not-an-email",
}

# print(bad_student)

"""
Step: 2 - BASEMODEL + TYPE HINTS

    We describe a student ONCE. Python every student against it.
"""
from pydantic import BaseModel, EmailStr, Field, computed_field, field_validator


class SimpleStudent(BaseModel):
    name: str
    age: int
    marks: int


s = SimpleStudent(name="Bhargav Sharma", age="21", marks=80)
# print(s.name, s.age, s.marks)

"""
Step: 3 - Field() Rules

    gt = greater than
    ge = greater than or equal to

    lt = less than
    le = less than or equal to
"""


class RuleStudent(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)  # `...` = required
    age: int = Field(..., gt=0, lt=100)
    marks: int = Field(..., ge=0, le=100)
    course: str = "Python"
    phone: str | None = None


s = RuleStudent(name="Rohan Verma", age=21, marks=77)
# print(s.name, s.age, s.marks, s.course, s.phone)

"""
Step: 4 - EMAILSTR
    Check the text really look like an email
"""


class EmailStudent(BaseModel):
    name: str
    email: EmailStr


s = EmailStudent(name="Kavir Singh", email="kavirsingh@gmail.com")
# print(s.name, s.email)


"""
Step: 5 - FINAL STUDENT MODEL
    1. field_validator: When we want to set our own custom rule

"""


class Student(BaseModel):
    id: str = Field(..., examples=["S1001"])
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., gt=0, le=100)
    course: str = Field(..., max_length=50)
    gpa: float = Field(..., ge=0, le=4)
    email: EmailStr

    # custom rule: Name must contain only letters and spaces
    @field_validator("name")  # we are validating only the field name
    @classmethod
    def check_name(cls, value: str):  # value = "name"
        if not value.replace(" ", "").isalpha():
            raise ValueError("\n\nName must contain only letter and spaces\n\n")

        return value.title()

    @computed_field(return_type="str")
    @property
    def grade(self):
        if self.gpa >= 3.5:
            return "A+"
        elif self.gpa >= 3.0:
            return "A"
        elif self.gpa >= 2.5:
            return "B"
        elif self.gpa >= 2.0:
            return "C"
        else:
            return "F"


s = Student(
    id="S1001",
    name="aarav sharma",
    age=21,
    course="Data Science",
    gpa=3.2,
    email="aaravsharma@gmail.com",
)

# print(s.id, s.name, s.age, s.course, s.gpa, s.email, s.grade, sep="\n\n")

"""
STEP: 6 - MODEL_DUMP()

    turn a model back into Python dictinary; save it later
"""

data = s.model_dump()
# print(data)


"""
STEP: 7 - CHECK OUR REAL DATA(student.json)

    Every student in our field will go through the Student model
"""

import json

with open("./src/api_practicals/students.json", "r") as file:
    raw = json.load(file)

# print(raw)

for student_id, info in raw.items():
    s = Student(id=student_id, **info)
    print(s.id, s.name, s.grade, s.email, sep="\n", end="\n\n")
