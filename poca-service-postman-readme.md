# POCA Service Postman Collection

This repository contains a Postman collection for testing the POCA Service API. The collection includes all available endpoints organized by category, with pre-configured requests and environment variables.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [API Categories](#api-categories)
- [Environment Variables](#environment-variables)
- [Testing Tips](#testing-tips)

## Prerequisites

- [Postman](https://www.postman.com/downloads/) installed on your machine
- POCA Service running locally or on a remote server

## Installation

1. Open Postman
2. Click on "Import" in the top left corner
3. Select the `poca-service-postman-collection.json` file
4. The collection will be imported into your Postman workspace

## Configuration

Before using the collection, you need to configure the base URL:

1. Click on the "POCA Service API" collection
2. Go to the "Variables" tab
3. Set the value for `baseUrl` to match your API endpoint (default: `http://localhost:8000/api/v1`)
4. Click "Save"

## Authentication

The collection includes authentication endpoints and automatically manages your authentication tokens:

1. Use the "Login" request in the Authentication folder to get an access token
2. The response will include `access_token` and `refresh_token`
3. Copy these values to the collection variables `authToken` and `refreshToken`
4. All other requests will automatically use the `authToken` for authentication
5. If your token expires, use the "Refresh Token" request to get a new access token

## API Categories

The collection is organized into the following categories:

1. **Authentication**
   - Login, Refresh Token

2. **Hospitals**
   - Get All Hospitals, Get Hospital by ID

3. **Patients**
   - Get Patient Case History, Create Patient Case History, Update Patient Case History, Get Patient Documents

4. **AI Assistant**
   - Chat with AI

## Environment Variables

The collection uses the following variables:

- `baseUrl`: Base URL for the API (e.g., `http://localhost:8000/api/v1`)
- `authToken`: Authentication token for API requests
- `refreshToken`: Refresh token for renewing the authentication token
- `hospitalId`: ID of a hospital
- `patientId`: ID of a patient

## Testing Tips

1. **Sequential Testing**:
   - Start with Authentication (login)
   - Test hospital endpoints
   - Test patient endpoints
   - Test AI assistant endpoints

2. **Token Management**:
   - The collection automatically manages your authentication token
   - If you get 401 Unauthorized errors, try the "Refresh Token" request

3. **ID Variables**:
   - After creating resources (hospitals, patients), manually set the ID variables in the collection
   - This allows other requests to reference these resources

4. **Error Handling**:
   - Check the response body for detailed error messages
   - The API returns standardized error responses with error codes and messages
