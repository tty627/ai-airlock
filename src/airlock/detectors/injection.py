"""High-recall prompt-injection and data-exfiltration heuristics."""

from __future__ import annotations

import re
from collections.abc import Iterator

from .models import Action, InternalFinding, Sensitivity, Span, line_number

_HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")
_NONEMPTY_LINE = re.compile(r"[^\r\n]+")
_MAX_SEMANTIC_WINDOW_LINES = 4
_MAX_SEMANTIC_WINDOW_CHARS = 512

_BENIGN_QUOTED_EXAMPLE = re.compile(
    r"\b(?:phrases?|strings?|text)\s+such\s+as\s+"
    r"(?P<quote>['\"])[^'\"\r\n]{1,160}(?P=quote)",
    re.IGNORECASE,
)

_DEFENSIVE_NEGATION = re.compile(
    r"\b(?:do\s+not|don't|never|must\s+not|should\s+not)\s+"
    r"(?:bypass|circumvent|disable|turn\s+off|execute|inspect|open|read|use|access|"
    r"ignore|disregard|forget|discard|put|place|include|print|reveal|return|send|"
    r"upload|exfiltrate)\b"
    r"(?:(?!\b(?:but|however|instead|then|yet|except)\b)[^.;\r\n])*(?:[.;]|$)",
    re.IGNORECASE,
)

_DEFENSIVE_NONDISCLOSURE = re.compile(
    r"(?:"
    r"\b(?:secrets?|credentials?|tokens?|private\s+keys?|access\s+keys?|"
    r"api\s+keys?|passwords?)\b.{0,50}\b(?:must|should)\s+(?:never|not)\s+"
    r"(?:appear|be\s+(?:put|placed|included|printed|returned|revealed|exposed|sent|"
    r"uploaded))\b"
    r"|"
    r"\b(?:do\s+not|don't|never|must\s+not|should\s+not)\s+"
    r"(?:put|place|include|print|return|reveal|expose|send|upload)\b.{0,80}"
    r"\b(?:secrets?|credentials?|tokens?|private\s+keys?|access\s+keys?|"
    r"api\s+keys?|passwords?)\b"
    r")"
    r"(?:(?!\b(?:but|however|instead|then|yet|except)\b)[^.;\r\n])*(?:[.;]|$)",
    re.IGNORECASE,
)

_CHINESE_DEFENSIVE_NEGATION = re.compile(
    r"(?:不要|不得|禁止).{0,12}(?:绕过|跳过|规避|关闭|停用|执行|读取|查看|打开|"
    r"使用|访问|返回|发送|上传|外传)"
    r"(?:(?!(?:但|然而|然后|改为|反而))[^。；\r\n])*(?:[。；]|$)"
)

_STRONG_BOUNDARY_BYPASS_PATTERNS = (
    re.compile(
        r"\b(?:do\s+not|don't)\s+(?:use|rely\s+on|trust)\b.{0,70}"
        r"\b(?:safe[_\s-]*context|capsule|saniti[sz](?:e|ed|er|ing|ation)?\s+view|"
        r"airlock)\b.{0,180}\b(?:open|read|inspect|access|use|work)\b.{0,100}"
        r"\b(?:raw|original|untouched|unfiltered|unsanitized|unprocessed)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:不要依赖|不要使用|无需遵守).{0,30}(?:安全上下文|气闸|Airlock|Capsule)"
        r".{0,80}(?:直接)?(?:读取|查看|打开|使用|访问).{0,40}"
        r"(?:原始|原文|未净化|未过滤|未脱敏)"
    ),
)

