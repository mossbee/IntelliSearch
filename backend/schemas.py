from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language question")


class SourceInfo(BaseModel):
    file_path: str
    file_name: str
    file_type: str


class SearchResponse(BaseModel):
    answer: str
    source: SourceInfo
    matched_preview: str


class TreeNode(BaseModel):
    name: str
    path: str
    node_type: str
    children: list["TreeNode"] = Field(default_factory=list)


TreeNode.model_rebuild()
