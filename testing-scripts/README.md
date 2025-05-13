# POCA Service Testing Scripts

This directory contains scripts for testing the POCA service.

## Scripts

### 1. `direct_signup.py`

This script creates test data by directly using the signup endpoints. It creates:

- 2 hospitals
- 4 doctors
- 6 patients

**Usage:**

```bash
python3 direct_signup.py
```

### 2. `create_test_data.py`

This script creates test data using the API helper functions. It attempts to create:

- 2 hospitals
- 4 doctors
- 6 patients
- Maps doctors to patients
- Creates chats between doctors and patients

**Usage:**

```bash
python3 create_test_data.py
```

### 3. `test_auth_flow.py`

This script tests the authentication flow of the POCA service by creating users and logging in.

**Usage:**

```bash
python3 test_auth_flow.py
```

### 4. `test_api_flow_direct.py`

This script tests all the flows of the POCA service by hitting actual APIs in non-docker flow. It uses direct signup endpoints to create test data.

**Usage:**

```bash
python3 test_api_flow_direct.py
```

### 5. `test_docker_flow_direct.py`

This script tests all the flows of the POCA service by hitting actual APIs in docker flow. It uses direct signup endpoints to create test data.

**Usage:**

```bash
python3 test_docker_flow_direct.py
```

### 6. `api_helpers.py`

This file contains helper functions for making API calls to the POCA service. These functions are used by the test scripts to interact with the service.

## Test Data

The test data includes:

### Hospitals
- General Hospital
- City Medical Center

### Doctors
- Dr. John Smith (Cardiology)
- Dr. Sarah Johnson (Neurology)
- Dr. Michael Brown (Pediatrics)
- Dr. Emily Davis (Dermatology)

### Patients
- Alice Williams (35, female)
- Bob Johnson (45, male)
- Charlie Brown (28, male)
- Diana Miller (52, female)
- Ethan Davis (8, male)
- Fiona Wilson (15, female)

## Notes

- The `direct_signup.py` script is the recommended way to create test data as it uses the signup endpoints directly.
- The `create_test_data.py` script may not work correctly if the API endpoints change.
- All users have simple passwords for testing purposes:
  - Hospitals: `hospital123`
  - Doctors: `doctor123`
  - Patients: `patient123`