_INJECTION_PATTERNS = (
    re.compile(
        r"\b(?:ignore|disregard|forget|discard)\b.{0,60}"
        r"\b(?:all\s+)?(?:previous|prior|earlier)\s+instructions?\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bsystem\s+override\b", re.IGNORECASE),
    re.compile(
        r"\boverride\b.{0,40}\b(?:policy|safety|instructions?|guardrails?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bdisable\b.{0,40}\b(?:safety|security|guardrails?)\b", re.IGNORECASE),
    re.compile(r"\bexecute\b.{0,30}\bcommands?\b", re.IGNORECASE),
    re.compile(r"\bhidden\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(?:the\s+)?system\b", re.IGNORECASE),
    re.compile(r"\bdo\s+not\s+obey\b", re.IGNORECASE),
    re.compile(
        r"\b(?:previous|earlier|prior)\b.{0,60}"
        r"\b(?:instructions?|guidance|directions?|requests?)\b.{0,60}"
        r"\b(?:obsolete|invalid|superseded|no\s+longer\s+(?:valid|authoritative))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:disregard|ignore)\b.{0,60}\b(?:user(?:'s)?\s+task|requested\s+analysis)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:turn|switch)\s+off\b.{0,40}"
        r"\b(?:sanitizer|filtering|redaction|safety|security|guardrails?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bsafety\s+filtering\b.{0,30}\bdisabled\b", re.IGNORECASE),
    re.compile(r"\brestore\b.{0,50}\b(?:redacted|masked)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:bypass|circumvent|evade|skip|work\s+around|route\s+around)\b.{0,100}"
        r"\b(?:saniti[sz](?:e|ed|er|ing|ation)?|redaction|filter(?:ing|ed)?|"
        r"(?:cleaned|filtered|redacted)\s+(?:view|copy|context|output|capsule)|"
        r"safe[_\s-]*context(?:\s+capsule)?|airlock)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:saniti[sz](?:ed|ation)?\s+(?:view|layer|output)|"
        r"(?:cleaned|filtered|redacted)\s+(?:view|copy|context|output|capsule)|"
        r"safe[_\s-]*context(?:\s+capsule)?|airlock)\b.{0,90}"
        r"\b(?:only\s+advisory|merely\s+advisory|optional|not\s+authoritative|"
        r"can\s+be\s+ignored|should\s+be\s+bypassed)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:inspect|open|read|use|access|consult|search|index|"
        r"work\s+(?:directly\s+)?from)\b.{0,100}"
        r"\b(?:raw|original|untouched|unfiltered|unsanitized|unprocessed|"
        r"pre[-\s]?filtered?)\b.{0,80}"
        r"\b(?:workspace|repository|files?|documents?|sources?|material|contents?|data)\b"
        r".{0,70}\b(?:directly|instead|rather\s+than|before\s+(?:answering|responding)|"
        r"authoritative|source\s+of\s+truth)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:inspect|open|read|use|access|consult|work\s+(?:directly\s+)?from)\b"
        r".{0,90}\b(?:workspace|repository|files?|documents?|sources?|material|contents?|data)\b"
        r".{0,90}\b(?:raw|original|untouched|unfiltered|unsanitized|unprocessed)\b"
        r".{0,70}\b(?:directly|instead|rather\s+than|before\s+(?:answering|responding)|"
        r"authoritative|source\s+of\s+truth)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:之前|先前|此前).{0,40}(?:要求|指示|指令|指导).{0,40}"
        r"(?:失效|作废|过时|不再(?:有效|具有权威))"
    ),
    re.compile(
        r"(?:绕过|跳过|规避|避开|关闭|停用).{0,40}"
        r"(?:净化|清洗|脱敏|过滤|安全上下文|气闸|Airlock|Capsule)"
    ),
    re.compile(
        r"(?:直接)?(?:读取|查看|打开|使用|访问).{0,40}"
        r"(?:原始|原文|未净化|未过滤|未脱敏).{0,40}"
        r"(?:工作区|仓库|文件|源码|内容|数据).{0,30}(?:直接|据此|回答|权威)"
    ),
)

_EXFILTRATION_PATTERNS = (
    re.compile(
        r"\b(?:reveal|expose|return|print|copy|include|send|transmit|upload|post|"
        r"exfiltrate)\b.{0,160}"
        r"\b(?:secrets?|credentials?|tokens?|private\s+keys?|access\s+keys?|"
        r"secret\s+keys?|api\s+tokens?|passwords?|db_password|"
        r"environment\s+variables?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:\b(?:secrets?|credentials?|tokens?|private\s+keys?|access\s+keys?|"
        r"secret\s+keys?|api\s+tokens?|passwords?|db_password|"
        r"environment\s+variables?)\b|"
        r"(?:^|[\s'\"])(?:~/|/[^\s]*)?\.(?:ssh|aws)(?:/|\b))"
        r".{0,180}\b(?:reveal|expose|return|print|copy|include|send|transmit|"
        r"upload|post|exfiltrate|final\s+answer|response|external|dns\s+lookups?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:检查|读取|查找|收集|提取|复制).{0,80}"
        r"(?:凭证|密钥|私钥|密码|令牌).{0,100}"
        r"(?:发送|上传|外传|公开|暴露|返回|输出)"
    ),
)


def _mask_benign_security_context(chunk: str) -> str:
    masked = _BENIGN_QUOTED_EXAMPLE.sub(lambda match: " " * len(match.group(0)), chunk)
    masked = _DEFENSIVE_NONDISCLOSURE.sub(lambda match: " " * len(match.group(0)), masked)
    masked = _DEFENSIVE_NEGATION.sub(lambda match: " " * len(match.group(0)), masked)
    return _CHINESE_DEFENSIVE_NEGATION.sub(lambda match: " " * len(match.group(0)), masked)


