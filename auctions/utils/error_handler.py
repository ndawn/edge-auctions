from functools import wraps
from traceback import print_exception

from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import UnprocessableEntity

from auctions.db import db
from auctions.dependencies import Provide
from auctions.dependencies import inject
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


@inject
def with_error_handler(
    func: callable,
    exception_serialzer: ExceptionSerializer = Provide(),
) -> callable:
    @wraps(func)
    def decorated(*args, **kwargs):
        try:
            try:
                return func(*args, **kwargs)
            except:
                db.session.rollback()
                raise
        except HTTPError as exception:
            return JsonResponse(exception_serialzer.dump(exception), status=exception.status_code)
        except (MarshmallowValidationError, UnprocessableEntity) as exception:
            exception = convert_validation_error(exception)
            print_exception(exception.__class__, exception, exception.__traceback__)
            return JsonResponse(exception_serialzer.dump(exception), status=exception.status_code)
        except Exception as exception:
            print_exception(exception.__class__, exception, exception.__traceback__)
            return JsonResponse(exception_serialzer.dump(exception), status=500)

    return decorated
