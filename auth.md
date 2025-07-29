# ODA Backend API - Authentication Documentation

## Overview
This documentation covers the authentication endpoints for the ODA Backend API. The system supports user registration with email/phone OTP verification, login, and token-based authentication.

## Base URL
```
http://localhost:8000/api/auth/
```

## Authentication Flow
1. **Register** → User creates account
2. **Verify OTP** → User verifies email/phone with OTP code
3. **Login** → User authenticates and receives token
4. **Use Token** → Include token in subsequent API requests

---

## Endpoints

### 1. User Registration
**Endpoint:** `POST /api/auth/register/`  
**Description:** Register a new user account  
**Authentication:** Not required

#### Request Body
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "role": "consumer"
}
```

#### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | Unique username (150 chars max) |
| email | string | Yes | Valid email address |
| phone | string | Yes | Phone number (9-15 digits) |
| password | string | Yes | Strong password |
| password_confirm | string | Yes | Must match password |
| role | string | Yes | One of: `consumer`, `retailer`, `vendor`, `admin` |

#### Success Response (201 Created)
```json
{
    "message": "User registered successfully. Please verify your email and phone.",
    "user_id": 1,
    "email": "john@example.com",
    "phone": "+1234567890"
}
```

#### Error Response (400 Bad Request)
```json
{
    "email": ["A user with this email already exists."],
    "phone": ["A user with this phone number already exists."],
    "password": ["Passwords don't match."]
}
```

#### What Happens After Registration:
- OTP codes are generated for both email and phone
- Email OTP is sent to user's email (console in development)
- Phone OTP is logged (SMS integration needed for production)
- User must verify at least one contact method before login

---

### 2. OTP Verification
**Endpoint:** `POST /api/auth/verify-otp/`  
**Description:** Verify email or phone with OTP code  
**Authentication:** Not required

#### Request Body
```json
{
    "contact": "john@example.com",
    "otp_code": "123456",
    "otp_type": "email"
}
```

#### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| contact | string | Yes | Email address or phone number |
| otp_code | string | Yes | 6-digit OTP code |
| otp_type | string | Yes | Either `email` or `phone` |

#### Success Response (200 OK)
```json
{
    "message": "Email verified successfully"
}
```

#### Error Response (400 Bad Request)
```json
{
    "non_field_errors": ["Invalid OTP."]
}
```

```json
{
    "non_field_errors": ["OTP has expired."]
}
```

---

### 3. Resend OTP
**Endpoint:** `POST /api/auth/resend-otp/`  
**Description:** Request a new OTP code  
**Authentication:** Not required

#### Request Body
```json
{
    "contact": "john@example.com",
    "otp_type": "email"
}
```

#### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| contact | string | Yes | Email address or phone number |
| otp_type | string | Yes | Either `email` or `phone` |

#### Success Response (200 OK)
```json
{
    "message": "OTP sent to john@example.com"
}
```

#### Error Response (404 Not Found)
```json
{
    "error": "User not found"
}
```

---

### 4. User Login
**Endpoint:** `POST /api/auth/login/`  
**Description:** Authenticate user and receive access token  
**Authentication:** Not required

#### Request Body
```json
{
    "email_or_phone": "john@example.com",
    "password": "SecurePassword123!"
}
```

#### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email_or_phone | string | Yes | Email address or phone number |
| password | string | Yes | User's password |

#### Success Response (200 OK)
```json
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "role": "consumer",
        "is_email_verified": true,
        "is_phone_verified": false,
        "created_at": "2025-07-28T10:30:00Z"
    },
    "message": "Login successful"
}
```

#### Error Response (400 Bad Request)
```json
{
    "non_field_errors": ["Invalid credentials."]
}
```

#### Error Response (401 Unauthorized)
```json
{
    "error": "Please verify your email or phone number before logging in."
}
```

---

### 5. Refresh Token
**Endpoint:** `POST /api/auth/refresh/`  
**Description:** Generate a new authentication token  
**Authentication:** Required

#### Headers
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

#### Request Body
```json
{}
```

#### Success Response (200 OK)
```json
{
    "token": "new_token_here_abcd1234567890",
    "message": "Token refreshed successfully"
}
```

---

### 6. User Logout
**Endpoint:** `POST /api/auth/logout/`  
**Description:** Invalidate current authentication token  
**Authentication:** Required

#### Headers
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

#### Request Body
```json
{}
```

#### Success Response (200 OK)
```json
{
    "message": "Logout successful"
}
```

---

## Authentication Usage

### Including Token in Requests
After successful login, include the token in all subsequent API requests:

```http
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json
```

### Example with cURL
```bash
curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/vendors/business-profile/
```

---

## Example Workflow

### Complete Registration and Login Flow

#### 1. Register User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com", 
    "phone": "+1234567890",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "role": "consumer"
  }'
```

#### 2. Check Console for OTP (Development)
Look in your Django server console for the email OTP:
```
Your email verification code is: 123456
Phone OTP for +1234567890: 654321
```

#### 3. Verify Email OTP
```bash
curl -X POST http://localhost:8000/api/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "contact": "john@example.com",
    "otp_code": "123456",
    "otp_type": "email"
  }'
```

#### 4. Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_phone": "john@example.com",
    "password": "SecurePassword123!"
  }'
```

#### 5. Use Token for Authenticated Requests
```bash
curl -H "Authorization: Token YOUR_TOKEN_HERE" \
     http://localhost:8000/api/vendors/business-profile/
```

---

## User Roles

| Role | Description |
|------|-------------|
| `consumer` | Regular users who can browse and purchase |
| `retailer` | Retail business owners |
| `vendor` | Suppliers and vendors |
| `admin` | System administrators |

---

## Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 201 | Created successfully |
| 400 | Bad request / Validation error |
| 401 | Unauthorized |
| 404 | Not found |
| 500 | Internal server error |

---

## Email Configuration

### Development Mode
- Uses console backend
- OTP codes appear in Django server console
- No actual emails sent

### Production Mode
- Configure SMTP settings in `settings.py`
- Use Gmail App Password for security
- Real emails will be sent

---

## Notes

- OTP codes expire after 5 minutes
- Users must verify at least one contact method (email OR phone) to login
- Tokens are persistent until logout or refresh
- Phone OTP requires SMS service integration (not implemented yet)
- All passwords must meet Django's validation requirements

---

## Troubleshooting

### Common Issues

1. **"Invalid credentials"** - Check email/phone and password
2. **"OTP has expired"** - Request new OTP using resend endpoint
3. **"User not found"** - Check if registration was successful
4. **"Please verify email or phone"** - Complete OTP verification first

### Development Tips

- Check Django console for OTP codes during development
- Use Django admin to view user verification status
- Test with console email backend before switching to SMTP