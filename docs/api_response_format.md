# API Response Format

## Standard Response Format

All API responses in the POCA Service follow a standardized format:

```json
{
  "status_code": int,
  "status": bool,
  "message": string,
  "data": any
}
```

### Fields

- `status_code`: HTTP status code (e.g., 200, 201, 400, 401, 403, 404, 500)
- `status`: Boolean indicating success (`true`) or failure (`false`)
- `message`: Human-readable message about the response
- `data`: The actual response data, which can be any valid JSON value (object, array, string, number, boolean, or null)

## Success Response Examples

### Example 1: Login Response

```json
{
  "status_code": 200,
  "status": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": "72530021-8af3-43cc-bc26-38255c6ed17d",
    "role": "admin"
  }
}
```

### Example 2: Get User Profile Response

```json
{
  "status_code": 200,
  "status": true,
  "message": "successful",
  "data": {
    "id": "72530021-8af3-43cc-bc26-38255c6ed17d",
    "name": "Admin User",
    "email": "admin@example.com",
    "role": "admin",
    "contact": "+1234567890",
    "address": "123 Admin St, Adminville, USA",
    "created_at": "2023-05-01T12:00:00Z",
    "updated_at": "2023-05-01T12:00:00Z"
  }
}
```

### Example 3: Empty Response (204 No Content)

```json
{
  "status_code": 200,
  "status": true,
  "message": "Operation completed successfully",
  "data": null
}
```

## Error Response Examples

### Example 1: Authentication Error

```json
{
  "status_code": 401,
  "status": false,
  "message": "Incorrect email or password",
  "data": {
    "error_code": "AUTH_001",
    "details": {}
  }
}
```

### Example 2: Resource Not Found

```json
{
  "status_code": 404,
  "status": false,
  "message": "User not found",
  "data": {
    "error_code": "RES_001",
    "details": {}
  }
}
```

### Example 3: Validation Error

```json
{
  "status_code": 422,
  "status": false,
  "message": "Validation error",
  "data": {
    "error_code": "VAL_001",
    "details": {
      "errors": [
        {
          "loc": ["body", "email"],
          "msg": "value is not a valid email address",
          "type": "value_error.email"
        }
      ]
    }
  }
}
```

## Client Implementation

When implementing a client for this API, always check the `status` field to determine if the request was successful. If `status` is `true`, the `data` field contains the response data. If `status` is `false`, the `data` field contains error information.

### Example (JavaScript)

```javascript
async function fetchData(url) {
  try {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    const result = await response.json();
    
    if (result.status) {
      // Success case
      return result.data;
    } else {
      // Error case
      console.error(`Error: ${result.message}`);
      console.error(`Error code: ${result.data.error_code}`);
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}
```
