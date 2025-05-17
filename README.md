# HouseHelpNetwork

India's First Peer-Verified Household Help Platform

## Overview

HouseHelpNetwork is a web application for connecting household helpers (maids, drivers) with homeowners in India. The platform allows homeowners to register helpers, share reviews, report incidents, and connect with other homeowners for verification.

## Features

- User registration and authentication
- Helper profile management
- Contract creation and management
- Review system for helpers
- Incident reporting
- Owner-to-owner connect system
- Admin dashboard for system management

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL
- Git

### Local Development Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd househelpnetwork
```

2. **Set up a virtual environment**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Create a .env file**

Copy the example environment file:

```bash
cp env.example .env
```

Update the `.env` file with your PostgreSQL credentials.

5. **Set up the database**

```bash
# Create the database and tables directly using SQL
python setup_db_direct.py
```

6. **Run the application**

```bash
python main.py
```

The application will be available at `http://localhost:5000`

## Project Structure

- `app.py` - Application factory and extensions
- `config.py` - Configuration settings
- `models.py` - Database models
- `routes.py` - Application routes
- `forms.py` - Form definitions
- `utils.py` - Utility functions
- `setup_database.py` - Database setup script
- `setup_db_direct.py` - Direct SQL database setup
- `main.py` - Application entry point

## Database

The application uses PostgreSQL and SQLAlchemy ORM. The database schema includes tables for:

- Users (homeowners)
- Owner profiles
- Helper profiles
- Contracts
- Reviews
- Incident reports
- And more

## License

[License information here] 