import json

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, computed_field, field_validator

app = FastAPI()

"""
CORS: CROSS ORIGIN RESOURCE SHARING
    UseCase:
        1. Allow frontend to access the backend.
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

"""
HTTP method:
1. GET : to show or display any message on the website or the page or on the application
"""


@app.get("/")  # this "/" ensures that the output will show at home page
def greet():
    return {"message": "Dark lord has kidnapped your mom"}


@app.get("/hello")
def hello():
    return {"message": "The dark lord has said hi to your mom"}


"""
Helper function: 1
"""


# read the `students.json` and load it
def load_data():
    with open("./src/api_practicals/students.json", "r") as file:
        return json.load(file)


"""
Helper Function: 2
"""


# write the `studetns.json` and dump it
def save_data(data: dict[str, dict[str, str | float | int]]):
    with open("./src/api_practicals/students.json", "w") as file:
        return json.dump(data, file, indent=4)


@app.get("/student")
def student():
    return load_data()


"""
Path Parameter
"""


@app.get("/student/{student_id}")
def get_id(
    student_id: str = Path(
        ..., description="The id of the student", examples=["S1001", "S1002"]
    ),
):  # `Path` with `...` (or you can set a default value) defines that you have to pass a value, otherwise it won't work
    data = load_data()

    if student_id not in data:
        raise HTTPException(
            status_code=404, detail=f"Student with id {student_id} not found!"
        )

    return data[student_id]


"""
Query Parameter
"""


@app.get("/filter")
def filter_student(
    course: str | None = Query(
        default=None,
        description="Show the student enrolled in this course",
        examples=["Python", "Data Science"],
    ),  # course: python, Data Science
    age_limit_upper: int | None = Query(
        default=None, description="Set the upper limit of age", gt=1, le=99
    ),
    age_limit_lower: int | None = Query(
        default=None, description="Set the lower limit of age", gt=0, le=100
    ),
) -> dict[str, dict[str, str | int | float]]:
    if (
        age_limit_upper is not None
        and age_limit_lower is not None
        and age_limit_upper <= age_limit_lower
    ):
        age_limit_lower = 0

    data = load_data()
    filtered: dict[str, dict[str, str | int | float]] = {}

    for student_id, info in data.items():
        # This block will skip all the students who don't fit the required condition
        if course is not None and info["course"].casefold() != course.casefold():
            continue
        if age_limit_lower is not None and info["age"] < age_limit_lower:
            continue
        if age_limit_upper is not None and info["age"] > age_limit_upper:
            continue
        filtered[student_id] = info

    return filtered


SORT_FIELDS = ["gpa", "name", "age"]
SORT_ORDER = ["asc", "desc"]


@app.get("/sort")
def sort_students(
    sort_by: str = Query(
        None, description="Sort students by gpa, name, age", examples=["marks"]
    ),
    order: str = Query("asc", description="Select ordering", examples=["asc", "desc"]),
) -> list[dict[str, str | int | float]]:

    # if the give sort_by input doesn't belongs to any (gpa, name, age), we will raise an error
    if sort_by not in SORT_FIELDS:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid sort by {sort_by}, Choose from {SORT_FIELDS}",
        )

    # if the give order input doesn't belongs to any (asc, desc), we will raise an error
    if order not in SORT_ORDER:
        raise HTTPException(
            status_code=404, detail=f"Invalid order {order}. Choose from {SORT_ORDER}"
        )

    data = load_data()

    # 1. put the student info dictionary in the student list, making it easy to sort

    student: list[dict[str, str | int | float]] = []
    for student_id, info in data.items():
        # we need this student_id for diplaying purposes
        info["id"] = student_id
        student.append(info)

    # 2. sort the list by choose field
    reverse = order == "desc"  # order: bool = asc -> reverse = False
    sorted_students = sorted(student, key=lambda s: s[sort_by], reverse=reverse)

    return sorted_students


"""
PAGINATION

http://127.0.0.1:8000/paginate?page=1&limit=2

