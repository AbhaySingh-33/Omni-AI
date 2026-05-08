import hashlib
import re
from typing import Dict, List, Optional, Tuple

import pdfplumber
from pypdf import PdfReader

from legal_rag.models import LegalDocumentMeta, LegalNode, LegalReference


LEVEL_BY_TYPE = {
    "document": 0,
    "part": 1,
    "chapter": 2,
    "section": 3,
    "article": 3,
    "rule": 3,
    "subsection": 4,
    "clause": 5,
    "paragraph": 6,
}


HEADING_PATTERNS = [
    ("part", re.compile(r"^\s*(part)\s+([IVXLC0-9A-Za-z\-]+)\b[\.:\-\s]*(.*)$", re.IGNORECASE)),
    ("chapter", re.compile(r"^\s*(chapter|chap\.?)\s+([IVXLC0-9A-Za-z\-]+)\b[\.:\-\s]*(.*)$", re.IGNORECASE)),
    ("section", re.compile(r"^\s*(section|sec\.?)\s+([0-9A-Za-z\-\.]+)\b[\.:\-\s]*(.*)$", re.IGNORECASE)),
    ("article", re.compile(r"^\s*(article|art\.?)\s+([0-9A-Za-z\-\.]+)\b[\.:\-\s]*(.*)$", re.IGNORECASE)),
    ("rule", re.compile(r"^\s*(rule)\s+([0-9A-Za-z\-\.]+)\b[\.:\-\s]*(.*)$", re.IGNORECASE)),
    ("clause", re.compile(r"^\s*(clause)\s+([0-9A-Za-z\-\.]+)\b[\.:\-\s]*(.*)$", re.IGNORECASE)),
    ("subsection", re.compile(r"^\s*\(([0-9A-Za-z]+)\)\s+(.*)$", re.IGNORECASE)),
]


NUMBERED_LINE_PATTERN = re.compile(r"^\s*([0-9]+(?:\.[0-9]+){0,3})\s+(.+)$")
ACT_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9,&\-\s]{3,80}\sAct(?:,\s*\d{4})?)\b")
INTERNAL_REF_PATTERN = re.compile(r"\b(Section|Rule|Article|Clause)\s+([0-9A-Za-z\-\.]+)\b", re.IGNORECASE)

SECTION_KEYWORDS = {
    "document": ["document"],
    "part": ["part"],
    "chapter": ["chapter"],
    "section": ["section"],
    "article": ["article"],
    "rule": ["rule"],
    "subsection": ["subsection"],
    "clause": ["clause"],
    "paragraph": ["paragraph"],
}


