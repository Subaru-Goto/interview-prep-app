import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict

from app.config import settings
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

    @abstractmethod
    def delete(self, session_id: str) -> None:
        pass


class InMemorySessionStore(SessionStore):
    def __init__(self, time_fn=time.time):

        self._sessions: OrderedDict[str, tuple[Session, float]] = OrderedDict()
        self._time_fn = time_fn
        self._lock = threading.Lock()

    def save(self, session: Session) -> None:
        with self._lock:
            self._sessions[session.session_id] = (session, self._time_fn())
            self._sessions.move_to_end(session.session_id)
            while len(self._sessions) > settings.max_sessions:
                self._sessions.popitem(last=False)

    def get(self, session_id: str) -> Session:
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None:
                raise SessionNotFound("Session not found")

            session, last_active_at = entry
            if self._time_fn() - last_active_at > settings.session_ttl_seconds:
                del self._sessions[session_id]
                raise SessionNotFound("Session not found")

            self._sessions[session_id] = (session, self._time_fn())
            self._sessions.move_to_end(session_id)
            return session

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


session_store = InMemorySessionStore()
