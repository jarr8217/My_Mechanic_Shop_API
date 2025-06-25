# Mechanic Shop API

This is a RESTful API for a Mechanic Shop, built with Flask, SQLAlchemy, Marshmallow, a## Automated Testing

- **Test Suite:**  
  All endpoints are covered by automated tests using Python's `unittest` framework.
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

## CI/CD Pipeline

This project includes a complete CI/CD pipeline using GitHub Actions:

### Continuous Integration
- **Automated Testing**: Tests run on every push to main/master branch
- **Multi-Environment Testing**: Tests run with Python 3.12 on Ubuntu
- **Dependency Management**: Automatic installation and verification of requirements

### Continuous Deployment
- **Automatic Deployment**: Successful tests trigger deployment to Render
- **Production Updates**: Live API updates automatically after code changes
- **Workflow File**: `.github/workflows/main.yaml`

### Pipeline Features
- Environment setup and dependency installation
- Comprehensive test execution
- Deployment to production on success
- Error reporting and debugging informationI provides endpoints for managing customers, mechanics, service tickets, and inventory, with robust authentication, authorization, rate limiting, and caching.

## Features
- **Customer, Mechanic, Service Ticket, and Inventory Management**: Full CRUD operations for all resources.
- **Authentication & Authorization**: JWT-based authentication for both customers and mechanics, with role-based access control (RBAC).
- **Rate Limiting**: Global and per-route rate limiting using Flask-Limiter.
- **Caching**: Response caching for improved performance using Flask-Caching.
- **Advanced Queries**: Search, pagination, and relationship management (e.g., assigning mechanics to tickets, adding/removing parts).
- **Many-to-Many & One-to-Many Relationships**: Proper SQLAlchemy models for complex relationships (e.g., mechanics <-> tickets, tickets <-> inventory parts).
- **Error Handling**: Consistent and informative error messages for all endpoints.
- **Cross-Origin Resource Sharing (CORS)**: Properly configured CORS support for frontend integration.
- **Production Deployment**: Configured for deployment on Render with PostgreSQL support.
- **CI/CD Pipeline**: Automated testing and deployment using GitHub Actions.

## Technologies Used
- Python 3.12
- Flask
- Flask-SQLAlchemy
- Flask-Marshmallow
- Flask-Limiter
- Flask-Caching
- Flask-CORS
- MySQL (Development)
- PostgreSQL (Production)
- PyJWT
- Marshmallow
- Gunicorn (Production Server)
- python-dotenv (Environment Variables)

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
python flask_app.py
```
- The API will be available at `http://localhost:5000`

## Production Deployment

This application is configured for deployment on [Render](https://render.com) with the following features:

### Live API
- **Production URL**: `https://my-mechanic-shop-api.onrender.com`
- **API Documentation**: `https://my-mechanic-shop-api.onrender.com/api/docs/`

### Deployment Configuration
- **Database**: PostgreSQL (automatically provisioned on Render)
- **Web Server**: Gunicorn with proper WSGI configuration
- **Environment Variables**: Configured via Render dashboard
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn flask_app:app`

### Environment Variables (Production)
Set these in your Render dashboard:
```env
SECRET_KEY=your_production_secret_key
SQLALCHEMY_DATABASE_URI=your_postgres_connection_string
CONFIG_NAME=ProductionConfig
```

## API Overview
- **Authentication**: `/auth/login` (customer), `/auth/mechanic_login` (mechanic)
- **Customers**: `/customers/` (CRUD, search, pagination)
- **Mechanics**: `/mechanics/` (CRUD, search, popular mechanics)
- **Service Tickets**: `/service_tickets/` (CRUD, assign/remove mechanics, add/remove parts)
- **Inventory**: `/inventory/` (CRUD)

## API Documentation

- **Interactive Docs (Local):**  
  The API is fully documented using Swagger/OpenAPI.
  - Visit [`/api/docs`](http://localhost:5000/api/docs) after running the app locally to view and interact with the API documentation.
  
- **Interactive Docs (Production):**  
  - Visit [`https://my-mechanic-shop-api.onrender.com/api/docs/`](https://my-mechanic-shop-api.onrender.com/api/docs/) to access the live API documentation.
  
- **Features:**
  - Every route includes path, method, parameters, request/response examples, and security requirements.
  - Test endpoints directly from the documentation interface.
  - JWT authentication testing capabilities.

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
- CORS properly configured for secure cross-origin requests.
- Environment variables used for sensitive configuration data.
- Production-ready configuration with separate development/testing/production environments.

## Project Structure
```
My-Mechanic-Shop/
├── app/
│   ├── blueprints/          # API route blueprints
│   │   ├── auth/           # Authentication routes
│   │   ├── customers/      # Customer management
│   │   ├── mechanics/      # Mechanic management
│   │   ├── inventory/      # Inventory management
│   │   └── service_tickets/ # Service ticket management
│   ├── static/             # Static files (Swagger docs)
│   ├── utils/              # Utility functions and decorators
│   ├── __init__.py         # App factory and configuration
│   ├── extensions.py       # Flask extensions initialization
│   └── models.py           # SQLAlchemy models
├── tests/                  # Unit tests for all blueprints
├── .github/workflows/      # CI/CD pipeline configuration
├── config.py              # Application configuration
├── flask_app.py           # Application entry point
└── requirements.txt       # Python dependencies
```

## Testing
- Use the included Postman collection (`My_Mechanic_Shop.postman_collection.json`) to test all endpoints.
- All endpoints have been tested for correct request/response handling and error cases.

## License
This project is for educational purposes.

---

**Author:** Jose A. Refoyo-Ron

---

Feel free to fork, modify, and use this project as a template for your own Flask REST APIs!



