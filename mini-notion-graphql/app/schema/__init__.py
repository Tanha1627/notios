import strawberry

from app.schema.queries import Query
from app.schema.mutations import Mutation

schema = strawberry.Schema(query=Query, mutation=Mutation)