def _normalize_text(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _make_node_id(doc_id: str, node_type: str, page: int, order_index: int) -> str:
    return f"{doc_id}:{node_type}:{page}:{order_index}"


def _detect_section_tag(title: str, text: str, default_tag: str = "general") -> str:
    # Section tags are intentionally structural, not keyword-driven by document type.
    haystack = _normalize_text(f"{title} {text}").lower()
    if not haystack:
        return default_tag
    for tag in SECTION_KEYWORDS.keys():
        if tag in haystack:
            return tag
    return default_tag


def _extract_citations(text: str) -> List[str]:
    snippets: List[str] = []
    for match in INTERNAL_REF_PATTERN.finditer(text or ""):
        snippets.append(_normalize_text(f"{match.group(1)} {match.group(2)}"))
    for match in ACT_PATTERN.finditer(text or ""):
        snippets.append(_normalize_text(match.group(1)))
    dedup = []
    for item in snippets:
        low = item.lower()
        if low not in [d.lower() for d in dedup]:
            dedup.append(item)
    return dedup[:16]


def _node_title_by_id(nodes: List[LegalNode], node_id: Optional[str]) -> str:
    if not node_id:
        return ""
    node = next((n for n in reversed(nodes) if n.node_id == node_id), None)
    return _normalize_text(node.title if node else "")


def _section_path_for_node(nodes: List[LegalNode], parent_id: Optional[str], title: str) -> str:
    parent_path = _path_for_node(nodes, parent_id)
    heading = _normalize_text(title)
    return f"{parent_path}/{heading}" if parent_path else heading


def _build_search_text(title: str, text: str, section_path: str, citations: List[str]) -> str:
    parts = [
        _normalize_text(title),
        _normalize_text(section_path),
        " ".join(citations),
        _normalize_text(text),
    ]
    return _normalize_text(" ".join([p for p in parts if p]))


def _extract_page_texts(file_path: str, reader: PdfReader) -> List[str]:
    page_texts: List[str] = []
    for page in reader.pages:
        page_texts.append((page.extract_text() or "").strip())

    # Fallback page-by-page with pdfplumber where pypdf produced empty text.
    if any(not text for text in page_texts):
        try:
            with pdfplumber.open(file_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    if idx >= len(page_texts):
                        break
                    if page_texts[idx]:
                        continue
                    fallback_text = (page.extract_text() or "").strip()
                    if fallback_text:
                        page_texts[idx] = fallback_text
        except Exception:
            # Best-effort fallback; keep parser resilient.
            pass

    return page_texts


def _match_heading(line: str) -> Optional[Tuple[str, Optional[str], str]]:
    cleaned = _normalize_text(line)
    if not cleaned:
        return None

    for node_type, pattern in HEADING_PATTERNS:
        match = pattern.match(cleaned)
        if not match:
            continue

        if node_type == "subsection":
            identifier = match.group(1)
            title = match.group(2)
            return node_type, identifier, title

        identifier = _normalize_text(match.group(2))
        tail = _normalize_text(match.group(3))
        title = tail if tail else cleaned
        return node_type, identifier, title

    generic_match = NUMBERED_LINE_PATTERN.match(cleaned)
    if generic_match:
        return "section", generic_match.group(1), _normalize_text(generic_match.group(2))

    return None


def _extract_references(node: LegalNode) -> List[LegalReference]:
    refs: List[LegalReference] = []
    search_space = f"{node.title}\n{node.text}".strip()
    if not search_space:
        return refs

    for match in INTERNAL_REF_PATTERN.finditer(search_space):
        kind = match.group(1).lower()
        identifier = _normalize_text(match.group(2))
        refs.append(
            LegalReference(
                user_id=node.user_id,
                doc_id=node.doc_id,
                source_node_id=node.node_id,
                ref_type=f"internal_{kind}",
                target_label=f"{kind}:{identifier}",
                target_node_id=None,
            )
        )

    for match in ACT_PATTERN.finditer(search_space):
        act_name = _normalize_text(match.group(1))
        refs.append(
            LegalReference(
                user_id=node.user_id,
                doc_id=node.doc_id,
                source_node_id=node.node_id,
                ref_type="external_act",
                target_label=act_name,
                target_node_id=None,
            )
        )

    dedup = {(r.ref_type, r.target_label): r for r in refs}
    return list(dedup.values())


def parse_legal_pdf(file_path: str, filename: str, user_id: str) -> Tuple[LegalDocumentMeta, List[LegalNode], List[LegalReference]]:
    with open(file_path, "rb") as handle:
        doc_id = hashlib.md5(handle.read()).hexdigest()

    reader = PdfReader(file_path)
    page_count = len(reader.pages)
    page_texts = _extract_page_texts(file_path, reader)

    meta = LegalDocumentMeta(user_id=user_id, doc_id=doc_id, filename=filename, page_count=page_count)
    nodes: List[LegalNode] = []

    root_id = _make_node_id(doc_id, "document", 1, 0)
    root = LegalNode(
        user_id=user_id,
        doc_id=doc_id,
        node_id=root_id,
        node_type="document",
        title=filename,
        text="",
        page_start=1,
        page_end=max(1, page_count),
        depth=0,
        order_index=0,
        path=filename,
        parent_id=None,
        identifier=None,
    )
    nodes.append(root)

    current_parent_at_depth: Dict[int, str] = {0: root_id}
    order_index = 1

    for page_idx, page_text in enumerate(page_texts, start=1):
        lines = [line for line in page_text.splitlines() if _normalize_text(line)]

        if not lines:
            continue

        paragraph_buffer: List[str] = []
        active_leaf_id = current_parent_at_depth.get(max(current_parent_at_depth.keys()), root_id)
        current_section_tag = "paragraph"

        def flush_paragraph() -> None:
            nonlocal order_index, paragraph_buffer, active_leaf_id, current_section_tag
            paragraph = _normalize_text(" ".join(paragraph_buffer))
            paragraph_buffer = []
            if len(paragraph) < 8:
                return

            parent_depth = 0
            parent_id = root_id
            if active_leaf_id:
                leaf = next((n for n in reversed(nodes) if n.node_id == active_leaf_id), None)
                if leaf is not None:
                    parent_depth = leaf.depth
                    parent_id = leaf.node_id

            current_order = order_index
            node_id = _make_node_id(doc_id, "paragraph", page_idx, current_order)
            order_index += 1
            node = LegalNode(
                user_id=user_id,
                doc_id=doc_id,
                node_id=node_id,
                node_type="paragraph",
                title=f"Paragraph p{page_idx}-{current_order}",
                text=paragraph,
                page_start=page_idx,
                page_end=page_idx,
                depth=min(parent_depth + 1, 6),
                order_index=current_order,
                path="",
                section_tag="paragraph",
                parent_id=parent_id,
                identifier=None,
            )
            node.path = f"{_path_for_node(nodes, node.parent_id)}/{node.node_type}:{node.title}"
            node.section_path = _section_path_for_node(nodes, node.parent_id, node.title)
            node.citations = _extract_citations(paragraph)
            node.search_text = _build_search_text(node.title, node.text, node.section_path, node.citations)
            nodes.append(node)
            active_leaf_id = node_id

        for line in lines:
            line_section = _detect_section_tag(line, "", default_tag=current_section_tag)
            current_section_tag = line_section
            heading = _match_heading(line)
            if heading:
                flush_paragraph()
                node_type, identifier, title = heading
                depth = LEVEL_BY_TYPE.get(node_type, 6)

                # Trim stale deeper parents when we open a same/higher-level node.
                for existing_depth in list(current_parent_at_depth.keys()):
                    if existing_depth >= depth:
                        current_parent_at_depth.pop(existing_depth, None)

                parent_depth = depth - 1
                while parent_depth > 0 and parent_depth not in current_parent_at_depth:
                    parent_depth -= 1
                parent_id = current_parent_at_depth.get(parent_depth, root_id)

                current_order = order_index
                node_id = _make_node_id(doc_id, node_type, page_idx, current_order)
                order_index += 1
                node = LegalNode(
                    user_id=user_id,
                    doc_id=doc_id,
                    node_id=node_id,
                    node_type=node_type,
                    title=_normalize_text(title) or _normalize_text(line),
                    text="",
                    page_start=page_idx,
                    page_end=page_idx,
                    depth=depth,
                    order_index=current_order,
                    path="",
                    section_tag=node_type,
                    parent_id=parent_id,
                    identifier=identifier,
                )
                node.path = f"{_path_for_node(nodes, parent_id)}/{node.node_type}:{node.title}"
                node.section_path = _section_path_for_node(nodes, parent_id, node.title)
                node.citations = _extract_citations(f"{node.title} {line}")
                node.search_text = _build_search_text(node.title, node.text, node.section_path, node.citations)
                nodes.append(node)
                current_parent_at_depth[depth] = node_id
                active_leaf_id = node_id
            else:
                paragraph_buffer.append(line)

        flush_paragraph()

    # Include fallback content if strict parsing did not produce enough leaf nodes.
    if len(nodes) <= 1:
        fallback_text = "\n".join([text for text in page_texts if text]).strip()
        if fallback_text:
            node_id = _make_node_id(doc_id, "paragraph", 1, order_index)
            node = LegalNode(
                user_id=user_id,
                doc_id=doc_id,
                node_id=node_id,
                node_type="paragraph",
                title="Document Body",
                text=fallback_text,
                page_start=1,
                page_end=max(1, page_count),
                depth=1,
                order_index=order_index,
                path=f"{filename}/paragraph:Document Body",
                section_tag="paragraph",
                parent_id=root_id,
                identifier=None,
            )
            node.section_path = _section_path_for_node(nodes, root_id, node.title)
            node.citations = _extract_citations(fallback_text)
            node.search_text = _build_search_text(node.title, node.text, node.section_path, node.citations)
            nodes.append(node)

    # Last-resort page-level nodes to ensure retrievable content if parsing stayed too sparse.
    if len(nodes) <= 1:
        for page_idx, text in enumerate(page_texts, start=1):
            normalized = _normalize_text(text)
            if not normalized:
                continue
            current_order = order_index
            node_id = _make_node_id(doc_id, "paragraph", page_idx, current_order)
            order_index += 1
            node = LegalNode(
                user_id=user_id,
                doc_id=doc_id,
                node_id=node_id,
                node_type="paragraph",
                title=f"Page {page_idx}",
                text=normalized,
                page_start=page_idx,
                page_end=page_idx,
                depth=1,
                order_index=current_order,
                path=f"{filename}/paragraph:Page {page_idx}",
                section_tag="paragraph",
                parent_id=root_id,
                identifier=None,
            )
            node.section_path = _section_path_for_node(nodes, root_id, node.title)
            node.citations = _extract_citations(normalized)
            node.search_text = _build_search_text(node.title, node.text, node.section_path, node.citations)
            nodes.append(node)

    references: List[LegalReference] = []
    internal_lookup = _build_internal_lookup(nodes)
    for node in nodes:
        if node.node_type == "document":
            continue
        for ref in _extract_references(node):
            if ref.ref_type.startswith("internal_"):
                ref.target_node_id = internal_lookup.get(ref.target_label.lower())
            references.append(ref)

    return meta, nodes, references


def _path_for_node(nodes: List[LegalNode], node_id: Optional[str]) -> str:
    if not node_id:
        return ""
    node = next((n for n in reversed(nodes) if n.node_id == node_id), None)
    if not node:
        return ""
    return node.path


def _build_internal_lookup(nodes: List[LegalNode]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for node in nodes:
        if not node.identifier:
            continue
        key = f"{node.node_type}:{node.identifier}".lower()
        if key not in lookup:
            lookup[key] = node.node_id
    return lookup
