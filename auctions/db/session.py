from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from auctions.config import Config


class SessionManager:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.engine = create_engine(config.db_url)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        return self.Session()
