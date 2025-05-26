def test_user_registration_and_login_flow():
    """Test the complete user registration and login flow."""
    # Setup test client
    client = app.test_client()
    
    # Register a new user
    register_response = client.post('/api/register', json={
        'username': 'testuser123',
        'email': 'test@example.com',
        'password': 'SecureP@ss123',
        'first_name': 'Test',
        'last_name': 'User'
    })
    assert register_response.status_code == 200
    
    # Login with the new user
    login_response = client.post('/api/login', json={
        'username': 'testuser123',
        'password': 'SecureP@ss123'
    })
    assert login_response.status_code == 200
    assert 'token' in login_response.json
    
    # Verify token works for authenticated endpoint
    token = login_response.json['token']
    profile_response = client.get('/api/user/profile', 
                                 headers={'Authorization': f'Bearer {token}'})
    assert profile_response.status_code == 200
    assert profile_response.json['username'] == 'testuser123'