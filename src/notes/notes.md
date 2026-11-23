# Build & Deploy a Real API(Pydantic + PostgreSQL + Docker)

## 1. What is API?

Answer: An API is an interface that defines how two pieces of software talk to each other. It also enforces constraints on how data is shared between those software pieces.

## 2. What is a server, and how is Uvicorn needed?

Answer: A server is a program that listens for incoming internet traffic (HTTP requests) from a client (like a browser or app) and sends back a response.

Uvicorn is a specialized web server designed for Python. By default, standard Python code cannot natively read raw internet traffic or open network sockets. Uvicorn acts as the vital translator between the outside world and your Python code:

1. Listening & Translating In: It listens on the internet, takes raw HTTP requests, and translates them into a standardized format (using the ASGI standard) that Python frameworks can easily understand.

2. Translating Out: Once your Python code processes the request and generates data, Uvicorn takes that response and converts it back into a valid HTTP packet to send back to the client.

## 3. What is an URL?

Answer: A URL is a address of a specific file, page, or resources on the internet.

## 4. What is an Endpoint?

Answer: An endpoint is a specific "destination" or "doorway" on a server where an API can receive requests and send back responses.

While a URL is the entire address of the website or server (e.g., [https://api.myrestaurant.com](https://api.myrestaurant.com)), an endpoint is the specific sub-path combined with an instruction that tells the server what you want to do (e.g., /menu, /orders, or /reservations)

## 5. What are http methods?

Answer: HTTP (Hypertext Transfer Protocol) is the core application-layer protocol that defines how data is requested, delivered, and exchanged between clients (such as web browsers) and servers on the World Wide Web(www).

1. GET: Use to show message on the website, or on the page, or on the application.(Read)
2. POST: Use to create anything(non-existing entity) on the website.(Create)
3. PUT: Use to update a particular thing on the wesite.(Update)
4. DELETE: Delete anything on the internet.(Delete)

## 6. What are the Status Codes?

Answer: You send the request, and the server gets the request. Now you have to know what the server has done with the request. Let's say you send the request. If you get nothing back, that is a problem. That's why we have a status code to inform us of the status of our request that we have just sent to the server.

[!![Status Codes](HTTP-Status-Codes-Cheat-Sheet.png)]

## 7. What is the Path Parameter?

Answer: A path parameter in FastAPI is a dynamic variable embedded directly inside a URL path to capture specific values and identify unique resources.

You declare path parameters using the same curly-brace {} syntax used in Python format strings. FastAPI extracts the value from the URL and passes it to your route function as an argument with the exact same name.

E.g., ```student_id``` in the following python code.

```python
@app.get("/student/{student_id}")
def get_id(
    student_id: str = Path(
        ..., description="The id of the student", examples=["S1001", "S1002"]
    ),
):  # class `Path` with `...` (or you can set a default value) defines that you have to pass a value, otherwise it won't work
    data = get_data()

    if student_id not in data:
        raise HTTPException(
            status_code=404, detail=f"Student with id {student_id} not found!"
        )

    return data[student_id]
```

## 8. What is Query Parameter?

Answer: A query parameter is a key-value pair added to the end of a URL that sends extra information to a web server. It lets you customize, filter, or sort a request without changing the main page or resource you are asking for.

## 9. What is Pagination?

Answer: It is the process to set how many number of values you have to show in a page.

## 10. What is the use of Pydantic?

Answer: Pydantic handle the data type validation.

## 11. What is a Request Body?

Answer: A request body is the part of an HTTP request that carries the actual data a client sends to a server.
