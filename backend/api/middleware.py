import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from urllib.error import HTTPError  # <-- important

logger = logging.getLogger(__name__)

class JsonExceptionMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):

        if not request.path.startswith("/api/"):
            return None

        status = 500
        payload = {
            "error": "server_error",
            "message": str(exception),
        }

        # 🔹 Handle urllib HTTPError (your case)
        if isinstance(exception, HTTPError):
            status = exception.code  # 429 in your case

            if status == 429:
                payload = {"error": "rate_limited", "message": "API - Rate Limit Hit (429). Please retry shortly."}
                response = JsonResponse(payload, status=429)
                retry_after = exception.headers.get("Retry-After")
                if retry_after:
                    response["Retry-After"] = retry_after
                return response

            if status == 401:
                return JsonResponse(
                    {"error": "unauthorized", "message": "API - Unauthorized (401). Possibly an ongoing session right now. Try again after."},
                    status=401,
                )

            if status == 400:
                return JsonResponse(
                    {"error": "bad_request", "message": "API - Bad Request (400). Query parameters are invalid."},
                    status=400,
                )

            if status == 403:
                return JsonResponse(
                    {"error": "forbidden", "message": "API - Forbidden (403)."},
                    status=403,
                )

            if status == 404:
                return JsonResponse(
                    {"error": "not_found", "message": "API - Not found (404). Resource not found."},
                    status=404,
                )

            # other upstream HTTP errors
            return JsonResponse(
                {"error": "upstream_http_error", "message": str(getattr(exception, "reason", "")), "upstream_status": status},
                status=502,
            )

        # 🔹 Fallback for anything else
        logger.exception("Unhandled exception on %s", request.path)
        return JsonResponse(payload, status=status)
