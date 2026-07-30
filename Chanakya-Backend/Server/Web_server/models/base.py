"""
Beanie-compatible PostgresDocument base class.
Uses asyncpg to query PostgreSQL.
"""
import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, Field

T = TypeVar("T", bound="PostgresDocument")

class QueryCondition:
    def __init__(self, field: str, op: str, value: Any):
        self.field = field
        self.op = op
        self.value = value

class SortInstruction:
    def __init__(self, field: str, direction: str):
        self.field = field
        self.direction = direction

class FieldOperator:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other) -> QueryCondition:
        return QueryCondition(self.name, "=", other)

    def __ne__(self, other) -> QueryCondition:
        return QueryCondition(self.name, "!=", other)

    def __gt__(self, other) -> QueryCondition:
        return QueryCondition(self.name, ">", other)

    def __lt__(self, other) -> QueryCondition:
        return QueryCondition(self.name, "<", other)

    def __ge__(self, other) -> QueryCondition:
        return QueryCondition(self.name, ">=", other)

    def __le__(self, other) -> QueryCondition:
        return QueryCondition(self.name, "<=", other)

    def __neg__(self) -> SortInstruction:
        return SortInstruction(self.name, "DESC")

class FieldDescriptor:
    def __init__(self, name: str):
        self.name = name

    def __get__(self, instance, owner):
        if instance is not None:
            return instance.__dict__.get(self.name)
        return FieldOperator(self.name)

class PostgresQueryBuilder:
    def __init__(self, model_cls: Type[T], conditions: List[Union[QueryCondition, Any]] = None):
        self.model_cls = model_cls
        self.conditions = []
        if conditions:
            for cond in conditions:
                if isinstance(cond, QueryCondition):
                    self.conditions.append(cond)
        self._sorts: List[SortInstruction] = []
        self._skip: Optional[int] = None
        self._limit: Optional[int] = None

    def sort(self, *sort_args) -> "PostgresQueryBuilder":
        for arg in sort_args:
            if isinstance(arg, SortInstruction):
                self._sorts.append(arg)
            elif isinstance(arg, FieldOperator):
                self._sorts.append(SortInstruction(arg.name, "ASC"))
            elif isinstance(arg, str):
                if arg.startswith("-"):
                    self._sorts.append(SortInstruction(arg[1:], "DESC"))
                else:
                    self._sorts.append(SortInstruction(arg, "ASC"))
        return self

    def skip(self, skip: int) -> "PostgresQueryBuilder":
        self._skip = skip
        return self

    def limit(self, limit: int) -> "PostgresQueryBuilder":
        self._limit = limit
        return self

    def _build_where(self, start_param: int = 1) -> tuple[str, List[Any]]:
        if not self.conditions:
            return "", []
        
        where_clauses = []
        params = []
        param_idx = start_param
        
        for cond in self.conditions:
            field = cond.field
            op = cond.op
            val = cond.value
            
            if val is None:
                if op == "=":
                    where_clauses.append(f"{field} IS NULL")
                else:
                    where_clauses.append(f"{field} IS NOT NULL")
            else:
                where_clauses.append(f"{field} {op} ${param_idx}")
                params.append(val)
                param_idx += 1
                
        return " WHERE " + " AND ".join(where_clauses), params

    async def to_list(self) -> List[T]:
        table_name = self.model_cls.get_table_name()
        where_clause, params = self._build_where()
        
        query = f"SELECT * FROM {table_name}" + where_clause
        
        if self._sorts:
            sort_clauses = [f"{s.field} {s.direction}" for s in self._sorts]
            query += " ORDER BY " + ", ".join(sort_clauses)
            
        if self._limit is not None:
            query += f" LIMIT {self._limit}"
        if self._skip is not None:
            query += f" OFFSET {self._skip}"
            
        from database import db
        if not db.pool:
            raise RuntimeError("Database pool not initialized.")
            
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
        results = []
        for row in rows:
            results.append(self.model_cls(**dict(row)))
        return results

    async def count(self) -> int:
        table_name = self.model_cls.get_table_name()
        where_clause, params = self._build_where()
        query = f"SELECT COUNT(*) FROM {table_name}" + where_clause
        
        from database import db
        if not db.pool:
            raise RuntimeError("Database pool not initialized.")
            
        async with db.pool.acquire() as conn:
            val = await conn.fetchval(query, *params)
        return val or 0

    async def delete(self) -> Any:
        table_name = self.model_cls.get_table_name()
        where_clause, params = self._build_where()
        query = f"DELETE FROM {table_name}" + where_clause
        
        from database import db
        if not db.pool:
            raise RuntimeError("Database pool not initialized.")
            
        async with db.pool.acquire() as conn:
            result = await conn.execute(query, *params)
        return result

class PostgresDocument(BaseModel):
    id: Optional[str] = None

    @classmethod
    async def get(cls: Type[T], document_id: Any) -> Optional[T]:
        if document_id is None:
            return None
        return await cls.find_one(cls.id == str(document_id))

    @classmethod
    def get_table_name(cls) -> str:
        if hasattr(cls, "Settings") and hasattr(cls.Settings, "name"):
            return cls.Settings.name
        return cls.__name__.lower() + "s"

    @classmethod
    def find(cls: Type[T], *criteria) -> PostgresQueryBuilder:
        return PostgresQueryBuilder(cls, list(criteria))

    @classmethod
    def find_all(cls: Type[T]) -> PostgresQueryBuilder:
        return PostgresQueryBuilder(cls, [])

    @classmethod
    async def find_one(cls: Type[T], *criteria) -> Optional[T]:
        builder = PostgresQueryBuilder(cls, list(criteria)).limit(1)
        res = await builder.to_list()
        return res[0] if res else None

    @classmethod
    async def count(cls) -> int:
        return await cls.find_all().count()

    async def insert(self: T) -> T:
        table_name = self.get_table_name()
        if not self.id:
            self.id = uuid.uuid4().hex[:24]
            
        fields_to_insert = []
        values = []
        
        model_dict = self.model_dump()
        for field, val in model_dict.items():
            fields_to_insert.append(field)
            values.append(val)
                
        placeholders = ", ".join([f"${i}" for i in range(1, len(fields_to_insert) + 1)])
        columns = ", ".join(fields_to_insert)
        
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON CONFLICT (id) DO UPDATE SET "
        update_clauses = []
        for i, field in enumerate(fields_to_insert):
            if field != "id":
                update_clauses.append(f"{field} = ${i+1}")
        query += ", ".join(update_clauses)
        
        from database import db
        if not db.pool:
            raise RuntimeError("Database pool not initialized.")
            
        async with db.pool.acquire() as conn:
            await conn.execute(query, *values)
            
        return self

    async def save(self: T) -> T:
        return await self.insert()

    async def delete(self: T) -> Any:
        if not self.id:
            return None
        table_name = self.get_table_name()
        query = f"DELETE FROM {table_name} WHERE id = $1"
        
        from database import db
        if not db.pool:
            raise RuntimeError("Database pool not initialized.")
            
        async with db.pool.acquire() as conn:
            result = await conn.execute(query, self.id)
        return result

def init_postgres_models(models: List[Type[PostgresDocument]]):
    """Dynamically set descriptors on field attributes for class-level query comparisons."""
    for model in models:
        for field_name in model.model_fields.keys():
            setattr(model, field_name, FieldDescriptor(field_name))
