import json
import time
import urllib.error
import urllib.parse
import urllib.request

from constants import (
    API_BASE, API_INCLUDE, API_TIMEOUT, INITIAL_BACKOFF, MAX_BACKOFF,
    MAX_RETRIES, RETRYABLE_STATUS, USER_AGENT, VEHICLE_ENDPOINT,
)


class APIResult:
    def __init__(self, ok=False, status=None, data=None, error="", headers=None,
                 attempts=0, retry_after=None, elapsed=0.0, problem_type="", problem_title="", problem_detail=""):
        self.ok = ok
        self.status = status
        self.data = data
        self.error = error
        self.headers = headers or {}
        self.attempts = attempts
        self.retry_after = retry_after
        self.elapsed = elapsed
        self.problem_type = problem_type or ""
        self.problem_title = problem_title or ""
        self.problem_detail = problem_detail or ""

    @property
    def rate_limit(self):
        return self.headers.get("ratelimit-limit") or self.headers.get("x-ratelimit-limit")

    @property
    def rate_remaining(self):
        return self.headers.get("ratelimit-remaining") or self.headers.get("x-ratelimit-remaining")

    @property
    def rate_reset(self):
        return self.headers.get("ratelimit-reset") or self.headers.get("x-ratelimit-reset")

    @property
    def api_key_expires_at(self):
        return self.headers.get("x-api-key-expires-at", "")

    @property
    def rate_remaining_value(self):
        try:
            return max(0, int(float(self.rate_remaining))) if self.rate_remaining is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def rate_reset_value(self):
        try:
            return max(0.0, float(self.rate_reset)) if self.rate_reset is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def rate_text(self):
        parts = []
        if self.rate_limit is not None:
            parts.append("limit=" + str(self.rate_limit))
        if self.rate_remaining is not None:
            parts.append("remaining=" + str(self.rate_remaining))
        if self.rate_reset is not None:
            parts.append("reset=" + str(self.rate_reset) + "s")
        if self.retry_after is not None:
            parts.append("retry-after=" + str(self.retry_after) + "s")
        return ", ".join(parts) if parts else "Unavailable"


class MySkodaAPI:
    def __init__(self, api_key, vin, logger=None, timeout=API_TIMEOUT):
        self.api_key = api_key.strip()
        self.vin = vin.strip()
        self.logger = logger
        self.timeout = timeout
        self.last_result = None

    def _log_debug(self, message):
        if self.logger:
            try:
                self.logger.Debug(message)
            except Exception:
                pass

    def _url(self):
        query = urllib.parse.urlencode({"include": ",".join(API_INCLUDE)})
        return API_BASE + VEHICLE_ENDPOINT.format(vin=urllib.parse.quote(self.vin, safe="")) + "?" + query

    @staticmethod
    def _parse_retry_after(value):
        if value is None:
            return None
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _headers_dict(headers):
        result = {}
        if headers:
            for key, value in headers.items():
                if value is not None:
                    result[str(key).lower()] = str(value)
        return result

    @staticmethod
    def _problem_fields(body):
        if not body:
            return "", "", ""
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return (
                    str(parsed.get("type") or ""),
                    str(parsed.get("title") or ""),
                    str(parsed.get("detail") or parsed.get("message") or parsed.get("error") or ""),
                )
        except (ValueError, TypeError):
            pass
        return "", "", ""

    def fetch_vehicle(self):
        # The MySkoda Public API authenticates with X-API-Key.
        # Do not replace this with Authorization: Bearer.
        headers = {
            "Accept": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": USER_AGENT,
        }
        url = self._url()
        backoff = INITIAL_BACKOFF
        started = time.time()

        for attempt in range(1, MAX_RETRIES + 2):
            try:
                request = urllib.request.Request(url, headers=headers, method="GET")
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    response_headers = self._headers_dict(response.headers)
                    body = response.read().decode("utf-8", errors="replace")
                    status = getattr(response, "status", 200)
                    try:
                        data = json.loads(body)
                    except ValueError as exc:
                        result = APIResult(
                            False, status, None,
                            "Invalid JSON response: {}".format(exc),
                            response_headers, attempt, None, time.time() - started,
                        )
                        self.last_result = result
                        return result
                    ok = 200 <= status < 300
                    result = APIResult(
                        ok, status, data,
                        "" if ok else "HTTP {}".format(status),
                        response_headers, attempt, None, time.time() - started,
                    )
                    self.last_result = result
                    return result

            except urllib.error.HTTPError as exc:
                response_headers = self._headers_dict(exc.headers)
                retry_after = self._parse_retry_after(response_headers.get("retry-after"))
                status = exc.code
                try:
                    body = exc.read().decode("utf-8", errors="replace")
                except Exception:
                    body = ""
                problem_type, problem_title, problem_detail = self._problem_fields(body)

                if status in RETRYABLE_STATUS and attempt <= MAX_RETRIES:
                    delay = retry_after if retry_after is not None else min(backoff, MAX_BACKOFF)
                    self._log_debug(
                        "MySkoda API HTTP {} - retry {}/{} in {:.1f}s".format(
                            status, attempt, MAX_RETRIES, delay
                        )
                    )
                    time.sleep(delay)
                    backoff = min(backoff * 2.0, MAX_BACKOFF)
                    continue

                message = "HTTP {}".format(status)
                if problem_detail:
                    message += " - " + problem_detail

                result = APIResult(
                    False, status, None, message, response_headers,
                    attempt, retry_after, time.time() - started,
                    problem_type, problem_title, problem_detail,
                )
                self.last_result = result
                return result

            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                message = "Connection error: {}".format(exc)
                if attempt <= MAX_RETRIES:
                    delay = min(backoff, MAX_BACKOFF)
                    self._log_debug(
                        "{} - retry {}/{} in {:.1f}s".format(
                            message, attempt, MAX_RETRIES, delay
                        )
                    )
                    time.sleep(delay)
                    backoff = min(backoff * 2.0, MAX_BACKOFF)
                    continue
                result = APIResult(
                    False, None, None, message, {}, attempt, None,
                    time.time() - started,
                )
                self.last_result = result
                return result

            except Exception as exc:
                result = APIResult(
                    False, None, None, "Unexpected API error: {}".format(exc),
                    {}, attempt, None, time.time() - started,
                )
                self.last_result = result
                return result

        result = APIResult(
            False, None, None, "API request failed", {}, MAX_RETRIES + 1,
            None, time.time() - started,
        )
        self.last_result = result
        return result
