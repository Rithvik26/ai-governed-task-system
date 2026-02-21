import logging

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError as MarshmallowValidationError

from database import db
from errors import NotFoundError
from errors import ValidationError as AppValidationError
from models import Task, TaskPriority, TaskStatus
from schemas import task_response_schema, task_update_schema

logger = logging.getLogger(__name__)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.route("/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError(f"Task {task_id} not found", code="TASK_NOT_FOUND")
    return jsonify(task_response_schema.dump(task)), 200


@tasks_bp.route("/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError(f"Task {task_id} not found", code="TASK_NOT_FOUND")

    try:
        data = task_update_schema.load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as exc:
        logger.warning("Validation error on task update: %s", exc.messages)
        raise AppValidationError(str(exc.messages))

    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "priority" in data:
        task.priority = TaskPriority(data["priority"])

    if "status" in data:
        new_status = TaskStatus(data["status"])
        # Delegation to the model enforces transition rules.
        # StateTransitionError is an AppError and will be caught by the
        # registered error handler — no explicit catch needed here.
        task.transition_to(new_status)
        logger.info(
            "Task id=%d transitioned to status=%r", task_id, new_status.value
        )

    db.session.commit()
    return jsonify(task_response_schema.dump(task)), 200
