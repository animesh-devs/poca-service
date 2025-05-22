from typing import Dict, Any, List, Optional, Type
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Customize the OpenAPI schema to include the standard response format.
    
    Args:
        app: The FastAPI application
        
    Returns:
        The customized OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add the standard response format to all endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                # Skip endpoints that already have a custom response
                if "responses" in openapi_schema["paths"][path][method]:
                    for status_code in openapi_schema["paths"][path][method]["responses"]:
                        response = openapi_schema["paths"][path][method]["responses"][status_code]
                        if "content" in response and "application/json" in response["content"]:
                            # Wrap the response schema in the standard format
                            original_schema = response["content"]["application/json"]["schema"]
                            
                            # Create the standard response schema
                            standard_schema = {
                                "type": "object",
                                "properties": {
                                    "status_code": {
                                        "type": "integer",
                                        "description": "HTTP status code"
                                    },
                                    "status": {
                                        "type": "boolean",
                                        "description": "Success status"
                                    },
                                    "message": {
                                        "type": "string",
                                        "description": "Response message"
                                    },
                                    "data": original_schema
                                },
                                "required": ["status_code", "status", "message", "data"]
                            }
                            
                            # Update the response schema
                            response["content"]["application/json"]["schema"] = standard_schema
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
