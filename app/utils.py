from passlib.context import CryptContext

# bcrypt 알고리즘 사용 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """입력받은 비번과 DB의 해시 비번이 일치하는지 확인"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """비밀번호를 암호화하여 리턴"""
    return pwd_context.hash(password)