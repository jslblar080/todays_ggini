from typing import Any # Any: 타입 힌팅에 사용되는 타입으로, 어떤 타입도 허용한다는 의미입니다
from sqlalchemy.ext.declarative import as_declarative, declared_attr 
# as_declarative: SQLAlchemy의 데코레이터로, 클래스를 ORM 모델로 사용할 수 있도록 변환합니다.
# declared_attr: 클래스 속성을 정의할 때 사용되는 데코레이터로, 이 속성이 클래스가 생성될 때 동적으로 평가되도록 합니

@as_declarative() # Base 클래스를 SQLAlchemy의 ORM 모델로 설정합니다. 즉, 이 클래스를 상속받은 모든 클래스는 SQLAlchemy의 테이블로 매핑될 수 있습니다
class Base:
    id: Any
    __name__: str

    # 클래스 이름을 소문자로 변환하여 테이블 이름으로 자동 지정
    # pylint: disable=no-self-argument
    @declared_attr # 이 데코레이터를 사용하여 __tablename__ 속성을 정의합니다. 이 속성은 각 모델 클래스가 생성될 때 동적으로 평가됩니다.
    def __tablename__(cls) -> str:
        return cls.__name__.lower()