page -> which page you want
limit -> how many students(records) on one page

Formula:
start = page - 1 * limit
end = start * limit
"""


@app.get("/paginate")
def paginate_student(
    page: int = Query(1, ge=1, description="Which page you want(start from 1)"),
    limit: int = Query(
        2,
        ge=1,
        le=100,
        description="How many student records you want to see on one page?(start from 1)",
    ),
) -> dict[str, int | list[dict[str, str | int | float]]]:
    data = load_data()

    # put the student info dictionary in the student list, making it easy to sort

    student: list[dict[str, str | int | float]] = []
    for student_id, info in data.items():
        # we need this student_id for diplaying purposes
        info["id"] = student_id
        student.append(info)

    start = (page - 1) * limit
    end = page * limit

    page_student = student[start:end]
    total_student = len(student)

    return {
        "page": page,
        "limit": limit,
        "total_students": total_student,
        "students": page_student,
    }


"""
REQUEST BODY

    POST -> Data comes in the BODY (a json object sent to the server)

    When a function argument is a pydantic model, FastAPI reads it from the body and validates automatically, Bad Data: 422
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
        if self.gpa == 4.0:
            return "S"
        elif self.gpa >= 3.5:
            return "A+"
        elif self.gpa >= 3.0:
            return "A"
        elif self.gpa >= 2.5:
            return "B"
        elif self.gpa >= 2.0:
            return "C"
        else:
            return "F"


@app.post("/create", status_code=201)
def create_student(student: Student) -> dict[str, str | Student]:
    # 1. load the json file into the ram
    data = load_data()

    if student.id in data:
        raise HTTPException(
            status_code=400,
            detail=f"Student with id {student.id} is already present. Try another id.",
        )
    # 2. write the into the json file in the ram
    data[student.id] = student.model_dump(exclude={"id", "grade"})

    # 3. dumps the whole file into the ram
    save_data(data)

    return {"message": "Student created succesfully", "student": student}


"""
PUT
"""


class StudentUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50)
    age: int | None = Field(None, gt=0, lt=100)
    course: str | None = Field(None, max_length=50)
    gpa: float | None = Field(None, ge=0, le=4.0)
    email: EmailStr | None = None


@app.put("/update/{student_id}", status_code=201)  # `student_id` is path parameter
def update_student(
    student_update: StudentUpdate,
    student_id: str = Path(
        ..., description="The id of the student", examples=["S1001"]
    ),
) -> dict[str, str | Student]:

    # load the existing data
    data = load_data()

    # check if the user had correct `student_id`
    if student_id not in data:
        raise HTTPException(
            status_code=404, detail=f"Student id: {student_id} not found!"
        )

    # 1. fetch the data of a the student(`student_id`) from json
    existing = data[student_id]

    # 2. fetch the new data into a dictionary
    update = student_update.model_dump(
        exclude_unset=True
    )  # `exclude_unset` ensures that change only the field that are changed by the user

    # 3. replace the values of the old data with the new ones
    for key, value in update.items():
        existing[key] = value

    # 4. validate the student schema
    student = Student(id=student_id, **existing)

    # 5. convert the `Student` class in the dictionary
    data[student_id] = student.model_dump(exclude={"id", "grade"})

    # 6. save the dictionary file into json
    save_data(data)

    return {"message": "Student data updated succesfully", "student": student}


"""
DELETE
"""


@app.delete("/student_id/{student_id}", status_code=201)
def delete_student(
    student_id: str = Path(
        ..., description="The id of the student", examples=["S1001"]
    ),
) -> dict[str, str]:

    # load the existing data
    data = load_data()

    # validate if we have the exact `student_id` in our data
    if student_id not in data:
        raise HTTPException(
            status_code=404,
            detail=f"There is no student with the id: {student_id} in our system",
        )

    # delete the data
    del data[student_id]  # data["S1001"]
    save_data(data)

    return {
        "message": f"The student with id: {student_id} has been deleted from our system"
    }
