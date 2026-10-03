import time
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, name: str):
        self.name = name
        self.failure_threshold = settings.CIRCUIT_FAILURE_THRESHOLD
        self.cooldown_seconds = settings.CIRCUIT_OPEN_SECONDS
        self.half_open_requests = settings.CIRCUIT_HALF_OPEN_REQUESTS
        
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_success_count = 0
        self.half_open_active_requests = 0

    def allow_request(self) -> bool:
        now = time.time()
        
        if self.state == "CLOSED":
            return True
            
        if self.state == "OPEN":
            if now - self.last_failure_time > self.cooldown_seconds:
                self.state = "HALF_OPEN"
                self.half_open_success_count = 0
                self.half_open_active_requests = 0
                logger.warning(f"Circuit Breaker '{self.name}' transitioned from OPEN to HALF_OPEN")
                return True
            return False
            
        if self.state == "HALF_OPEN":
            if self.half_open_active_requests < self.half_open_requests:
                self.half_open_active_requests += 1
                return True
            return False

    def record_success(self):
        if self.state == "HALF_OPEN":
            self.half_open_success_count += 1
            if self.half_open_success_count >= self.half_open_requests:
                self.state = "CLOSED"
                self.failure_count = 0
                self.half_open_active_requests = 0
                logger.info(f"Circuit Breaker '{self.name}' recovered. Transitioned from HALF_OPEN to CLOSED")
        elif self.state == "CLOSED":
            self.failure_count = 0

    def record_failure(self):
        now = time.time()
        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.last_failure_time = now
            logger.error(f"Circuit Breaker '{self.name}' failed in HALF_OPEN. Transitioning back to OPEN")
        elif self.state == "CLOSED":
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.last_failure_time = now
                logger.error(f"Circuit Breaker '{self.name}' reached failure threshold ({self.failure_threshold}). Transitioning from CLOSED to OPEN")

gemini_circuit_breaker = CircuitBreaker("gemini")
