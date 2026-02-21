import logging

from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates

from models import TaskPriority, TaskStatus

logger = logging.getLogger(__name__)

_VALID_PRIORITIES = [p.value for p in TaskPriority]
_VALID_STATUSES = [s.value for s in TaskStatus]


# ---------------------------------------------------------------------------
# Project schemas
# ---------------------------------------------------------------------------


class ProjectCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(load_default=None)


class ProjectResponseSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    created_at = fields.DateTime(format="iso")


# ---------------------------------------------------------------------------
# Task schemas
# ---------------------------------------------------------------------------


class TaskCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    description = fields.Str(load_default=None)
    priority = fields.Str(load_default="medium")

    @validates("priority")
    def validate_priority(self, value, **kwargs):
        if value not in _VALID_PRIORITIES:
            logger.warning("Rejected invalid priority value: %r", value)
            raise ValidationError(
                f"Must be one of: {_VALID_PRIORITIES}. Got: {value!r}"
            )


class TaskUpdateSchema(Schema):
    """Partial update schema — every field is optional."""

    class Meta:
        unknown = EXCLUDE

    title = fields.Str(validate=validate.Length(min=1, max=300))
    description = fields.Str(allow_none=True)
    priority = fields.Str()
    status = fields.Str()

    @validates("priority")
    def validate_priority(self, value, **kwargs):
        if value not in _VALID_PRIORITIES:
            logger.warning("Rejected invalid priority value: %r", value)
            raise ValidationError(
                f"Must be one of: {_VALID_PRIORITIES}. Got: {value!r}"
            )

    @validates("status")
    def validate_status(self, value, **kwargs):
        if value not in _VALID_STATUSES:
            logger.warning("Rejected invalid status value: %r", value)
            raise ValidationError(
                f"Must be one of: {_VALID_STATUSES}. Got: {value!r}"
            )


class TaskResponseSchema(Schema):
    id = fields.Int()
    project_id = fields.Int()
    title = fields.Str()
    description = fields.Str(allow_none=True)
    # Enums are serialised to their string value via Method fields so the
    # response contract is explicit rather than relying on SQLAlchemy's repr.
    status = fields.Method("get_status")
    priority = fields.Method("get_priority")
    created_at = fields.DateTime(format="iso")
    updated_at = fields.DateTime(format="iso")

    def get_status(self, obj):
        return obj.status.value

    def get_priority(self, obj):
        return obj.priority.value


# ---------------------------------------------------------------------------
# Module-level schema instances (avoid repeated instantiation)
# ---------------------------------------------------------------------------

project_create_schema = ProjectCreateSchema()
project_response_schema = ProjectResponseSchema()
projects_response_schema = ProjectResponseSchema(many=True)

task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
task_response_schema = TaskResponseSchema()
tasks_response_schema = TaskResponseSchema(many=True)
