from dataclasses import dataclass
from dataclasses import field
from typing import List, Optional


@dataclass
class LegalDocumentMeta:
    user_id: str
    doc_id: str
    filename: str
    page_count: int


@dataclass
class LegalNode:
    user_id: str
    doc_id: str
    node_id: str
    node_type: str
    title: str
    text: str
    page_start: int
    page_end: int
    depth: int
    order_index: int
    path: str
    section_tag: str = "general"
    section_path: str = ""
    search_text: str = ""
    citations: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    identifier: Optional[str] = None


@dataclass
class LegalReference:
    user_id: str
    doc_id: str
    source_node_id: str
    ref_type: str
    target_label: str
    target_node_id: Optional[str] = None
