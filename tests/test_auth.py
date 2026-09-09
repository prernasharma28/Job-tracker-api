# Test user registration
def test_user_registration(client):
    response = client.post('/auth/register', json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"


# Test user login
def test_user_login(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "test@example.com",
        "password": "password123"
    })

    # Then, login with the registered user
    response = client.post('/auth/login', json={
        "email": "test@example.com",
        "password": "password123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


# Test user login with incorrect credentials
def test_user_login_incorrect_credentials(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "test@example.com",
        "password": "password123"
    })

    # Then, attempt to login with incorrect credentials
    response = client.post('/auth/login', json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password"


# Test user registration with an already registered email
def test_user_registration_existing_email(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "test@example.com",
        "password": "password123"
    })

    # Then, attempt to register the same user again
    response = client.post('/auth/register', json={
        "email": "test@example.com",
        "password": "password456"
    })

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Email already registered"


# Test user registration with invalid email format
def test_user_registration_invalid_email(client):
    response = client.post('/auth/register', json={
        "email": "invalid-email",
        "password": "password123"
    })

    assert response.status_code == 422  # Unprocessable Entity


# Test user registration with a duplicate email
def test_duplicate_registration(client):
    # First registration
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 201

    # Second registration with same email
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 400


# Test accessing protected applications endpoint without authentication
def test_get_applications_without_token(client):
    response = client.get("/applications")

    assert response.status_code == 401


# Test accessing protected applications endpoint with a valid access token
def test_get_applications_with_token(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "protected@example.com",
        "password": "password123"
    })

    # Then, login to get an access token
    login_response = client.post('/auth/login', json={
        "email": "protected@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Use the access token to access the protected endpoint
    response = client.get(
        "/applications",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200


# Test accessing protected applications endpoint with an invalid access token
def test_get_applications_with_invalid_token(client):
    # Use an invalid access token
    response = client.get(
        "/applications",
        headers={
            "Authorization": "Bearer invalid-token"
        }
    )

    assert response.status_code == 401


# Test refreshing an access token using a valid refresh token
def test_refresh_token(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "refresh@example.com",
        "password": "password123"
    })

    # Then, login to get access and refresh tokens
    login_response = client.post('/auth/login', json={
        "email": "refresh@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    data = login_response.json()

    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Use the refresh token to get a new access token
    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token
        }
    )

    assert refresh_response.status_code == 200

    refresh_data = refresh_response.json()

    assert "access_token" in refresh_data
    assert refresh_data["access_token"]
    assert refresh_data["token_type"] == "bearer"


# Test that a revoked refresh token cannot be used after logout
def test_logout_revokes_refresh_token(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "logout@example.com",
        "password": "password123"
    })

    # Then, login to get access and refresh tokens
    login_response = client.post('/auth/login', json={
        "email": "logout@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    data = login_response.json()

    refresh_token = data["refresh_token"]

    # Logout using the refresh token
    logout_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token
        }
    )

    assert logout_response.status_code == 200

    # Try to use the revoked refresh token
    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token
        }
    )

    assert refresh_response.status_code == 401


# Test that an access token cannot be used as a refresh token
def test_access_token_cannot_be_used_as_refresh_token(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "token-type@example.com",
        "password": "password123"
    })

    # Then, login to get an access token
    login_response = client.post('/auth/login', json={
        "email": "token-type@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Try to use the access token as a refresh token
    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": access_token
        }
    )

    assert refresh_response.status_code == 401


