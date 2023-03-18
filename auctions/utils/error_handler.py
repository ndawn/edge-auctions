from traceback import print_exception

from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import UnprocessableEntity

from auctions.exceptions import HTTPError
from auctions.exceptions import ValidationError
from auctions.serializers.exceptions import ExceptionSerializer
from auctions.utils.response import JsonResponse


def convert_validation_error(exception: MarshmallowValidationError | UnprocessableEntity) -> ValidationError:
    if isinstance(exception, UnprocessableEntity):
        exception = exception.exc

    return ValidationError(
        message=str(exception),
        extra={"validation_errors": exception.messages},
    )


def handle_exception(exception: Exception):
    serializer = ExceptionSerializer()

    if isinstance(exception, HTTPError):
        return JsonResponse(serializer.dump(exception), status=exception.status_code)
    if isinstance(exception, (MarshmallowValidationError, UnprocessableEntity)):
        exception = convert_validation_error(exception)
        print_exception(exception.__class__, exception, exception.__traceback__)
        return JsonResponse(serializer.dump(exception), status=exception.status_code)

    print_exception(exception.__class__, exception, exception.__traceback__)
    return JsonResponse(serializer.dump(exception), status=500)
