from abc import ABC, abstractmethod

from app.schemas import Session


class SessionNotFound(Exception):
    pass


class SessionStore(ABC):
    @abstractmethod
    def save(self, session: Session) -> None:
        pass

    @abstractmethod
    def get(self, session_id: str) -> Session:
        pass


class InMemorySessionStore(SessionStore):
    def __init__(self):
        self._sessions = {}

    def save(self, session: Session) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            raise SessionNotFound("Session not found")
        return self._sessions[session_id]


session_store = InMemorySessionStore()