def _has_benign_security_scope(chunk: str) -> bool:
    return any(
        pattern.search(chunk)
        for pattern in (
            _BENIGN_QUOTED_EXAMPLE,
            _DEFENSIVE_NONDISCLOSURE,
            _DEFENSIVE_NEGATION,
            _CHINESE_DEFENSIVE_NEGATION,
        )
    )


def _semantic_projection(chunk: str) -> str:
    return re.sub(r"[\t\r\n ]+", " ", chunk).strip()


def _categories(chunk: str) -> tuple[str, ...]:
    strong_boundary_bypass = any(
        pattern.search(chunk) for pattern in _STRONG_BOUNDARY_BYPASS_PATTERNS
    )
    candidate = _mask_benign_security_context(chunk)
    categories: list[str] = []
    if strong_boundary_bypass or any(pattern.search(candidate) for pattern in _INJECTION_PATTERNS):
        categories.append("injection")
    if any(pattern.search(candidate) for pattern in _EXFILTRATION_PATTERNS):
        categories.append("data_exfiltration")
    return tuple(categories)


def _finding(*, category: str, source: str, text: str, start: int, end: int) -> InternalFinding:
    exfiltration = category == "data_exfiltration"
    return InternalFinding(
        finding_type="DATA_EXFILTRATION" if exfiltration else "PROMPT_INJECTION",
        severity="critical" if exfiltration else "high",
        source=source,
        line=line_number(text, start),
        detector="heuristic",
        action=Action.ISOLATE,
        sensitivity=Sensitivity.UNTRUSTED_INSTRUCTION,
        span=Span(start, end),
        category=category,
    )


def _overlaps_any(span: Span, intervals: list[Span]) -> bool:
    return any(span.overlaps(interval) for interval in intervals)


def _iter_injection_findings(text: str, source: str) -> Iterator[InternalFinding]:
    risky_comments: list[Span] = []
    for match in _HTML_COMMENT.finditer(text):
        categories = _categories(_semantic_projection(match.group(0)))
        if not categories:
            continue
        interval = Span(*match.span())
        risky_comments.append(interval)
        for category in categories:
            yield _finding(
                category=category,
                source=source,
                text=text,
                start=interval.start,
                end=interval.end,
            )

    lines = [match for match in _NONEMPTY_LINE.finditer(text) if match.group(0).strip()]
    line_categories = [_categories(match.group(0)) for match in lines]
    risky_windows: list[tuple[Span, tuple[str, ...]]] = []
    benign_windows: list[Span] = []
    for size in range(2, _MAX_SEMANTIC_WINDOW_LINES + 1):
        for start_index in range(0, len(lines) - size + 1):
            window = lines[start_index : start_index + size]
            interval = Span(window[0].start(), window[-1].end())
            if interval.length > _MAX_SEMANTIC_WINDOW_CHARS:
                continue
            projection = _semantic_projection(text[interval.start : interval.end])
            categories = _categories(projection)
            if not categories and _has_benign_security_scope(projection):
                benign_windows.append(interval)
                continue
            individual = {
                category
                for line_index in range(start_index, start_index + size)
                for category in line_categories[line_index]
            }
            window_categories = tuple(
                category
                for category in categories
                if category not in individual
                or sum(
                    category in line_categories[line_index]
                    for line_index in range(start_index, start_index + size)
                )
                > 1
            )
            if not window_categories or any(
                interval.overlaps(existing) for existing, _ in risky_windows
            ):
                continue
            risky_windows.append((interval, window_categories))

    for interval, categories in risky_windows:
        if _overlaps_any(interval, risky_comments):
            continue
        for category in categories:
            yield _finding(
                category=category,
                source=source,
                text=text,
                start=interval.start,
                end=interval.end,
            )

    risky_intervals = [interval for interval, _ in risky_windows]
    for match, categories in zip(lines, line_categories, strict=True):
        interval = Span(*match.span())
        if _overlaps_any(interval, [*risky_comments, *risky_intervals]):
            continue
        if _overlaps_any(interval, benign_windows):
            continue
        for category in categories:
            yield _finding(
                category=category,
                source=source,
                text=text,
                start=interval.start,
                end=interval.end,
            )


def detect_injections(text: str, source: str = "<input>") -> list[InternalFinding]:
    """Classify risky comments/lines without retaining their contents."""

    return list(_iter_injection_findings(text, source))
