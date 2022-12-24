from flask import request
from webargs.flaskparser import parser

from auctions.db.models.external import ExternalEntity
from auctions.db.repositories.external import ExternalEntitiesRepository
from auctions.dependencies import Provide
from auctions.dependencies import inject
from auctions.endpoints.crud import create_crud_blueprint
from auctions.serializers.external import ExternalEntityCreateSerializer
from auctions.serializers.external import ExternalEntitySerializer
from auctions.utils.error_handler import with_error_handler
from auctions.utils.external import resolve_external_relation
from auctions.utils.login import login_required
from auctions.utils.response import JsonResponse

blueprint = create_crud_blueprint(
    model=ExternalEntity,
    serializer_name="external_entity_serializer",
    create_args=ExternalEntityCreateSerializer(),
    update_args=ExternalEntitySerializer(partial=True),
    operations=("read", "update", "delete"),
    protected=("read", "update", "delete"),
)


@blueprint.post("")
@with_error_handler
@login_required()
@inject
def create_external_entity(
    external_entities_repository: ExternalEntitiesRepository = Provide["external_entities_repository"],
    external_entity_create_serializer: ExternalEntityCreateSerializer = Provide["external_entity_create_serializer"],
    external_entity_serializer: ExternalEntitySerializer = Provide["external_entity_serializer"],
) -> JsonResponse:
    data = parser.parse(external_entity_create_serializer, request)

    related_repository = resolve_external_relation(relates_to=data["relates_to"])
    external_entity = external_entities_repository.create(
        source=data["source"],
        entity_id=data["entity_id"],
        extra=data.get("extra") or {},
    )
    related_object = related_repository.get_one_by_id(data["relates_to_id"])
    related_repository.add_external(related_object, external_entity)
    return JsonResponse(external_entity_serializer.dump(external_entity))
