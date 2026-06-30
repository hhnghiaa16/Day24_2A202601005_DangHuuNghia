from pathlib import Path

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider

VI_LANGUAGE = "vi"
VI_MODEL_CANDIDATES = ("vi_core_news_lg", "vi_spacy_model")
SUPPORTED_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]


def _pattern_recognizer(
    entity: str,
    name: str,
    regex: str,
    score: float,
    context: list[str] | None = None,
) -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity=entity,
        supported_language=VI_LANGUAGE,
        patterns=[Pattern(name=name, regex=regex, score=score)],
        context=context or [],
    )


def _resolve_vi_model_name() -> str:
    import spacy

    for model_name in VI_MODEL_CANDIDATES:
        try:
            spacy.load(model_name)
            return model_name
        except OSError:
            continue
    return ""


def _blank_vi_model_path() -> str:
    import spacy

    blank_path = Path.cwd() / ".spacy_models" / "vi_blank"
    if not blank_path.exists():
        blank_path.parent.mkdir(parents=True, exist_ok=True)
        spacy.blank(VI_LANGUAGE).to_disk(blank_path)
    return str(blank_path)


def build_vietnamese_analyzer() -> AnalyzerEngine:
    cccd_recognizer = _pattern_recognizer(
        entity="VN_CCCD",
        name="cccd_pattern",
        regex=r"\b\d{11,12}\b",
        score=0.9,
        context=["cccd", "can cuoc", "chung minh", "cmnd"],
    )

    phone_recognizer = _pattern_recognizer(
        entity="VN_PHONE",
        name="vn_phone",
        regex=r"\b0?[35789]\d{8}\b",
        score=0.85,
        context=["dien thoai", "sdt", "phone", "lien he"],
    )

    email_recognizer = _pattern_recognizer(
        entity="EMAIL_ADDRESS",
        name="email_pattern",
        regex=r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        score=0.9,
        context=["email", "mail", "gmail"],
    )

    person_recognizer = _pattern_recognizer(
        entity="PERSON",
        name="vn_person_name",
        regex=r"\b[^\W\d_]+(?:\s+[^\W\d_]+){1,4}\b",
        score=0.65,
        context=["benh nhan", "bac si", "ho ten", "patient"],
    )

    model_name = _resolve_vi_model_name() or _blank_vi_model_path()
    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": VI_LANGUAGE, "model_name": model_name}],
        }
    )
    nlp_engine = provider.create_engine()

    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=[VI_LANGUAGE],
    )
    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(email_recognizer)
    analyzer.registry.add_recognizer(person_recognizer)
    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    if text is None:
        return []

    return analyzer.analyze(
        text=str(text),
        language=VI_LANGUAGE,
        entities=SUPPORTED_ENTITIES,
    )
