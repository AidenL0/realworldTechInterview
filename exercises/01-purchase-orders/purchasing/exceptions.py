from rest_framework import status
from rest_framework.exceptions import APIException


class Conflict(APIException):
    """The request is valid, but the order's current status doesn't allow it."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "This action isn't allowed in the order's current status."
    default_code = "conflict"
