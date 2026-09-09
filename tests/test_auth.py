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


# Test getting a non-existent application
def test_get_nonexistent_application(client):
    # Register a user
    register_response = client.post(
        "/auth/register",
        json={
            "email": "nonexistent@example.com",
            "password": "password123"
        }
    )

    assert register_response.status_code == 201

    login_response = client.post(
    "/auth/login",
    json={
        "email": "nonexistent@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Try to get a non-existent application
    response = client.get(
        "/applications/9999",  # Assuming this ID does not exist
        headers={"Authorization": f"Bearer {access_token}"}
        )

    assert response.status_code == 404
    assert response.json() == {
        "error": "Application not found",
        "status_code": 404
    }


# Test getting an application with an invalid ID (non-integer)
def test_get_application_with_invalid_id(client):
    # Register a user
    client.post('/auth/register', json={
        "email": "invalidid@example.com",
        "password": "password123"
    })

    # Login
    login_response = client.post('/auth/login', json={
        "email": "invalidid@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Try to access an application using a non-integer ID
    response = client.get(
        "/applications/abc",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 422


# Test getting applications with an invalid sort_by value
def test_get_applications_invalid_sort_by(client):
    # Register a user
    client.post('/auth/register', json={
        "email": "invalidsort@example.com",
        "password": "password123"
    })

    # Login
    login_response = client.post('/auth/login', json={
        "email": "invalidsort@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Try to sort applications using an invalid field
    response = client.get(
        "/applications?sort_by=invalid_field",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 400


# Test pagination validation
def test_get_applications_invalid_pagination(client):
    # Register a user
    client.post('/auth/register', json={
        "email": "pagination@example.com",
        "password": "password123"
    })

    # Login
    login_response = client.post('/auth/login', json={
        "email": "pagination@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Page cannot be 0
    response = client.get(
        "/applications?page=0",
        headers=headers
    )

    assert response.status_code == 422

    # Limit cannot be 0
    response = client.get(
        "/applications?limit=0",
        headers=headers
    )

    assert response.status_code == 422

    # Limit cannot be greater than 100
    response = client.get(
        "/applications?limit=101",
        headers=headers
    )

    assert response.status_code == 422


# Test update application with invalid data
def test_update_application_invalid_data(client):
    # Register a user
    client.post('/auth/register', json={
        "email": "updatevalidation@example.com",
        "password": "password123"
    })

    # Login
    login_response = client.post('/auth/login', json={
        "email": "updatevalidation@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Create an application first
    create_response = client.post(
        "/applications",
        json={
            "company": "Google",
            "role": "Software Engineer",
            "status": "Applied"
        },
        headers=headers
    )

    assert create_response.status_code == 201

    application_id = create_response.json()["id"]

    # Try to update with an invalid company
    response = client.put(
        f"/applications/{application_id}",
        json={
            "company": "",
            "role": "Software Engineer",
            "status": "Applied"
        },
        headers=headers
    )

    assert response.status_code == 422

    # Try to update with an invalid role
    response = client.put(
        f"/applications/{application_id}",
        json={
            "company": "Google",
            "role": "",
            "status": "Applied"
        },
        headers=headers
    )

    assert response.status_code == 422

    # Try to update with an invalid status
    response = client.put(
        f"/applications/{application_id}",
        json={
            "company": "Google",
            "role": "Software Engineer",
            "status": "InvalidStatus"
        },
        headers=headers
    )

    assert response.status_code == 422


# Test updating a non-existent application
def test_update_nonexistent_application(client):
    # Register a user
    client.post('/auth/register', json={
        "email": "updatenonexistent@example.com",
        "password": "password123"
    })

    # Login
    login_response = client.post('/auth/login', json={
        "email": "updatenonexistent@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Try to update a non-existent application
    response = client.put(
        "/applications/9999",
        json={
            "company": "Google",
            "role": "Software Engineer",
            "status": "Applied"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "Application not found",
        "status_code": 404
    }


# Test deleting a non-existent application
def test_delete_nonexistent_application(client):
    # Register a user
    client.post('/auth/register', json={
        "email": "deletenonexistent@example.com",
        "password": "password123"
    })

    # Login
    login_response = client.post('/auth/login', json={
        "email": "deletenonexistent@example.com",
        "password": "password123"
    })

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Try to delete a non-existent application
    response = client.delete(
        "/applications/9999",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": "Application not found",
        "status_code": 404
    }