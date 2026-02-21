import logging

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError as MarshmallowValidationError

from database import db
from errors import NotFoundError
from errors import ValidationError as AppValidationError
from models import Project, Task, TaskPriority, TaskStatus
from schemas import (
    project_create_schema,
    project_response_schema,
    projects_response_schema,
    task_create_schema,
    task_response_schema,
    tasks_response_schema,
)

logger = logging.getLogger(__name__)

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------


@projects_bp.route("/", methods=["GET"])
def list_projects():
    projects = Project.query.all()
    return jsonify(projects_response_schema.dump(projects)), 200


@projects_bp.route("/", methods=["POST"])
def create_project():
    try:
        data = project_create_schema.load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as exc:
        logger.warning("Validation error on project creation: %s", exc.messages)
        raise AppValidationError(str(exc.messages))

    project = Project(name=data["name"], description=data["description"])
    db.session.add(project)
    db.session.commit()
    logger.info("Created project id=%d name=%r", project.id, project.name)
    return jsonify(project_response_schema.dump(project)), 201


@projects_bp.route("/<int:project_id>", methods=["GET"])
def get_project(project_id):
    project = db.session.get(Project, project_id)
    if project is None:
        raise NotFoundError(
            f"Project {project_id} not found", code="PROJECT_NOT_FOUND"
        )
    return jsonify(project_response_schema.dump(project)), 200


@projects_bp.route("/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    project = db.session.get(Project, project_id)
    if project is None:
        raise NotFoundError(
            f"Project {project_id} not found", code="PROJECT_NOT_FOUND"
        )
    db.session.delete(project)
    db.session.commit()
    logger.info("Deleted project id=%d", project_id)
    return "", 204


# ---------------------------------------------------------------------------
# Tasks nested under a project
# ---------------------------------------------------------------------------


@projects_bp.route("/<int:project_id>/tasks", methods=["GET"])
def list_project_tasks(project_id):
    project = db.session.get(Project, project_id)
    if project is None:
        raise NotFoundError(
            f"Project {project_id} not found", code="PROJECT_NOT_FOUND"
        )

    query = Task.query.filter_by(project_id=project_id)

    status_filter = request.args.get("status")
    if status_filter:
        try:
            status_enum = TaskStatus(status_filter)
        except ValueError:
            raise AppValidationError(
                f"Invalid status filter: {status_filter!r}. "
                f"Must be one of: {[s.value for s in TaskStatus]}"
            )
        query = query.filter_by(status=status_enum)

    priority_filter = request.args.get("priority")
    if priority_filter:
        try:
            priority_enum = TaskPriority(priority_filter)
        except ValueError:
            raise AppValidationError(
                f"Invalid priority filter: {priority_filter!r}. "
                f"Must be one of: {[p.value for p in TaskPriority]}"
            )
        query = query.filter_by(priority=priority_enum)

    tasks = query.all()
    return jsonify(tasks_response_schema.dump(tasks)), 200


@projects_bp.route("/<int:project_id>/tasks", methods=["POST"])
def create_task(project_id):
    project = db.session.get(Project, project_id)
    if project is None:
        raise NotFoundError(
            f"Project {project_id} not found", code="PROJECT_NOT_FOUND"
        )

    try:
        data = task_create_schema.load(request.get_json(silent=True) or {})
    except MarshmallowValidationError as exc:
        logger.warning("Validation error on task creation: %s", exc.messages)
        raise AppValidationError(str(exc.messages))

    task = Task(
        project_id=project_id,
        title=data["title"],
        description=data["description"],
        priority=TaskPriority(data["priority"]),
    )
    db.session.add(task)
    db.session.commit()
    logger.info(
        "Created task id=%d project_id=%d title=%r", task.id, project_id, task.title
    )
    return jsonify(task_response_schema.dump(task)), 201
