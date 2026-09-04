import json
import urllib.error
import urllib.parse
import urllib.request

from constants import API_BASE, VEHICLE_ENDPOINT, API_TIMEOUT, API_INCLUDE, USER_AGENT


class APIResult:
    def __init__(self, data=None, status=None, error_type=None, retry_after=None):
        self.data = data
        self.status = status
        self.error_type = error_type
        self.retry_after = retry_after

    @property
    def ok(self):
        return self.data is not None and self.status == 200


class MySkodaAPI:
    def __init__(self, vin, api_key, logger):
        self.vin = vin
        self.api_key = api_key
        self.logger = logger
        self.api_key_expires = ""
        self.rate_limit = ""

    def build_vehicle_url(self):
        encoded_vin = urllib.parse.quote(self.vin, safe="")
        endpoint = VEHICLE_ENDPOINT.format(vin=encoded_vin)
        query = urllib.parse.urlencode([("include", ",".join(API_INCLUDE))])
        return API_BASE + endpoint + "?" + query

    def get_vehicle(self):
        request = urllib.request.Request(
            self.build_vehicle_url(),
            headers={
                "X-API-Key": self.api_key,
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="GET",
        )
        self.logger.debug("Requesting vehicle data")
        try:
            with urllib.request.urlopen(request, timeout=API_TIMEOUT) as response:
                self._capture_headers(response.headers)
                status = response.getcode()
                body = response.read().decode("utf-8", errors="replace")
                if status != 200:
                    self.logger.error("Unexpected HTTP status {}".format(status))
                    return APIResult(status=status, error_type="HTTP")
                try:
                    data = json.loads(body)
                except json.JSONDecodeError as exc:
                    self.logger.error("Invalid JSON response: {}".format(exc))
                    return APIResult(status=status, error_type="INVALID_JSON")
                return APIResult(data=data, status=status)
        except urllib.error.HTTPError as exc:
            self._capture_headers(exc.headers)
            status = exc.code
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            messages = {
                400: "HTTP 400 Bad Request",
                401: "HTTP 401 Unauthorized - check the API key",
                403: "HTTP 403 Forbidden - API key may not be authorized for this vehicle",
                404: "HTTP 404 Not Found - vehicle not found",
                422: "HTTP 422 Unprocessable Entity",
                429: "HTTP 429 Too Many Requests",
                500: "HTTP 500 Internal Server Error",
                503: "HTTP 503 Service Unavailable",
                504: "HTTP 504 Gateway Timeout",
            }
            self.logger.error(messages.get(status, "HTTP {} returned by MyŠkoda API".format(status)))
            if retry_after:
                self.logger.error("Retry-After: {}".format(retry_after))
            return APIResult(status=status, error_type="HTTP", retry_after=retry_after)
        except urllib.error.URLError as exc:
            self.logger.error("Connection error: {}".format(exc.reason))
            return APIResult(error_type="CONNECTION")
        except TimeoutError:
            self.logger.error("API request timed out after {} seconds".format(API_TIMEOUT))
            return APIResult(error_type="TIMEOUT")
        except Exception as exc:
            self.logger.error("Unexpected API error: {}".format(exc))
            return APIResult(error_type="ERROR")

    def _capture_headers(self, headers):
        if not headers:
            return
        expires = headers.get("X-API-Key-Expires-At")
        if expires:
            self.api_key_expires = expires
        remaining = headers.get("RateLimit-Remaining")
        limit = headers.get("RateLimit-Limit")
        reset = headers.get("RateLimit-Reset")
        if remaining is not None or limit is not None or reset is not None:
            self.rate_limit = "Remaining={}; Limit={}; Reset={}".format(
                remaining or "?", limit or "?", reset or "?"
            )
