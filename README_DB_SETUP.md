# Database Setup and Test Data Creation

This document explains how to clean up the database and create test data for the POCA Service application.

## Available Scripts

The project includes several scripts for database initialization:

1. **init_db.py**: Creates the database tables and a default admin user.
2. **init_test_db.py**: Creates test data with a predefined set of users and relationships.
3. **simple_init_db.py**: Creates a minimal set of test data.
4. **clean_db_create_test_data.py**: Cleans the database and creates comprehensive test data.

## Cleaning the Database and Creating Test Data

### Using clean_db_create_test_data.py (Recommended)

This script provides the most comprehensive test data setup:

```bash
# Run the script
python3 ./clean_db_create_test_data.py
```

This script will:
1. Drop all existing tables
2. Create new tables
3. Create test data with:
   - 1 admin user
   - 2 hospitals
   - 5 doctors (with different specialties)
   - 4 patient users, each with 2-3 patients
   - Appropriate mappings between entities
   - Chat sessions between doctors and patients

The script will output all the credentials for the created users.

### Using init_test_db.py

```bash
# Remove the existing database file (optional)
rm app.db

# Run the script
python3 ./testing-scripts/init_test_db.py

# Or use the shell script
./init_test_db.sh
```

This script creates a predefined set of test data with:
- 1 hospital
- 2 doctors
- 2 patients
- Appropriate mappings

### Using simple_init_db.py

```bash
# Remove the existing database file (optional)
rm app.db

# Run the script
python3 ./simple_init_db.py
```

This script creates a minimal set of test data with:
- 1 admin user
- 1 hospital
- 1 doctor
- 1 patient
- Appropriate mappings

## Test Data Structure

The `clean_db_create_test_data.py` script creates the following test data:

### Admin User
- Email: admin@example.com
- Password: admin123

### Hospitals
- Hospital 1:
  - Email: hospital1@example.com
  - Password: hospital1
- Hospital 2:
  - Email: hospital2@example.com
  - Password: hospital2

### Doctors
- Doctor 1 (Cardiologist):
  - Email: doctor1@example.com
  - Password: doctor1
- Doctor 2 (Neurologist):
  - Email: doctor2@example.com
  - Password: doctor2
- Doctor 3 (Pediatrician):
  - Email: doctor3@example.com
  - Password: doctor3
- Doctor 4 (Orthopedic Surgeon):
  - Email: doctor4@example.com
  - Password: doctor4
- Doctor 5 (General Practitioner):
  - Email: doctor5@example.com
  - Password: doctor5

### Patients
- Patient User 1:
  - Email: patient1@example.com
  - Password: patient1
  - Associated Patients: 2-3 patients with different relationships
- Patient User 2:
  - Email: patient2@example.com
  - Password: patient2
  - Associated Patients: 2-3 patients with different relationships
- Patient User 3:
  - Email: patient3@example.com
  - Password: patient3
  - Associated Patients: 2-3 patients with different relationships
- Patient User 4:
  - Email: patient4@example.com
  - Password: patient4
  - Associated Patients: 2-3 patients with different relationships

## Customizing Test Data

If you need to customize the test data, you can modify the `clean_db_create_test_data.py` script. The script is well-commented and organized into sections for creating different types of entities.

## Database Configuration

The database URL is configured in `app/config.py`. By default, it uses SQLite with the file `app.db` in the project root directory.

If you need to change the database configuration, you can set the `DATABASE_URL` environment variable or modify the `app/config.py` file.
