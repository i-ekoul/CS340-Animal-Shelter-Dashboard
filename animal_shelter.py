# animal_shelter_mod5.py
# Implements Create, Read, Update, Delete against AAC.animals

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pymongo import MongoClient, errors


class AnimalShelter:
    """
    CRUD operations for the AAC.animals collection in MongoDB.

    Connection defaults match the SNHU Apporto environment you used:
      - host: nv-desktop-services.apporto.com
      - port: 32789  (dynamic per session; can be overridden via env)
      - authSource: admin
      - user/pass: aacuser / SNHU1234

    You can override host/port with environment variables:
      MONGO_HOST, MONGO_PORT

    You can also pass a full MongoDB URI to __init__(uri=...) if desired.
    """

    # Status enum: allowed values for the status field
    # Documented allowed values: "Available", "Adopted", "Transferred", "Euthanized", "Returned to Owner"
    STATUS_VALUES = {"Available", "Adopted", "Transferred", "Euthanized", "Returned to Owner"}

    def __init__(
        self,
        *,
        uri: Optional[str] = None,
        user: str = "aacuser",
        password: str = "SNHU1234",
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: str = "AAC",
        collection: str = "animals",
        # Extra MongoClient kwargs (timeouts, etc.) can be passed via **client_kwargs
        **client_kwargs: Any,
    ) -> None:
        """
        Initialize MongoDB client and bind to database/collection.
        """
        # Resolve host/port using environment fallbacks (matches Apporto pattern)
        resolved_host = host or os.getenv("MONGO_HOST", "nv-desktop-services.apporto.com")
        resolved_port = int(port or os.getenv("MONGO_PORT", "32789"))

        if uri is None:
            # Build a simple, reliable single-host URI.
            # Notes:
            #  - authSource=admin (Module 3 user lives in 'admin' with role on 'AAC')
            #  - directConnection=true to avoid topology discovery quirks in labs
            #  - retryWrites=false avoids retryable write/session requirements on single hosts
            uri = (
                f"mongodb://{user}:{password}@{resolved_host}:{resolved_port}/"
                f"?authSource=admin&directConnection=true&retryWrites=false"
            )

        # Sensible defaults; can be overridden via **client_kwargs
        defaults = dict(
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
        )
        defaults.update(client_kwargs)

        try:
            self.client = MongoClient(uri, **defaults)
            self.database = self.client[database]
            self.collection = self.database[collection]
            # Create compound index for common query path
            # Safe: won't crash if index already exists
            self._ensure_indexes()
        except errors.PyMongoError as e:
            raise RuntimeError(f"MongoDB connection failed: {e}") from e

    def _ensure_indexes(self) -> None:
        """
        Create compound index for the most common query path.
        Safe: handles case where index already exists.
        Ensures exactly: { status: 1, animal_type: 1, intake_date: -1 }
        """
        try:
            # Compound index on status, animal_type, and intake_date (descending)
            # Optimizes queries filtering by status and animal_type, sorted by intake_date
            self.collection.create_index([("status", 1), ("animal_type", 1), ("intake_date", -1)])
        except errors.PyMongoError:
            # Index may already exist or creation failed - silently continue
            pass

    # -----------------------------
    # Input Validation Helpers
    # -----------------------------
    @staticmethod
    def _normalize_animal_type(value: Any) -> Optional[str]:
        """Normalize animal_type field to string or None."""
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() if value.strip() else None
        return str(value).strip() if str(value).strip() else None

    @staticmethod
    def _normalize_outcome_type(value: Any) -> Optional[str]:
        """Normalize outcome_type field to string or None."""
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() if value.strip() else None
        return str(value).strip() if str(value).strip() else None

    @staticmethod
    def _normalize_status(value: Any) -> Optional[str]:
        """
        Normalize status field to string or None.
        Enforces status enum: allowed values are "Available", "Adopted", "Transferred", 
        "Euthanized", "Returned to Owner".
        """
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            if normalized in AnimalShelter.STATUS_VALUES:
                return normalized
        return None

    @staticmethod
    def _normalize_limit(value: Any) -> Optional[int]:
        """Normalize limit to positive int or None."""
        if value is None:
            return None
        try:
            limit = int(value)
            return limit if limit > 0 else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _normalize_intake_date(value: Any) -> Optional[datetime]:
        """
        Normalize intake_date field to datetime or None.
        Accepts datetime objects, ISO format strings, or None.
        Coerces to consistent datetime type for query/sort operations.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                # Try parsing ISO format strings
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                try:
                    # Try common date formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
                except (ValueError, TypeError):
                    pass
        return None

    @staticmethod
    def _validate_query(query: Any) -> Dict[str, Any]:
        """Validate and normalize query dict."""
        if not isinstance(query, dict):
            return {}
        # Normalize common string fields if present
        normalized = {}
        for key, value in query.items():
            if key == "animal_type":
                normalized[key] = AnimalShelter._normalize_animal_type(value)
            elif key == "outcome_type":
                normalized[key] = AnimalShelter._normalize_outcome_type(value)
            elif key == "status":
                normalized[key] = AnimalShelter._normalize_status(value)
            elif key == "intake_date":
                normalized[key] = AnimalShelter._normalize_intake_date(value)
            else:
                normalized[key] = value
        return normalized

    # -----------------------------
    # Structured Error Response Helper
    # -----------------------------
    @staticmethod
    def _error_result(code: str, message: str) -> Dict[str, Any]:
        """
        Create a structured error response with code and message.
        Error codes: VALIDATION_FAILED, NOT_FOUND, CONFLICT, DB_ERROR
        Do not return raw exception strings (no driver error text, no stack traces).
        
        Args:
            code: Error code (VALIDATION_FAILED, NOT_FOUND, CONFLICT, DB_ERROR)
            message: Human-readable error message (user-safe text)
            
        Returns:
            Dict with ok=False, code, message
        """
        return {"ok": False, "code": code, "message": message}

    @staticmethod
    def _success_result(data: Any = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Create a structured success response."""
        result = {"ok": True}
        if data is not None:
            result["data"] = data
        if count is not None:
            result["count"] = count
        return result

    # -----------------------------
    # C — Create (Structured Result)
    # -----------------------------
    def create_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a single document and return structured result.
        Returns:
            {"ok": True, "data": {"inserted_id": "..."}} or 
            {"ok": False, "code": "...", "message": "..."}
        """
        if not isinstance(data, dict) or not data:
            return self._error_result("VALIDATION_FAILED", "Data must be a non-empty dictionary")
        try:
            result = self.collection.insert_one(data)
            if result.inserted_id:
                return self._success_result({"inserted_id": str(result.inserted_id)})
            return self._error_result("DB_ERROR", "No document was inserted")
        except errors.PyMongoError:
            return self._error_result("DB_ERROR", "Database operation failed")

    def create(self, data: Dict[str, Any]) -> bool:
        """
        Insert a single document (legacy method for compatibility).
        Returns:
            True if successful, False otherwise
        """
        result = self.create_result(data)
        return result.get("ok", False)

    # -----------------------------
    # R — Read (Structured Result)
    # -----------------------------
    def read_result(
        self,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, int]] = None,
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None,
    ) -> Dict[str, Any]:
        """
        Query documents using find() and return structured result.

        Args:
            query: MongoDB filter dict (defaults to {}).
            projection: e.g., {"_id": 0, "name": 1}
            limit: positive int to cap results; None means no explicit limit.
            sort: list of (field, direction) tuples, e.g., [("name", 1)]

        Returns:
            {"ok": True, "data": [...], "count": N} or 
            {"ok": False, "code": "...", "message": "..."}
        """
        q = self._validate_query(query) if query is not None else {}
        normalized_limit = self._normalize_limit(limit)
        
        try:
            cursor = self.collection.find(q, projection)
            if sort:
                cursor = cursor.sort(sort)
            if normalized_limit:
                cursor = cursor.limit(normalized_limit)
            results = list(cursor)
            return self._success_result(data=results, count=len(results))
        except errors.PyMongoError:
            return self._error_result("DB_ERROR", "Query operation failed")

    def read(
        self,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, int]] = None,
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query documents using find() (legacy method for compatibility).
        Returns:
            List of documents (empty list on error)
        """
        result = self.read_result(query, projection, limit, sort)
        if result.get("ok"):
            return result.get("data", [])
        return []

    def explain_hot_query(
        self,
        status: Optional[str] = None,
        animal_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Explain the hot path query: status + optional animal_type, sorted by intake_date descending.
        This query path is optimized by the compound index { status: 1, animal_type: 1, intake_date: -1 }.
        
        Args:
            status: Status value to filter by (required for optimal index usage)
            animal_type: Optional animal_type filter
            limit: Optional limit on results
            
        Returns:
            {"ok": True, "data": <explain json>} or {"ok": False, "code": "...", "message": "..."}
        """
        # Build query matching the compound index
        query: Dict[str, Any] = {}
        if status:
            normalized_status = self._normalize_status(status)
            if normalized_status:
                query["status"] = normalized_status
            else:
                return self._error_result("VALIDATION_FAILED", f"Invalid status value: {status}")
        
        if animal_type:
            normalized_animal_type = self._normalize_animal_type(animal_type)
            if normalized_animal_type:
                query["animal_type"] = normalized_animal_type
        
        # Sort by intake_date descending (matches index)
        sort = [("intake_date", -1)]
        normalized_limit = self._normalize_limit(limit)
        
        try:
            cursor = self.collection.find(query)
            cursor = cursor.sort(sort)
            if normalized_limit:
                cursor = cursor.limit(normalized_limit)
            explain_result = cursor.explain()
            return self._success_result(data=explain_result)
        except errors.PyMongoError:
            return self._error_result("DB_ERROR", "Explain operation failed")

    def explain_query(
        self,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, int]] = None,
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None,
    ) -> Dict[str, Any]:
        """
        Run explain() on the primary read operation to verify index usage.
        
        Args:
            query: MongoDB filter dict (defaults to {}).
            projection: e.g., {"_id": 0, "name": 1}
            limit: positive int to cap results; None means no explicit limit.
            sort: list of (field, direction) tuples, e.g., [("name", 1)]
            
        Returns:
            {"ok": True, "data": <explain json>} or {"ok": False, "code": "...", "message": "..."}
        """
        q = self._validate_query(query) if query is not None else {}
        normalized_limit = self._normalize_limit(limit)
        
        try:
            cursor = self.collection.find(q, projection)
            if sort:
                cursor = cursor.sort(sort)
            if normalized_limit:
                cursor = cursor.limit(normalized_limit)
            explain_result = cursor.explain()
            return self._success_result(data=explain_result)
        except errors.PyMongoError:
            return self._error_result("DB_ERROR", "Explain operation failed")

    # -----------------------------
    # U — Update (Structured Result)
    # -----------------------------
    def update_result(
        self,
        query: Dict[str, Any],
        new_values: Dict[str, Any],
        *,
        many: bool = False,
    ) -> Dict[str, Any]:
        """
        Update matching document(s) using $set and return structured result.

        Args:
            query: filter to select documents to update (must be non-empty)
            new_values: fields to set, e.g., {"outcome_type": "Transfer"}
            many: if True, update_many; else update_one

        Returns:
            {"ok": True, "count": N} or {"ok": False, "code": "...", "message": "..."}
        """
        q = self._validate_query(query)
        if not q:
            return self._error_result("VALIDATION_FAILED", "Query must be a non-empty dictionary")
        if not isinstance(new_values, dict) or not new_values:
            return self._error_result("VALIDATION_FAILED", "new_values must be a non-empty dictionary")

        try:
            update_doc = {"$set": new_values}
            if many:
                result = self.collection.update_many(q, update_doc)
            else:
                result = self.collection.update_one(q, update_doc)
            modified_count = int(result.modified_count or 0)
            if modified_count == 0:
                return self._error_result("NOT_FOUND", "No documents matched the query")
            return self._success_result(count=modified_count)
        except errors.PyMongoError:
            return self._error_result("DB_ERROR", "Update operation failed")

    def update(
        self,
        query: Dict[str, Any],
        new_values: Dict[str, Any],
        *,
        many: bool = False,
    ) -> bool:
        """
        Update matching document(s) using $set (legacy method for compatibility).

        Args:
            query: filter to select documents to update (must be non-empty)
            new_values: fields to set, e.g., {"outcome_type": "Transfer"}
            many: if True, update_many; else update_one

        Returns:
            True if successful, False otherwise
        """
        result = self.update_result(query, new_values, many=many)
        return result.get("ok", False)

    # -----------------------------
    # D — Delete (Structured Result)
    # -----------------------------
    def delete_result(
        self,
        query: Dict[str, Any],
        *,
        many: bool = False,
        allow_all: bool = False,
    ) -> Dict[str, Any]:
        """
        Delete matching document(s) and return structured result.

        Args:
            query: filter to select documents to delete.
            many: if True, delete_many; else delete_one.
            allow_all: set to True to permit an empty filter {} for bulk deletes.
                       (Safety guard to prevent accidental full collection wipes.)

        Returns:
            {"ok": True, "count": N} or {"ok": False, "code": "...", "message": "..."}
        """
        q = self._validate_query(query) if isinstance(query, dict) else {}
        if not q and not allow_all:
            return self._error_result("VALIDATION_FAILED", "Empty query not allowed unless allow_all=True")

        try:
            if many:
                result = self.collection.delete_many(q)
            else:
                result = self.collection.delete_one(q)
            deleted_count = int(result.deleted_count or 0)
            if deleted_count == 0:
                return self._error_result("NOT_FOUND", "No documents matched the query")
            return self._success_result(count=deleted_count)
        except errors.PyMongoError:
            return self._error_result("DB_ERROR", "Delete operation failed")

    def delete(
        self,
        query: Dict[str, Any],
        *,
        many: bool = False,
        allow_all: bool = False,
    ) -> bool:
        """
        Delete matching document(s) (legacy method for compatibility).

        Args:
            query: filter to select documents to delete.
            many: if True, delete_many; else delete_one.
            allow_all: set to True to permit an empty filter {} for bulk deletes.
                       (Safety guard to prevent accidental full collection wipes.)

        Returns:
            True if successful, False otherwise
        """
        result = self.delete_result(query, many=many, allow_all=allow_all)
        return result.get("ok", False)