# Test creating an application with a valid access token
def test_create_application_with_token(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "application@example.com",
        "password": "password123"
    })

    # Then, login to get an access token
    login_response = client.post('/auth/login', json={
        "email": "application@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Create an application using the access token
    response = client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "company": "Google",
            "role": "Software Engineer",
            "status": "Applied"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["company"] == "Google"
    assert data["role"] == "Software Engineer"
    assert data["status"] == "Applied"


# Test that a user cannot access another user's application
def test_user_cannot_access_another_users_application(client):
    # First, register the first user
    client.post('/auth/register', json={
        "email": "user1@example.com",
        "password": "password123"
    })

    # Login as the first user
    login_response = client.post('/auth/login', json={
        "email": "user1@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    user1_token = login_response.json()["access_token"]

    # Create an application for the first user
    create_response = client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
        json={
            "company": "Google",
            "role": "Software Engineer",
            "status": "Applied"
        }
    )

    assert create_response.status_code == 201

    application_id = create_response.json()["id"]

    # Register the second user
    client.post('/auth/register', json={
        "email": "user2@example.com",
        "password": "password123"
    })

    # Login as the second user
    login_response = client.post('/auth/login', json={
        "email": "user2@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    user2_token = login_response.json()["access_token"]

    # Try to access the first user's application
    response = client.get(
        f"/applications/{application_id}",
        headers={
            "Authorization": f"Bearer {user2_token}"
        }
    )

    assert response.status_code == 404


# Test that a user cannot update another user's application
def test_user_cannot_update_another_users_application(client):
    # First, register the first user
    client.post('/auth/register', json={
        "email": "updateuser1@example.com",
        "password": "password123"
    })

    # Login as the first user
    login_response = client.post('/auth/login', json={
        "email": "updateuser1@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    user1_token = login_response.json()["access_token"]

    # Create an application for the first user
    create_response = client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
        json={
            "company": "Google",
            "role": "Software Engineer",
            "status": "Applied"
        }
    )

    assert create_response.status_code == 201

    application_id = create_response.json()["id"]

    # Register the second user
    client.post('/auth/register', json={
        "email": "updateuser2@example.com",
        "password": "password123"
    })

    # Login as the second user
    login_response = client.post('/auth/login', json={
        "email": "updateuser2@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    user2_token = login_response.json()["access_token"]

    # Try to update the first user's application
    response = client.put(
        f"/applications/{application_id}",
        headers={
            "Authorization": f"Bearer {user2_token}"
        },
        json={
            "company": "Microsoft",
            "role": "Backend Engineer",
            "status": "Interview"
        }
    )

    assert response.status_code == 404


# Test that a user cannot delete another user's application
def test_user_cannot_delete_another_users_application(client):
    # First, register the first user
    client.post('/auth/register', json={
        "email": "deleteuser1@example.com",
        "password": "password123"
    })

    # Login as the first user
    login_response = client.post('/auth/login', json={
        "email": "deleteuser1@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    user1_token = login_response.json()["access_token"]

    # Create an application for the first user
    create_response = client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {user1_token}"
        },
        json={
            "company": "Amazon",
            "role": "Software Engineer",
            "status": "Applied"
        }
    )

    assert create_response.status_code == 201

    application_id = create_response.json()["id"]

    # Register the second user
    client.post('/auth/register', json={
        "email": "deleteuser2@example.com",
        "password": "password123"
    })

    # Login as the second user
    login_response = client.post('/auth/login', json={
        "email": "deleteuser2@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    user2_token = login_response.json()["access_token"]

    # Try to delete the first user's application
    response = client.delete(
        f"/applications/{application_id}",
        headers={
            "Authorization": f"Bearer {user2_token}"
        }
    )

    assert response.status_code == 404


# Test creating an application with an invalid company name
def test_create_application_invalid_company(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "validation@example.com",
        "password": "password123"
    })

    # Then, login to get an access token
    login_response = client.post('/auth/login', json={
        "email": "validation@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Try to create an application with an empty company name
    response = client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "company": "",
            "role": "Software Engineer",
            "status": "Applied"
        }
    )

    assert response.status_code == 422


# Test creating an application with an invalid role name
def test_create_application_invalid_role(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "rolevalidation@example.com",
        "password": "password123"
    })

    # Then, login to get an access token
    login_response = client.post('/auth/login', json={
        "email": "rolevalidation@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Try to create an application with an empty role name
    response = client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "company": "Google",
            "role": "",
            "status": "Applied"
        }
    )

    assert response.status_code == 422


# Test creating an application with an invalid status
def test_create_application_invalid_status(client):
    # First, register a user
    client.post('/auth/register', json={
        "email": "statusvalidation@example.com",
        "password": "password123"
    })

    # Then, login to get an access token
    login_response = client.post('/auth/login', json={
        "email": "statusvalidation@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Try to create an application with an invalid status
    response = client.post(
        "/applications",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "company": "Google",
            "role": "Software Engineer",
            "status": "InvalidStatus"
        }
    )

    assert response.status_code == 422


