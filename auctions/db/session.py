from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from auctions.config import Config


class SessionManager:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.engine = create_engine(config.db_url, echo=True)
        self.session = scoped_session(sessionmaker(bind=self.engine))
