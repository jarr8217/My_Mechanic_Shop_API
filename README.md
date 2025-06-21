# Mechanic Shop API

This is a RESTful API for a Mechanic Shop, built with Flask, SQLAlchemy, Marshmallow, and MySQL. The API provides endpoints for managing customers, mechanics, service tickets, and inventory, with robust authentication, authorization, rate limiting, and caching.

## Features
- **Customer, Mechanic, Service Ticket, and Inventory Management**: Full CRUD operations for all resources.
- **Authentication & Authorization**: JWT-based authentication for both customers and mechanics, with role-based access control (RBAC).
- **Rate Limiting**: Global and per-route rate limiting using Flask-Limiter.
- **Caching**: Response caching for improved performance using Flask-Caching.
- **Advanced Queries**: Search, pagination, and relationship management (e.g., assigning mechanics to tickets, adding/removing parts).
- **Many-to-Many & One-to-Many Relationships**: Proper SQLAlchemy models for complex relationships (e.g., mechanics <-> tickets, tickets <-> inventory parts).
- **Error Handling**: Consistent and informative error messages for all endpoints.

## Technologies Used
- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Marshmallow
- Flask-Limiter
- Flask-Caching
- MySQL
- PyJWT
- Marshmallow

## Installation and Running
To set up and run the project locally:

### 1. Clone the Repository
```sh
git clone https://github.com/jarr8217/My_Mechanic_Shop_API.git
cd My-Mechanic-Shop
```

### 2. Set Up the Environment
- Create a `.env` file in the root directory with your secret key and database URL (see `.env.example` if provided).
- Example:
  ```env
  SECRET_KEY=your_secret_key
  DATABASE_URL=mysql+mysqlconnector://user:password@localhost:3306/mechanic_shop_db
  ```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Set Up the Database
- Ensure MySQL is running and the database exists.
- The app will auto-create tables on first run.

### 5. Run the Application
```sh
python app.py
```
- The API will be available at `http://localhost:5000`

## API Overview
- **Authentication**: `/auth/login` (customer), `/auth/mechanic_login` (mechanic)
- **Customers**: `/customers/` (CRUD, search, pagination)
- **Mechanics**: `/mechanics/` (CRUD, search, popular mechanics)
- **Service Tickets**: `/service_tickets/` (CRUD, assign/remove mechanics, add/remove parts)
- **Inventory**: `/inventory/` (CRUD)

## API Documentation

- **Interactive Docs:**  
  The API is fully documented using Swagger/OpenAPI.
  - Visit [`/swagger`](http://localhost:5000/swagger) or [`/docs`](http://localhost:5000/docs) after running the app to view and interact with the API documentation.
  - Every route includes path, method, parameters, request/response examples, and security requirements.

- **Spec File:**  
  The OpenAPI/Swagger spec is located at `app/static/swagger.yaml`.

## Automated Testing

- **Test Suite:**  
  All endpoints are covered by automated tests using Python’s `unittest` framework.
  - Tests are located in the `tests/` directory, with a separate file for each blueprint.
  - Both positive and negative cases are tested, including authentication, RBAC, and edge cases.

- **How to Run Tests:**  
  ```sh
  python -m unittest discover -v
  ```
  or simply
  ```sh
  python -m unittest
  ```
  from the project root.

## Security & Best Practices
- All sensitive routes are protected by JWT authentication and RBAC decorators.
- Rate limiting and caching are applied for security and performance.
- Error messages are consistent and informative.

## Testing
- Use the included Postman collection (`My_Mechanic_Shop.postman_collection.json`) to test all endpoints.
- All endpoints have been tested for correct request/response handling and error cases.

## License
This project is for educational purposes.

---

**Author:** Jose A. Refoyo-Ron

---

Feel free to fork, modify, and use this project as a template for your own Flask REST APIs!



