# User Entity ID Header

## Overview

The `user-entity-id` header is a new addition to the API that simplifies permission checks and entity validation. It allows the client to specify which entity (doctor, patient, hospital) the user is operating as, which is particularly useful for users who may have multiple roles or entities associated with their account.

## Entity Relationships

The system has the following entity relationships:

1. **User-Doctor: 1:1 mapping**
   - Each doctor is associated with exactly one user account
   - The doctor's ID is stored in the user's `profile_id` field

2. **User-Patient: 1:n mapping**
   - A user can be associated with multiple patients (themselves, family members, etc.)
   - This relationship is managed through the `user_patient_relations` table
   - Each relation has a type (self, wife, husband, child, etc.)

3. **User-Hospital: 1:1 mapping**
   - Each hospital is associated with exactly one user account
   - The hospital's ID is stored in the user's `profile_id` field

## Purpose

In healthcare systems, users often have complex relationships with multiple entities. For example:
- A user might be associated with multiple patient profiles (for themselves and family members)
- A doctor might work at multiple hospitals
- An admin might need to act on behalf of different entities

The `user-entity-id` header allows the client to specify which entity the user is currently operating as, simplifying permission checks and reducing the need for complex lookups on the server side.

## Usage

### Header Format

Add the following header to your API requests:

```
user-entity-id: <entity_id>
```

Where `<entity_id>` is the ID of the entity (doctor, patient, hospital) that the user is operating as.

### Behavior

1. **If the header is provided**:
   - The server will validate that the user has permission to act as the specified entity
   - The entity ID will be used for permission checks against resources
   - If the user doesn't have permission to act as the specified entity, a 403 Forbidden error will be returned
   - For patients, the server will check the `user_patient_relations` table to verify the relationship

2. **If the header is not provided**:
   - For doctors and hospitals (1:1 relationships):
     - If the user has a `profile_id` set, that will be used
     - Otherwise, the server will look up the entity by `user_id`
   - For patients (1:n relationships):
     - The server will first try to find a "self" relation in the `user_patient_relations` table
     - If no "self" relation exists, it will use the first available patient relation
     - If no patient relation exists, a 403 Forbidden error will be returned
   - For admins:
     - The user's ID will be used as the entity ID
   - It's strongly recommended to include the header for better control and performance, especially for users with multiple patient relationships

### Examples

#### Doctor accessing a patient's chat

```
GET /api/v1/chats/123
Authorization: Bearer <token>
user-entity-id: doctor_456
```

This request specifies that the user is acting as the doctor with ID `doctor_456`. The server will check if this doctor has permission to access the chat with ID `123`. Since doctors have a 1:1 relationship with users, the server will verify that the doctor is associated with the authenticated user.

#### Patient accessing their own chat

```
GET /api/v1/chats/123
Authorization: Bearer <token>
user-entity-id: patient_789
```

This request specifies that the user is acting as the patient with ID `patient_789`. The server will check if this patient has permission to access the chat with ID `123`. Since users can have multiple patient relationships, the server will verify that the patient is related to the authenticated user through the `user_patient_relations` table.

#### User with multiple patient relationships

A user might be associated with multiple patients (themselves, spouse, children, etc.). The `user-entity-id` header allows the user to specify which patient they are acting as:

```
# User acting as themselves
GET /api/v1/chats/123
Authorization: Bearer <token>
user-entity-id: patient_self_123

# User acting as their child
GET /api/v1/chats/456
Authorization: Bearer <token>
user-entity-id: patient_child_456
```

#### Admin accessing any chat

```
GET /api/v1/chats/123
Authorization: Bearer <token>
user-entity-id: admin_001
```

Admins can access any chat, so the specific entity ID is less important, but still required for consistency.

## Benefits

1. **Simplified Permission Checks**: The server can directly compare the entity ID with resource IDs without complex lookups
2. **Reduced Database Queries**: Fewer queries are needed to determine the user's entity
3. **Support for Multi-Entity Users**: Users with multiple roles or entities can easily switch between them
4. **Consistent API Design**: All endpoints follow the same pattern for permission checks

## Implementation Notes

- The header is validated by the `get_user_entity_id` dependency
- If the header is missing, the dependency will attempt to determine the appropriate entity ID
- The dependency returns a validated entity ID that can be used directly in permission checks
