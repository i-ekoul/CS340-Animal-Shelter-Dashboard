# animal_shelter_mod5.py
# Implements Create, Read, Update, Delete against AAC.animals

from __future__ import annotations

import os
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
        except errors.PyMongoError as e:
            raise RuntimeError(f"MongoDB connection failed: {e}") from e

    # -----------------------------
    # C — Create
    # -----------------------------
    def create(self, data: Dict[str, Any]) -> bool:
        """
        Insert a single document.
        Returns:
            True on success; False on validation/driver error.
        """
        if not isinstance(data, dict) or not data:
            return False
        try:
            result = self.collection.insert_one(data)
            return bool(result.inserted_id)
        except errors.PyMongoError:
            return False

    # -----------------------------
    # R — Read
    # -----------------------------
    def read(
        self,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, int]] = None,
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query documents using find() and return a list.

        Args:
            query: MongoDB filter dict (defaults to {}).
            projection: e.g., {"_id": 0, "name": 1}
            limit: positive int to cap results; None means no explicit limit.
            sort: list of (field, direction) tuples, e.g., [("name", 1)]

        Returns:
            List of documents (possibly empty). Returns [] on driver error.
        """
        q = {} if query is None else query
        try:
            cursor = self.collection.find(q, projection)
            if sort:
                cursor = cursor.sort(sort)
            if isinstance(limit, int) and limit > 0:
                cursor = cursor.limit(limit)
            return list(cursor)
        except errors.PyMongoError:
            return []

    # -----------------------------
    # U — Update
    # -----------------------------
    def update(
        self,
        query: Dict[str, Any],
        new_values: Dict[str, Any],
        *,
        many: bool = False,
    ) -> int:
        """
        Update matching document(s) using $set.

        Args:
            query: filter to select documents to update (must be non-empty)
            new_values: fields to set, e.g., {"outcome_type": "Transfer"}
            many: if True, update_many; else update_one

        Returns:
            Number of documents modified (0 on validation/driver error).
        """
        if not isinstance(query, dict) or not query:
            return 0
        if not isinstance(new_values, dict) or not new_values:
            return 0

        try:
            update_doc = {"$set": new_values}
            if many:
                result = self.collection.update_many(query, update_doc)
            else:
                result = self.collection.update_one(query, update_doc)
            return int(result.modified_count or 0)
        except errors.PyMongoError:
            return 0

    # -----------------------------
    # D — Delete
    # -----------------------------
    def delete(
        self,
        query: Dict[str, Any],
        *,
        many: bool = False,
        allow_all: bool = False,
    ) -> int:
        """
        Delete matching document(s).

        Args:
            query: filter to select documents to delete.
            many: if True, delete_many; else delete_one.
            allow_all: set to True to permit an empty filter {} for bulk deletes.
                       (Safety guard to prevent accidental full collection wipes.)

        Returns:
            Number of documents deleted (0 on validation/driver error).
        """
        if not isinstance(query, dict):
            return 0
        if not query and not allow_all:
            # Safety: do not allow full-collection deletes by default
            return 0

        try:
            if many:
                result = self.collection.delete_many(query)
            else:
                result = self.collection.delete_one(query)
            return int(result.deleted_count or 0)
        except errors.PyMongoError:
            return 0