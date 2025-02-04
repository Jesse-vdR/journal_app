from app.models import User

def test_password_hashing():
    u = User(username='test')
    u.set_password('test_password')
    assert not u.check_password('wrong_password')
    assert u.check_password('test_password')

def test_user_representation():
    username = 'test'
    u = User(username=username)
    assert str(u) == f'<User {username}>'
