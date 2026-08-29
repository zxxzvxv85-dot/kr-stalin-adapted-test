#!/usr/bin/env python3
"""Audit missing HOI4 localisation keys and fill them through Bing Translator.

Only keys present in this mod's Simplified Chinese localisation but absent from
the selected language across the mod, its declared dependencies, and vanilla
are emitted. HOI4 formatting tokens are protected during translation.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import http.cookiejar
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from pathlib import Path


LOC_LINE_RE = re.compile(r'^\s*([^#\s][^:]*?):(?:\d+)?\s+"(.*)"\s*$')
LANG_HEADER_RE = re.compile(r'^\ufeff?\s*l_([a-z_]+)\s*:\s*$')
PROTECTED_RE = re.compile(
    r'\\n|§[A-Za-z0-9!]|£[A-Za-z0-9_]+|\[[^\]\r\n]+\]|\$[^$\r\n]+\$'
)
TOKEN_RE = re.compile(r'\{(\d{1,4})\}')

ENGLISH_SOURCE_GLOSSARY = OrderedDict(
    [
        ("联邦军备与国防工业委员会", "Federal Armaments and Defence Industry Commission"),
        ("全俄罗斯劳工联盟", "All-Russian Labour Union"),
        ("工农红军", "Workers' and Peasants' Red Army"),
        ("国家军事委员会", "State Military Commission"),
        ("革命军事委员会", "Revolutionary Military Council"),
        ("军事改革物资", "Military Reform Materiel"),
        ("特里安达菲洛夫", "Triandafillov"),
        ("沙波什尼科夫", "Shaposhnikov"),
        ("图哈切夫斯基", "Tukhachevsky"),
        ("斯维尔德洛夫", "Sverdlov"),
        ("季诺维也夫", "Zinoviev"),
        ("斯皮里多诺娃", "Spiridonova"),
        ("斯特鲁米林", "Strumilin"),
        ("布柳哈诺夫", "Bryukhanov"),
        ("卡冈诺维奇", "Kaganovich"),
        ("华西列夫斯基", "Vasilevsky"),
        ("铁木辛哥", "Timoshenko"),
        ("朱加什维利", "Dzhugashvili"),
        ("弗兰格尔", "Wrangel"),
        ("伏罗希洛夫", "Voroshilov"),
        ("最高纲领派", "Maximalists"),
        ("社会革命党", "Socialist Revolutionary Party"),
        ("国际主义者", "Internationalists"),
        ("布尔什维克", "Bolsheviks"),
        ("加米涅夫", "Kamenev"),
        ("乌斯季诺夫", "Ustinov"),
        ("萨文科夫", "Savinkov"),
        ("日丹诺夫", "Zhdanov"),
        ("托姆斯基", "Tomsky"),
        ("伏龙芝", "Frunze"),
        ("布琼尼", "Budyonny"),
        ("斯大林", "Stalin"),
        ("列宁", "Lenin"),
        ("托洛茨基", "Trotsky"),
        ("俄共（布）", "RCP(b)"),
        ("共产主义者", "Communists"),
        ("五年计划", "Five-Year Plan"),
        ("大纵深", "Deep Operations"),
        ("雷雨", "Thunderstorm"),
        ("红军", "Red Army"),
        ("国策", "focus"),
    ]
)

MANUAL_TRANSLATIONS = {
    "english": {
        "RUS_fr_frunze_defence_report": "Timoshenko's Army Reorganisation Report",
        "RUS_fr_unified_military_leadership": "Commander Responsibility System",
    },
    "russian": {
        "RUS_fr_dashboard_achievements_stage_0": "§WВоенный совет сформирован§!\\n§WОфицеры-эмигранты собраны§!",
        "RUS_fr_frunze_defence_report": "Доклад Тимошенко о реорганизации армии",
        "RUS_fr_unified_military_leadership": "Единоначалие",
        "RUS_fr_topbar_military_reform_materials_tt": "£GFX_RUS_fr_military_reform_materials §YМатериальные средства военной реформы§!\\n\\nБазовый ежедневный прирост составляет §G+1,00§!. Каждый достигнутый рубеж очков §YПервого пятилетнего плана§! добавляет §G+0,05§!. Завершение фокусов §Y«Единое командование и организация»§! и §Y«Народная и революционная армия»§! повышает предел запасов на §Y10§! каждый.\\n\\nПри выборе §YФедеральной комиссии по вооружениям и оборонной промышленности§! или расположенного ниже неё фокуса достаточный запас материальных средств расходуется для его немедленного завершения. Если средств недостаточно, фокус выполняется обычным образом.",
    },
}

KEYED_REPLACEMENTS = {
    "english": {
        "RUS_fr_reform_disorganisation_4_desc": [("General Vlassov", "General Vasilevsky")],
        "RUS_fr_armaments_report_conclusion_armaments": [("the保障 of", "the supply of")],
    },
    "russian": {
        "RUS_fr_reform_disorganisation_4_desc": [("генерала Власова", "генерала Василевского")],
        "RUS_fr_military_reform.53.d": [("基层ных подразделений", "низовых подразделений")],
    },
}


def prepare_english_source(text: str) -> str:
    for chinese, english in ENGLISH_SOURCE_GLOSSARY.items():
        text = text.replace(chinese, english)
    return text


def read_language(root: Path, language: str) -> OrderedDict[str, tuple[str, Path]]:
    result: OrderedDict[str, tuple[str, Path]] = OrderedDict()
    loc_root = root / "localisation"
    if not loc_root.exists():
        return result

    regular = sorted(p for p in loc_root.rglob("*.yml") if "replace" not in p.parts)
    replacement = sorted((loc_root / "replace").rglob("*.yml")) if (loc_root / "replace").exists() else []
    for path in [*regular, *replacement]:
        if path.name.startswith("RUS_test_missing_l_"):
            continue
        text = path.read_text(encoding="utf-8-sig")
        lines = text.splitlines()
        if not lines:
            continue
        header = LANG_HEADER_RE.match(lines[0])
        if not header or header.group(1) != language:
            continue
        for line in lines[1:]:
            match = LOC_LINE_RE.match(line)
            if match:
                result[match.group(1).strip()] = (match.group(2), path)
    return result


def read_localisation_file(path: Path, language: str) -> OrderedDict[str, tuple[str, Path]]:
    result: OrderedDict[str, tuple[str, Path]] = OrderedDict()
    if not path.exists():
        return result
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines:
        return result
    header = LANG_HEADER_RE.match(lines[0])
    if not header or header.group(1) != language:
        return result
    for line in lines[1:]:
        match = LOC_LINE_RE.match(line)
        if match:
            result[match.group(1).strip()] = (match.group(2), path)
    return result


def protect_hoi4_tokens(text: str) -> tuple[str, list[str]]:
    tokens: list[str] = []

    def replace(match: re.Match[str]) -> str:
        index = len(tokens)
        tokens.append(match.group(0))
        return f"{{{index}}}"

    return PROTECTED_RE.sub(replace, text), tokens


def restore_hoi4_tokens(text: str, tokens: list[str]) -> str:
    seen: set[int] = set()

    def replace(match: re.Match[str]) -> str:
        index = int(match.group(1))
        if index >= len(tokens):
            return match.group(0)
        seen.add(index)
        return tokens[index]

    restored = TOKEN_RE.sub(replace, text)
    if len(seen) != len(tokens):
        missing = sorted(set(range(len(tokens))) - seen)
        raise ValueError(f"translator dropped protected token(s): {missing}")
    return restored


class BingTranslator:
    def __init__(self) -> None:
        self._opener: urllib.request.OpenerDirector | None = None
        self._ig = ""
        self._iid = "translator.5028.1"
        self._key = ""
        self._token = ""
        self.refresh()

    def refresh(self) -> None:
        jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        request = urllib.request.Request(
            "https://www.bing.com/translator",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0.0.0 Safari/537.36"
                ),
            },
        )
        with self._opener.open(request, timeout=30) as response:
            page = response.read().decode("utf-8", errors="replace")
        ig_match = re.search(r'IG:"([^"]+)"', page)
        token_match = re.search(
            r'params_AbusePreventionHelper\s*=\s*\[(\d+),"([^"]+)",', page
        )
        if not ig_match or not token_match:
            raise RuntimeError("could not initialise Bing Translator session")
        self._ig = ig_match.group(1)
        self._key = token_match.group(1)
        self._token = token_match.group(2)

    @staticmethod
    def _split_text(text: str, limit: int = 700) -> list[str]:
        if len(text) <= limit:
            return [text]
        chunks: list[str] = []
        remaining = text
        while len(remaining) > limit:
            window = remaining[:limit]
            candidates = [
                window.rfind(mark)
                for mark in ("\\n", "。", "！", "？", "；", ";", ". ", "! ", "? ")
            ]
            split_at = max(candidates)
            if split_at < limit // 3:
                split_at = limit
            elif window[split_at : split_at + 2] == "\\n":
                split_at += 2
            else:
                split_at += 1
            chunks.append(remaining[:split_at])
            remaining = remaining[split_at:]
        if remaining:
            chunks.append(remaining)
        return chunks

    def _translate_piece(self, text: str, target: str, source_language: str) -> str:
        quote_open = True

        def normalise_quote(_match: re.Match[str]) -> str:
            nonlocal quote_open
            result = "“" if quote_open else "”"
            quote_open = not quote_open
            return result

        text = re.sub(r'\\"', normalise_quote, text)
        styles: list[tuple[str, str]] = []
        html_tags = ("b", "i", "strong", "em", "u")

        def style_replace(match: re.Match[str]) -> str:
            index = len(styles)
            tag = html_tags[index] if index < len(html_tags) else "span"
            styles.append((match.group(1), tag))
            return f"<{tag}>{match.group(2)}</{tag}>"

        styled = re.sub(r'§([A-Za-z0-9])(.+?)§!', style_replace, text)
        protected, tokens = protect_hoi4_tokens(styled)
        target_code = {"english": "en", "russian": "ru"}[target]
        form = urllib.parse.urlencode(
            {
                "fromLang": source_language,
                "text": protected,
                "to": target_code,
                "token": self._token,
                "key": self._key,
                "tryFetchingGenderDebiasedTranslations": "true",
            }
        ).encode("utf-8")
        url = (
            "https://www.bing.com/ttranslatev3?isVertical=1"
            f"&IG={self._ig}&IID={self._iid}"
        )
        assert self._opener is not None
        request = urllib.request.Request(
            url,
            data=form,
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.bing.com",
                "Referer": "https://www.bing.com/translator",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0.0.0 Safari/537.36"
                ),
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        with self._opener.open(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list) or not payload:
            raise RuntimeError(f"unexpected translator response: {payload!r}")
        translated = payload[0]["translations"][0]["text"]
        translated = translated.replace('"', '\\"')
        translated = restore_hoi4_tokens(translated, tokens)
        for index, (style, tag) in enumerate(styles):
            opening = f"<{tag}>"
            closing = f"</{tag}>"
            if translated.count(opening) != 1 or translated.count(closing) != 1:
                raise ValueError(f"translator dropped style tag {index}")
            translated = translated.replace(opening, f"§{style}")
            translated = translated.replace(closing, "§!")
        return translated

    def translate(self, text: str, target: str, source_language: str = "zh-Hans") -> str:
        def translate_segment(content: str, style: str | None = None) -> str:
            paragraphs = content.split("\\n")
            translated_paragraphs: list[str] = []
            for paragraph in paragraphs:
                pieces = self._split_text(paragraph)
                translated_paragraphs.append(
                    "".join(
                        self._translate_piece(
                            f"§{style}{piece}§!" if style is not None else piece,
                            target,
                            source_language,
                        )
                        for piece in pieces
                        if piece
                    )
                )
            return "\\n".join(translated_paragraphs)

        translated_segments: list[str] = []
        cursor = 0
        for match in re.finditer(r'§([A-Za-z0-9])(.*?)§!', text, flags=re.DOTALL):
            translated_segments.append(translate_segment(text[cursor : match.start()]))
            translated_segments.append(translate_segment(match.group(2), match.group(1)))
            cursor = match.end()
        translated_segments.append(translate_segment(text[cursor:]))
        return "".join(translated_segments)


def load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_localisation(path: Path, language: str, rows: list[tuple[str, str]]) -> None:
    lines = [f"l_{language}:"]
    for key, value in rows:
        value = MANUAL_TRANSLATIONS.get(language, {}).get(key, value)
        for old, new in KEYED_REPLACEMENTS.get(language, {}).get(key, []):
            value = value.replace(old, new)
        value = re.sub(r'§!([A-Za-zА-Яа-яЁё])', r'§! \1', value)
        value = re.sub(r'([A-Za-zА-Яа-яЁё])§([A-Za-z0-9])', r'\1 §\2', value)
        lines.append(f' {key}:0 "{value}"')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mod-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--vanilla-root", type=Path, required=True)
    parser.add_argument("--dependency", type=Path, action="append", default=[])
    parser.add_argument("--translate", action="store_true")
    parser.add_argument("--delay", type=float, default=0.12)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    mod_root = args.mod_root.resolve()
    providers = [mod_root, *[p.resolve() for p in args.dependency], args.vanilla_root.resolve()]
    chinese = read_language(mod_root, "simp_chinese")
    cache_path = mod_root / "tmp" / "localisation_translation_cache.json"
    cache = load_cache(cache_path)

    thread_state = threading.local()

    def translate_with_retry(source: str, language: str, source_language: str) -> str:
        visible = PROTECTED_RE.sub("", source)
        if source_language == "en" and not re.search(r"[A-Za-z]{2,}", visible):
            return source
        if source_language == "zh-Hans" and not re.search(r"[\u3400-\u9fff]", visible):
            return source
        translator = getattr(thread_state, "translator", None)
        if translator is None:
            translator = BingTranslator()
            thread_state.translator = translator
        for attempt in range(6):
            try:
                result = translator.translate(source, language, source_language)
                time.sleep(args.delay)
                return result
            except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, KeyError, IndexError):
                if attempt == 5:
                    raise
                time.sleep(1.5 * (attempt + 1))
                translator.refresh()
        raise AssertionError("unreachable")

    provider_english: OrderedDict[str, tuple[str, Path]] = OrderedDict()
    for provider in providers:
        provider_english.update(read_language(provider, "english"))
    generated_english: dict[str, str] = {}

    for language in ("english", "russian"):
        available: set[str] = set()
        for provider in providers:
            available.update(read_language(provider, language))
        if not args.translate:
            generated_path = (
                mod_root / "localisation" / language / f"RUS_test_missing_l_{language}.yml"
            )
            available.update(read_localisation_file(generated_path, language))
        missing_chinese = [(key, value_path[0]) for key, value_path in chinese.items() if key not in available]
        if language == "english":
            source_language = "zh-Hans"
            missing = [(key, prepare_english_source(source)) for key, source in missing_chinese]
        elif not args.translate:
            source_language = "zh-Hans"
            missing = missing_chinese
        else:
            source_language = "en"
            missing = []
            for key, _source in missing_chinese:
                english_source = generated_english.get(key)
                if english_source is None and key in provider_english:
                    english_source = provider_english[key][0]
                if english_source is None:
                    raise RuntimeError(f"no English bridge text found for Russian key {key}")
                missing.append((key, english_source))
        print(f"{language}: {len(missing)} genuinely missing key(s)")
        if not args.translate:
            continue
        pending: dict[str, str] = {}
        for _key, source in missing:
            cache_key = json.dumps(["v2", source_language, language, source], ensure_ascii=False)
            if cache_key not in cache:
                pending[cache_key] = source

        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = {
                executor.submit(translate_with_retry, source, language, source_language): cache_key
                for cache_key, source in pending.items()
            }
            for future in concurrent.futures.as_completed(futures):
                cache_key = futures[future]
                try:
                    cache[cache_key] = future.result()
                except Exception as exc:
                    save_cache(cache_path, cache)
                    raise RuntimeError(f"failed translating {cache_key}: {exc}") from exc
                completed += 1
                if completed % 20 == 0:
                    save_cache(cache_path, cache)
                if completed % 25 == 0 or completed == len(pending):
                    print(f"  translated {completed}/{len(pending)}", flush=True)

        rows: list[tuple[str, str]] = []
        for key, source in missing:
            cache_key = json.dumps(["v2", source_language, language, source], ensure_ascii=False)
            rows.append((key, cache[cache_key]))

        output = mod_root / "localisation" / language / f"RUS_test_missing_l_{language}.yml"
        write_localisation(output, language, rows)
        if language == "english":
            generated_english = dict(rows)
        save_cache(cache_path, cache)
        print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
