"""
Simple Weaviate-backed vector DB helper.

This module intentionally keeps Weaviate as an optional dependency: the
`weaviate-client` package is imported only when you call `connect()` /
`get_vector_db()`.

Environment variables (optional):
- `WEAVIATE_URL` (default: http://localhost:8080)
- `WEAVIATE_API_KEY` (default: unset)
- `WEAVIATE_GRPC_PORT` (default: 50051)
- `WEAVIATE_COLLECTION` (default: Document)
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def _import_weaviate() -> Any:
    """
    Import the Weaviate Python client with a helpful error message.

    Common pitfall: installing the `weaviate` placeholder package instead of
    `weaviate-client` can lead to `ImportError` about a "partially initialized
    module 'weaviate'" (circular import).
    """
    # If the `weaviate` distribution is installed, it shadows the real client.
    # Detect it before importing to avoid the circular-import crash.
    try:
        from importlib import metadata

        try:
            weaviate_pkg = metadata.version("weaviate")
        except Exception:
            weaviate_pkg = None
        try:
            weaviate_client_pkg = metadata.version("weaviate-client")
        except Exception:
            weaviate_client_pkg = None

        if weaviate_pkg:
            raise RuntimeError(
                "The `weaviate` placeholder package is installed and breaks the Weaviate Python client.\n\n"
                "Fix:\n"
                "  pip uninstall -y weaviate\n"
                "  pip install -U weaviate-client\n\n"
                f"Detected: weaviate=={weaviate_pkg}"
                + (f", weaviate-client=={weaviate_client_pkg}" if weaviate_client_pkg else "")
            )
    except RuntimeError:
        raise
    except Exception:
        # If importlib.metadata isn't available for some reason, fall back to a normal import.
        pass

    try:
        import weaviate  # type: ignore

        return weaviate
    except Exception as exc:  # ImportError, circular import, etc.
        try:
            from importlib import metadata

            weaviate_pkg = None
            weaviate_client_pkg = None
            try:
                weaviate_pkg = metadata.version("weaviate")
            except Exception:
                weaviate_pkg = None
            try:
                weaviate_client_pkg = metadata.version("weaviate-client")
            except Exception:
                weaviate_client_pkg = None

            if weaviate_pkg and weaviate_client_pkg:
                raise RuntimeError(
                    "Weaviate import failed. Both `weaviate` and `weaviate-client` are installed, "
                    "and the `weaviate` placeholder package can shadow/break the real client.\n\n"
                    "Fix:\n"
                    "  pip uninstall -y weaviate\n"
                    "  pip install -U weaviate-client\n\n"
                    f"Detected: weaviate=={weaviate_pkg}, weaviate-client=={weaviate_client_pkg}"
                ) from exc

            if weaviate_pkg and not weaviate_client_pkg:
                raise RuntimeError(
                    "Weaviate import failed. The `weaviate` placeholder package is installed, "
                    "but the real client is `weaviate-client`.\n\n"
                    "Fix:\n"
                    "  pip uninstall -y weaviate\n"
                    "  pip install -U weaviate-client\n\n"
                    f"Detected: weaviate=={weaviate_pkg}"
                ) from exc

            raise RuntimeError(
                "Weaviate import failed. Install the Python client with:\n"
                "  pip install -U weaviate-client\n\n"
                "If you previously installed `weaviate`, uninstall it first:\n"
                "  pip uninstall -y weaviate"
            ) from exc
        except RuntimeError:
            raise
        except Exception:
            # Fallback if importlib.metadata isn't available for some reason.
            raise RuntimeError(
                "Weaviate import failed. Install the Python client with `pip install -U weaviate-client` "
                "and ensure the `weaviate` placeholder package is not installed."
            ) from exc


def _is_v4_client(weaviate_module: Any) -> bool:
    # v4 has connect helpers; v3 primarily exposes weaviate.Client
    return hasattr(weaviate_module, "connect_to_local") or hasattr(weaviate_module, "connect_to_custom")


@dataclass(frozen=True)
class SearchResult:
    uuid: str
    score: Optional[float]
    properties: Dict[str, Any]


@dataclass
class WeaviateVectorDB:
    url: str = "http://localhost:8080"
    grpc_port: Optional[int] = None
    api_key: Optional[str] = None
    collection: str = "Document"

    # property names (kept simple on purpose)
    text_key: str = "text"
    document_id_key: str = "document_id"
    page_key: str = "page"
    class_id_key: str = "class_id"
    material_id_key: str = "material_id"

    _client: Any = None

    def connect(self) -> Any:
        """
        Connect to Weaviate and cache the client.

        Supports both the v4 client (preferred) and legacy v3 client.
        """
        if self._client is not None:
            return self._client

        weaviate = _import_weaviate()

        if _is_v4_client(weaviate):
            # v4 client
            auth = None
            if self.api_key:
                try:
                    auth = weaviate.auth.AuthApiKey(self.api_key)
                except Exception:
                    # Keep auth optional; some setups don't require it.
                    auth = None

            if self.url.startswith("http://localhost") or self.url.startswith("http://127.0.0.1"):
                # If user didn't specify custom URL, local is the common case.
                try:
                    client = weaviate.connect_to_local(
                        host="localhost",
                        port=int(self.url.rsplit(":", 1)[-1]) if ":" in self.url else 8080,
                        grpc_port=self.grpc_port,
                        auth_credentials=auth,
                    )
                except Exception:
                    client = weaviate.connect_to_custom(
                        http_host=self.url.replace("http://", "").replace("https://", "").split(":")[0],
                        http_port=int(self.url.rsplit(":", 1)[-1]) if ":" in self.url else 8080,
                        http_secure=self.url.startswith("https://"),
                        grpc_host=self.url.replace("http://", "").replace("https://", "").split(":")[0],
                        grpc_port=self.grpc_port,
                        grpc_secure=self.url.startswith("https://"),
                        auth_credentials=auth,
                    )
            else:
                # Generic custom connection.
                host = self.url.replace("http://", "").replace("https://", "").split(":")[0]
                http_port = int(self.url.rsplit(":", 1)[-1]) if ":" in self.url else (443 if self.url.startswith("https://") else 80)
                client = weaviate.connect_to_custom(
                    http_host=host,
                    http_port=http_port,
                    http_secure=self.url.startswith("https://"),
                    grpc_host=host,
                    grpc_port=self.grpc_port,
                    grpc_secure=self.url.startswith("https://"),
                    auth_credentials=auth,
                )

            self._client = client
            return self._client

        # v3 legacy client
        if self.api_key:
            auth_config = weaviate.AuthApiKey(api_key=self.api_key)
            client = weaviate.Client(self.url, auth_client_secret=auth_config)
        else:
            client = weaviate.Client(self.url)

        self._client = client
        return self._client

    def close(self) -> None:
        client = self._client
        self._client = None
        if client is None:
            return

        # v4 client exposes `close()`; v3 does not require it
        close_fn = getattr(client, "close", None)
        if callable(close_fn):
            close_fn()

    def ensure_schema(self) -> None:
        """
        Ensure a simple schema/collection exists.

        - Collection/class name: `self.collection`
        - Properties: text, document_id, page
        - Vectorizer: none (we provide vectors explicitly)
        """
        client = self.connect()
        weaviate = _import_weaviate()

        if _is_v4_client(weaviate):
            try:
                existing = client.collections.list_all(simple=True)
            except Exception:
                existing = {}

            if self.collection in existing:
                return

            try:
                from weaviate.classes.config import Configure, Property, DataType  # type: ignore
            except Exception as exc:
                raise RuntimeError(
                    "Weaviate v4 client is installed, but config classes are unavailable. "
                    "Check your `weaviate-client` version."
                ) from exc

            client.collections.create(
                name=self.collection,
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name=self.text_key, data_type=DataType.TEXT),
                    Property(name=self.document_id_key, data_type=DataType.TEXT),
                    Property(name=self.page_key, data_type=DataType.INT),
                    Property(name=self.class_id_key, data_type=DataType.TEXT),
                    Property(name=self.material_id_key, data_type=DataType.INT),
                ],
            )
            return

        # v3 schema creation
        schema = client.schema.get()
        classes = {c.get("class") for c in schema.get("classes", []) if isinstance(c, dict)}
        if self.collection in classes:
            return

        class_obj = {
            "class": self.collection,
            "vectorizer": "none",
            "properties": [
                {"name": self.text_key, "dataType": ["text"]},
                {"name": self.document_id_key, "dataType": ["text"]},
                {"name": self.page_key, "dataType": ["int"]},
                {"name": self.class_id_key, "dataType": ["text"]},
                {"name": self.material_id_key, "dataType": ["int"]},
            ],
        }
        client.schema.create_class(class_obj)

    def add(
        self,
        *,
        text: str,
        vector: Sequence[float],
        document_id: str,
        page: int = 0,
        uuid: Optional[str] = None,
        extra_properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Insert a single vectorized chunk.

        Returns the object UUID.
        """
        self.ensure_schema()
        client = self.connect()
        weaviate = _import_weaviate()

        properties: Dict[str, Any] = {
            self.text_key: text,
            self.document_id_key: document_id,
            self.page_key: page,
        }
        if extra_properties:
            properties.update(extra_properties)

        if _is_v4_client(weaviate):
            collection = client.collections.get(self.collection)
            inserted_uuid = collection.data.insert(properties=properties, vector=list(vector), uuid=uuid)
            return str(inserted_uuid)

        # v3 insert
        return str(
            client.data_object.create(
                data_object=properties,
                class_name=self.collection,
                vector=list(vector),
                uuid=uuid,
            )
        )

    def add_many(
        self,
        *,
        items: Iterable[Tuple[str, Sequence[float], str, int, Optional[Dict[str, Any]]]],
    ) -> List[str]:
        """
        Batch insert.

        Each item is: (text, vector, document_id, page, extra_properties)
        """
        self.ensure_schema()
        client = self.connect()
        weaviate = _import_weaviate()

        if _is_v4_client(weaviate):
            collection = client.collections.get(self.collection)
            uuids: List[str] = []
            with collection.batch.dynamic() as batch:
                for text, vector, document_id, page, extra in items:
                    properties: Dict[str, Any] = {
                        self.text_key: text,
                        self.document_id_key: document_id,
                        self.page_key: page,
                    }
                    if extra:
                        properties.update(extra)
                    obj_uuid = batch.add_object(properties=properties, vector=list(vector))
                    if obj_uuid is not None:
                        uuids.append(str(obj_uuid))
            return uuids

        # v3 batch
        uuids = []
        with client.batch as batch:
            for text, vector, document_id, page, extra in items:
                properties: Dict[str, Any] = {
                    self.text_key: text,
                    self.document_id_key: document_id,
                    self.page_key: page,
                }
                if extra:
                    properties.update(extra)
                uuids.append(
                    str(
                        batch.add_data_object(
                            data_object=properties,
                            class_name=self.collection,
                            vector=list(vector),
                        )
                    )
                )
        return uuids

    def similarity_search(
        self,
        *,
        query_vector: Sequence[float],
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Return the top-k nearest objects by vector similarity.
        """
        client = self.connect()
        weaviate = _import_weaviate()

        if _is_v4_client(weaviate):
            from weaviate.classes.query import Filter, MetadataQuery  # type: ignore

            collection = client.collections.get(self.collection)
            query_filter = None
            for key, value in (filters or {}).items():
                current = Filter.by_property(key).equal(value)
                query_filter = current if query_filter is None else query_filter & current

            resp = collection.query.near_vector(
                near_vector=list(query_vector),
                limit=k,
                filters=query_filter,
                return_properties=[
                    self.text_key,
                    self.document_id_key,
                    self.page_key,
                    self.class_id_key,
                    self.material_id_key,
                ],
                return_metadata=MetadataQuery(distance=True),
            )

            results: List[SearchResult] = []
            for obj in resp.objects:
                # v4 distance: smaller is better. Convert to a "score" (higher better) only if you want;
                # here we keep it as distance to avoid guessing the scale.
                distance = None
                meta = getattr(obj, "metadata", None)
                if meta is not None:
                    distance = getattr(meta, "distance", None)
                results.append(SearchResult(uuid=str(obj.uuid), score=distance, properties=dict(obj.properties or {})))
            return results

        # v3 query
        q = (
            client.query.get(
                self.collection,
                [self.text_key, self.document_id_key, self.page_key, self.class_id_key, self.material_id_key],
            )
            .with_near_vector({"vector": list(query_vector)})
            .with_limit(k)
            .with_additional(["id", "distance"])
        )
        if filters:
            operands = []
            for key, value in filters.items():
                where_filter: Dict[str, Any] = {"path": [key], "operator": "Equal"}
                if isinstance(value, bool):
                    where_filter["valueBoolean"] = value
                elif isinstance(value, int):
                    where_filter["valueInt"] = value
                elif isinstance(value, float):
                    where_filter["valueNumber"] = value
                else:
                    where_filter["valueText"] = str(value)
                operands.append(where_filter)
            q = q.with_where(operands[0] if len(operands) == 1 else {"operator": "And", "operands": operands})
        data = q.do()
        out: List[SearchResult] = []
        for row in (data.get("data", {}).get("Get", {}).get(self.collection, []) or []):
            additional = row.get("_additional", {}) if isinstance(row, dict) else {}
            uuid = str(additional.get("id", ""))
            distance = additional.get("distance")
            properties = {k: v for k, v in (row or {}).items() if k != "_additional"}
            out.append(SearchResult(uuid=uuid, score=distance, properties=properties))
        return out

    def delete_by_material_id(self, material_id: int) -> None:
        """
        Delete all chunks associated with a material id.
        """
        self._delete_by_property(self.material_id_key, material_id)

    def delete_by_document_id(self, document_id: str) -> None:
        """
        Delete all chunks associated with a document id.
        """
        self._delete_by_property(self.document_id_key, document_id)

    def _delete_by_property(self, key: str, value: Any) -> None:
        self.ensure_schema()
        client = self.connect()
        weaviate = _import_weaviate()

        if _is_v4_client(weaviate):
            from weaviate.classes.query import Filter  # type: ignore

            collection = client.collections.get(self.collection)
            collection.data.delete_many(where=Filter.by_property(key).equal(value))
            return

        where_filter: Dict[str, Any] = {"path": [key], "operator": "Equal"}
        if isinstance(value, bool):
            where_filter["valueBoolean"] = value
        elif isinstance(value, int):
            where_filter["valueInt"] = value
        elif isinstance(value, float):
            where_filter["valueNumber"] = value
        else:
            where_filter["valueText"] = str(value)

        client.batch.delete_objects(class_name=self.collection, where=where_filter)


def get_vector_db() -> WeaviateVectorDB:
    url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    api_key = os.getenv("WEAVIATE_API_KEY") or None
    grpc_port = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
    collection = os.getenv("WEAVIATE_COLLECTION", "Document")

    return WeaviateVectorDB(url=url, api_key=api_key, grpc_port=grpc_port, collection=collection)
