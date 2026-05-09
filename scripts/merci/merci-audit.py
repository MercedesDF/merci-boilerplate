#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-audit.py — Auditoría local del proyecto merci-boilerplate.es (Fase 1).

¿Qué problema resuelve?
    Evitar que secretos o errores básicos lleguen al repositorio, y adelantar
    reglas de SEO técnico en HTML antes del despliegue (shift-left).

¿Cómo está organizado el programa (orden mental para leerlo)?
    1) Descubrimos QUÉ archivos revisar (todo el repo o solo lo staged en Git).
    2) Para cada archivo de texto, leemos su contenido de forma segura.
    3) Aplicamos comprobaciones independientes (secretos, Python, JSON, JS, HTML).
    4) Imprimimos un informe y devolvemos un código de salida (0 = bien, 1 = errores).

Dependencias:
    Solo biblioteca estándar de Python 3.10+, para que funcione sin ``pip install``.

Códigos de salida:
    0 — No hay errores bloqueantes (puede haber advertencias).
    1 — Hay al menos un error (p. ej. posible secreto o HTML incompleto).
    2 — Fallo del propio script (ruta inválida, Git roto, etc.).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Iterator, Optional

try:
    import litellm
    from litellm import completion
    litellm.telemetry = False  # Desactivar telemetría por privacidad (Zero Trust)
    # QUÉ HACE: Desactiva los mensajes de soporte y depuración internos de la librería.
    # POR QUÉ: Preserva la limpieza de la terminal (DX) al realizar la degradación elegante.
    litellm.suppress_debug_info = True
except ImportError:
    litellm = None

# ---------------------------------------------------------------------------
# Rutas y exclusiones
# ---------------------------------------------------------------------------
# ``__file__`` es la ruta de este .py; subimos dos carpetas para llegar a la
# raíz del repositorio (scripts/merci → scripts → raíz).
REPO_ROOT = Path(__file__).resolve().parents[2]

# Carpetas que no debemos recorrer: binarios, cachés, dependencias externas
# o material bruto pesado (.assets-raw) que no aporta a la auditoría de texto.
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
        ".assets-raw",
        "evidencias",
    }
)

# Extensiones que tratamos como texto. Fuera de esta lista ignoramos el
# archivo en el barrido completo (salvo .env, que a veces no tiene sufijo).
TEXT_SUFFIXES = frozenset(
    {
        ".html",
        ".htm",
        ".css",
        ".js",
        ".mjs",
        ".cjs",
        ".json",
        ".md",
        ".txt",
        ".xml",
        ".svg",
        ".scss",
        ".sass",
        ".ts",
        ".tsx",
        ".jsx",
        ".yml",
        ".yaml",
        ".toml",
        ".py",
        ".ini",
        ".env",
        ".sh",
        ".zsh",
    }
)

# Límite de tamaño por archivo: evita cargar vídeos o dumps gigantes en RAM.
MAX_FILE_BYTES = 2 * 1024 * 1024

# ---------------------------------------------------------------------------
# Patrones de secretos (expresiones regulares)
# ---------------------------------------------------------------------------
# Cada entrada es (descripción humana, patrón compilado). Son heurísticas:
# pueden dar falsos positivos en documentación; por eso existe la marca
# ``merci-audit:silence-secret`` en la misma línea para silenciar un caso conocido.
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Posible clave privada PEM", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Posible credencial AWS (prefijo tipo AKIA/ASIA…)", re.compile(r"\b(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b")),
    ("Posible PAT GitHub (ghp_)", re.compile(r"\bghp_[0-9a-zA-Z]{36,}\b")),
    ("Posible PAT GitHub fine-grained (github_pat_)", re.compile(r"\bgithub_pat_[0-9a-zA-Z_]{20,}\b")),
    ("Posible token Slack (xox…)", re.compile(r"\bxox[baprs]-[0-9a-zA-Z-]{10,}\b")),
    ("Posible clave Stripe en vivo (sk_live_)", re.compile(r"\bsk_live_[0-9a-zA-Z]{24,}\b")),
    ("Posible clave API de Google (AIza…)", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("Posible API key SendGrid (SG.)", re.compile(r"\bSG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}\b")),
]


@dataclass
class Finding:
    """Un hallazgo concreto: dónde, qué tan grave, y mensaje para humanos."""

    path: Path
    line: int
    level: str  # "error" bloquea el commit; "warn" solo informa.
    code: str  # Código corto estable (SECRET, SEO_LANG, …) para filtrar en CI.
    message: str


@dataclass
class AuditState:
    """Acumula hallazgos separando errores de advertencias."""

    errors: list[Finding] = field(default_factory=list)
    warns: list[Finding] = field(default_factory=list)

    def add(self, item: Finding) -> None:
        if item.level == "error":
            self.errors.append(item)
        else:
            self.warns.append(item)


def iter_repo_files(root: Path) -> Iterator[Path]:
    """
    Recorre ``root`` en profundidad y entrega rutas de archivos auditables.

    Por qué ``rglob``: es simple y suficiente para un repo pequeño/mediano.
    Si en el futuro el repo creciera mucho, podríamos sustituir esto por
    ``git ls-files`` también en modo no-staged.
    """
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            # ``path`` no cuelga de ``root`` (caso raro con enlaces); lo saltamos.
            continue
        if any(part in SKIP_DIR_NAMES for part in relative.parts):
            continue
        suffix_ok = path.suffix.lower() in TEXT_SUFFIXES
        dotenv_ok = path.name in {".env", ".env.local"}
        if not suffix_ok and not dotenv_ok:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            # Permisos o carrera con borrado; no tumbar todo el audit.
            continue
        if size > MAX_FILE_BYTES:
            continue
        yield path


def git_staged_paths(root: Path) -> list[Path]:
    """
    Lista archivos en el índice de Git (staged) listos para el próximo commit.

    ``--diff-filter=ACM`` limita a añadidos, copiados y modificados (no borrados),
    que son los que normalmente queremos validar antes de ``git commit``.
    """
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("No se encontró el ejecutable ``git`` en el PATH.") from exc
    except subprocess.CalledProcessError as exc:
        # ``stderr`` suele explicar si no estamos en un repo Git.
        detail = (exc.stderr or "").strip()
        raise SystemExit(f"Git devolvió error al listar staged.{(' ' + detail) if detail else ''}") from exc

    result: list[Path] = []
    for line in completed.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        path = (root / line).resolve()
        if not path.is_file():
            continue
            
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIR_NAMES for part in relative.parts):
            continue
            
        suffix_ok = path.suffix.lower() in TEXT_SUFFIXES
        dotenv_ok = path.name in {".env", ".env.local"}
        if not suffix_ok and not dotenv_ok:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        result.append(path)
    return result


def read_text(path: Path) -> Optional[str]:
    """
    Lee texto UTF-8. ``errors='replace'`` evita que un byte inválido tumbe el audit:
    sustituye caracteres ilegibles en lugar de lanzar UnicodeDecodeError.
    """
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"[merci-audit] No se pudo leer {path}: {exc}", file=sys.stderr)
        return None


def scan_secrets(state: AuditState, path: Path, text: str) -> None:
    """Busca patrones típicos de secretos línea a línea (rápido y fácil de entender)."""
    lines = text.splitlines()
    for line_number, line in enumerate(lines, start=1):
        if "merci-audit:silence-secret" in line:
            continue
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                state.add(
                    Finding(
                        path,
                        line_number,
                        "error",
                        "SECRET",
                        f"{label} — mover a variable de entorno o gestor de secretos.",
                    )
                )


def audit_python_syntax(state: AuditState, path: Path, text: str) -> None:
    """
    Comprueba que el .py sea sintácticamente válido sin ejecutarlo.

    ``ast.parse`` construye el árbol sintáctico; si falla, el archivo no puede
    importarse ni interpretarse correctamente.
    """
    if path.suffix.lower() != ".py":
        return
    try:
        ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        lineno = exc.lineno or 1
        state.add(
            Finding(
                path,
                lineno,
                "error",
                "PY_SYNTAX",
                f"Sintaxis Python inválida: {exc.msg}",
            )
        )

GLOBAL_ACRONYM_COUNTS: dict[str, int] = {}

def get_global_acronym_count(acronym: str) -> int:
    """Cuenta las apariciones de un acrónimo en todos los archivos .md del repositorio."""
    if acronym in GLOBAL_ACRONYM_COUNTS:
        return GLOBAL_ACRONYM_COUNTS[acronym]
        
    count = 0
    pattern = re.compile(rf"\b{re.escape(acronym)}\b")
    for path in REPO_ROOT.rglob("*.md"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            count += len(pattern.findall(content))
        except Exception:
            continue
            
    GLOBAL_ACRONYM_COUNTS[acronym] = count
    return count

def audit_js_smells(state: AuditState, path: Path, text: str) -> None:
    """
    Reglas suaves para JavaScript: ``eval`` y ``new Function`` suelen ser
    vectores de inyección o dificultan el análisis estático. Aquí solo avisamos.
    """
    if path.suffix.lower() not in {".js", ".mjs", ".cjs", ".jsx"}:
        return
    lines = text.splitlines()
    for line_number, line in enumerate(lines, start=1):
        if "merci-audit:silence-js" in line:
            continue
        if re.search(r"\beval\s*\(", line):
            state.add(
                Finding(
                    path,
                    line_number,
                    "warn",
                    "JS_EVAL",
                    "Uso de eval(); revisar riesgo de inyección y política del proyecto.",
                )
            )
        if re.search(r"\bnew\s+Function\s*\(", line):
            state.add(
                Finding(
                    path,
                    line_number,
                    "warn",
                    "JS_NEW_FUNCTION",
                    "new Function(); perfil de riesgo parecido a eval en muchos casos.",
                )
            )

def audit_md_acronyms(state: AuditState, path: Path, text: str) -> None:
    """
    Vigila que los acrónimos clave del proyecto incluyan su expansión explicativa.
    Lanza advertencia (warn) para no bloquear el commit por falsos positivos.
    """
    if path.suffix.lower() != ".md":
        return
        
    # Lista de vigilancia de acrónimos críticos (Watchlist)
    watchlist = ["AJAX", "PHP", "CPU", "TTFB", "INP", "JSON-LD", "SEO", "DOM", "BEM", "CMS"]
    
    for acronym in watchlist:
        # Si el acrónimo existe en el texto como palabra exacta...
        if re.search(rf"\b{re.escape(acronym)}\b", text):
            # ...buscamos si está expandido en formato: ACRONIMO (Explicación)
            expansion_pattern = rf"\b{re.escape(acronym)}\s*\([^)]+\)"
            if re.search(expansion_pattern, text):
                continue
                
            # Si no está expandido, verificamos si es un término consolidado (> 3 apariciones globales)
            if get_global_acronym_count(acronym) > 3:
                continue
                
            # Localizamos la primera línea donde aparece para lanzar la advertencia
            for i, line in enumerate(text.splitlines(), start=1):
                if re.search(rf"\b{re.escape(acronym)}\b", line):
                    state.add(
                        Finding(
                            path, i, "warn", "MD_ACRONYM",
                            f"El acrónimo '{acronym}' no está expandido y no está consolidado (aparece 3 veces o menos). Regla: {acronym} (Inglés - Español)."
                        )
                    )
                    break


def audit_php_smells(state: AuditState, path: Path, text: str) -> None:
    """
    Busca funciones PHP peligrosas que son vectores comunes de RCE.
    Lanza una advertencia para que se revise manualmente el contexto.
    """
    if path.suffix.lower() != ".php":
        return

    dangerous_functions = [
        "eval", "exec", "shell_exec", "system", "passthru", "popen", "proc_open"
    ]
    pattern = re.compile(rf"\b({'|'.join(dangerous_functions)})\s*\(")

    lines = text.splitlines()
    for line_number, line in enumerate(lines, start=1):
        if "merci-audit:silence-php" in line:
            continue
        match = pattern.search(line)
        if match:
            state.add(
                Finding(
                    path, line_number, "warn", "PHP_DANGEROUS_FUNC",
                    f"Uso de función peligrosa '{match.group(1)}()'. Revisar para posible RCE."
                )
            )

def audit_inline_styles(state: AuditState, path: Path, text: str) -> None:
    """
    Detecta atributos style="..." en el código, los cuales vulneran # merci-audit:silence-style
    la arquitectura SASS 7-1 y la metodología BEM.
    """
    if path.suffix.lower() not in {".html", ".htm", ".php", ".py", ".js"}:
        return
        
    pattern = re.compile(r'\bstyle\s*=\s*(["\'])(.*?)\1', re.IGNORECASE)  # merci-audit:silence-style
    lines = text.splitlines()
    
    for line_number, line in enumerate(lines, start=1):
        if "merci-audit:silence-style" in line:
            continue
        
        for match in pattern.finditer(line):
            style_content = match.group(2).strip()
            # Excepciones arquitectónicas justificadas (como el ancla WAI-ARIA invisible o los estilos del PDF)
            if "position: absolute; top: 0; left: 0;" in style_content or "text-align: left; padding-bottom: 6rem;" in style_content:
                continue
                
            state.add(
                Finding(
                    path,
                    line_number,
                    "warn",
                    "UI_INLINE_STYLE",
                    f"Estilo en línea detectado (style='{style_content[:25]}...'). Extraer a componente SASS (BEM).",  # merci-audit:silence-style
                )
            )

class SeoHTMLParser(HTMLParser):
    """
    Acumula datos mientras el analizador HTML de la librería estándar recorre el documento.

    No intenta ser un navegador completo: solo extrae señales SEO que comprobamos después.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_chunks: list[str] = []
        self.in_title = False
        self.html_lang: Optional[str] = None
        self.charset: Optional[str] = None
        self.has_viewport = False
        self.description: Optional[str] = None
        self.canonical: Optional[str] = None
        self.json_ld_scripts = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        # Normalizamos nombres de atributos a minúsculas para comparar sin sorpresas.
        attributes = {name.lower(): (value or "") for name, value in attrs}
        tag_lower = tag.lower()

        if tag_lower == "title":
            self.in_title = True

        if tag_lower == "html" and "lang" in attributes:
            self.html_lang = attributes["lang"].strip()

        if tag_lower == "meta":
            name = attributes.get("name", "").lower()
            http_equiv = attributes.get("http-equiv", "").lower()
            content = attributes.get("content", "").strip()

            if name == "description" and content:
                self.description = content
            if name == "viewport":
                self.has_viewport = True

            if http_equiv == "content-type" and "charset=" in content.lower():
                tail = content.lower().split("charset=", 1)[-1]
                self.charset = tail.split(";")[0].strip()

            if "charset" in attributes:
                self.charset = (attributes.get("charset") or "").strip()

        if tag_lower == "link" and attributes.get("rel", "").lower() == "canonical":
            href = attributes.get("href", "").strip()
            if href:
                self.canonical = href

        if tag_lower == "script":
            script_type = (attributes.get("type") or "").lower()
            if script_type == "application/ld+json":
                self.json_ld_scripts += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        # Etiquetas vacías en XML/HTML (<meta … />) pasan por aquí en lugar de start+end.
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False


def audit_html_seo(state: AuditState, path: Path, text: str, strict_json_ld: bool) -> None:
    """
    SEO técnico mínimo alineado con la Fase 2 del roadmap, pero ya activo en HTML.

    Separación error vs advertencia:
        - Errores: lo que consideramos imprescindible (idioma, título, descripción).
        - Advertencias: mejores prácticas (viewport, canonical, JSON-LD si no es estricto).
    """
    if path.suffix.lower() not in {".html", ".htm"}:
        return

    parser = SeoHTMLParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:
        # HTMLParser raramente falla; si ocurre, preferimos un informe claro a un traceback crudo.
        state.add(
            Finding(
                path,
                1,
                "error",
                "HTML_PARSE",
                f"No se pudo analizar HTML ({type(exc).__name__}): {exc}",
            )
        )
        return

    title_text = "".join(parser.title_chunks).strip()

    if not parser.html_lang:
        state.add(Finding(path, 1, "error", "SEO_LANG", 'Falta atributo lang en <html lang="...">.'))
    if not title_text:
        state.add(Finding(path, 1, "error", "SEO_TITLE", "Falta <title> no vacío."))
    if not parser.description:
        state.add(Finding(path, 1, "error", "SEO_DESC", 'Falta <meta name="description" content="...">.'))

    if not parser.charset:
        state.add(
            Finding(
                path,
                1,
                "warn",
                "SEO_CHARSET",
                "No se detectó charset UTF-8 explícito (<meta charset> o equivalente).",
            )
        )
    elif "utf-8" not in parser.charset.lower():
        state.add(
            Finding(
                path,
                1,
                "warn",
                "SEO_CHARSET",
                f'Charset declarado "{parser.charset}"; se recomienda utf-8.',
            )
        )

    if not parser.has_viewport:
        state.add(
            Finding(
                path,
                1,
                "warn",
                "SEO_VIEWPORT",
                "Falta meta viewport (mobile-first / Core Web Vitals).",
            )
        )

    if not parser.canonical:
        state.add(
            Finding(
                path,
                1,
                "warn",
                "SEO_CANONICAL",
                'Falta <link rel="canonical" href="...">.',
            )
        )

    if strict_json_ld and parser.json_ld_scripts < 1:
        state.add(
            Finding(
                path,
                1,
                "error",
                "SEO_JSONLD",
                'Falta <script type="application/ld+json"> (JSON-LD).',
            )
        )
    elif not strict_json_ld and parser.json_ld_scripts < 1:
        state.add(
            Finding(
                path,
                1,
                "warn",
                "SEO_JSONLD",
                'Sin JSON-LD; en Fase 2 será obligatorio (usar --strict-json-ld en CI).',
            )
        )


def audit_json(state: AuditState, path: Path, text: str) -> None:
    """Validación superficial: si el JSON no parsea, el archivo rompería consumidores."""
    if path.suffix.lower() != ".json":
        return
    if path.name == "package-lock.json" or "lock" in path.name.lower():
        return
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        line = getattr(exc, "lineno", 1) or 1
        state.add(
            Finding(
                path,
                line,
                "error",
                "JSON_SYNTAX",
                f"JSON inválido: {exc.msg}",
            )
        )


def run_on_files(paths: Iterable[Path], strict_json_ld: bool) -> AuditState:
    """Orquesta todas las comprobaciones, archivo por archivo."""
    state = AuditState()
    for path in sorted(set(paths)):
        text = read_text(path)
        if text is None:
            continue
        scan_secrets(state, path, text)
        audit_python_syntax(state, path, text)
        audit_js_smells(state, path, text)
        audit_json(state, path, text)
        audit_html_seo(state, path, text, strict_json_ld)
        audit_md_acronyms(state, path, text)
        audit_php_smells(state, path, text)
        audit_inline_styles(state, path, text)
    return state


def audit_banned_tracked_files(root: Path, state: AuditState, staged_only: bool) -> None:
    """Verifica que no haya material pesado rastreado por Git (o en stage)."""
    cmd = ["git", "-C", str(root), "diff", "--cached", "--name-only", "--diff-filter=ACM"] if staged_only else ["git", "-C", str(root), "ls-files"]
    try:
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
        for line in completed.stdout.splitlines():
            line = line.strip()
            # Ignorar líneas vacías y marcadores de estructura permitidos
            if not line or line.endswith(".gitkeep"): continue
            
            if line.startswith("laboratorio/evidencias/") or line.startswith(".assets-raw/") or line == ".linkedin_token.json":
                path = root / line
                state.add(Finding(
                    path, 1, "error", "BANNED_TRACKED_FILE",
                    f"Archivo en directorio restringido ({line}). Retíralo con 'git rm --cached'."
                ))
    except Exception:
        pass

def get_system_prompt() -> str:
    """Lee el prompt rector del sistema para inyectarlo en la IA."""
    # QUÉ HACE: Lee físicamente el documento de directrices base del ecosistema.
    # POR QUÉ: Mantiene las reglas de la IA desacopladas del código Python, facilitando su evolución.
    prompt_path = REPO_ROOT / "laboratorio" / "prompts" / "prompt-sistema-base.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8", errors="replace")
    return "Eres un asistente DevSecOps. Sugiere una reparación breve para el siguiente error."

def get_ai_suggestion(finding: Finding) -> str:
    """Genera una sugerencia de código usando el modelo local (Ollama + qwen2.5-coder)."""
    # QUÉ HACE: Extrae contexto del archivo roto y pide al modelo local una corrección específica.
    # POR QUÉ: Reduce la fricción operativa al proporcionar la solución directamente en consola.
    if not litellm:
        return ""
        
    try:
        content = finding.path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        # Extraer hasta 5 líneas de contexto antes y después del error
        start = max(0, finding.line - 6)
        end = min(len(lines), finding.line + 5)
        context_snippet = "\n".join(lines[start:end])
    except Exception:
        context_snippet = "No se pudo leer el contexto del archivo."

    prompt = (
        f"Archivo: {finding.path.name}\n"
        f"Línea: {finding.line}\n"
        f"Error detectado: [{finding.code}] {finding.message}\n"
        f"Contexto del código:\n```\n{context_snippet}\n```\n"
        f"Proporciona la maniobra de corrección directa."
    )

    mensajes = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": prompt}
    ]

    try:
        # Delegamos a qwen2.5-coder local por el puerto 11434
        respuesta = completion(
            model="ollama/qwen2.5-coder",
            messages=mensajes,
            api_base="http://localhost:11434",
            max_tokens=250
        )
        return respuesta.choices[0].message.content.strip()
    except Exception:
        return ""  # Degradación elegante silenciosa en caso de fallo de Ollama

def print_report(state: AuditState) -> None:
    """Imprime hallazgos en stdout, una línea por hallazgo (fácil de grep en CI)."""
    for item in state.errors + state.warns:
        try:
            display = item.path.resolve().relative_to(REPO_ROOT.resolve())
        except ValueError:
            display = item.path
        prefix = "ERROR" if item.level == "error" else "WARN"
        print(f"{prefix} {item.code} {display}:{item.line}: {item.message}")
        
        # --- INYECCIÓN DE IA (El Agente Auditor) ---
        # Solo solicitamos sugerencias para errores críticos para no saturar el pre-commit.
        if item.level == "error" and litellm:
            print(f"  🤖 [Merci Brain] Analizando contexto de {item.code}...")
            suggestion = get_ai_suggestion(item)
            if suggestion:
                # Indentamos la respuesta para separarla visualmente del log estándar
                formatted_suggestion = "\n".join(f"     {line}" for line in suggestion.splitlines())
                print(f"  💡 Sugerencia de reparación:\n{formatted_suggestion}\n")


def main(argv: Optional[list[str]] = None) -> int:
    """
    Punto de entrada: parsea argumentos, elige lista de archivos y ejecuta el audit.

    Devuelve un entero porque ``raise SystemExit(main())`` espera código de proceso.
    """
    parser = argparse.ArgumentParser(
        description="Merci Audit: secretos, sintaxis básica, higiene JS y SEO mínimo en HTML.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Raíz del repositorio (por defecto: raíz del proyecto).",
    )
    parser.add_argument(
        "--git-staged",
        action="store_true",
        help="Solo archivos añadidos al índice (staged); pensado para pre-commit.",
    )
    parser.add_argument(
        "--strict-json-ld",
        action="store_true",
        help="Exige al menos un bloque JSON-LD en cada HTML.",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse ya imprimió ayuda o mensaje; respetamos su código si existe.
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 2

    root = args.root.resolve()
    if not root.is_dir():
        print(f"Raíz inválida (no es carpeta): {root}", file=sys.stderr)
        return 2

    try:
        if args.git_staged:
            files = git_staged_paths(root)
        else:
            files = list(iter_repo_files(root))
        state = run_on_files(files, args.strict_json_ld)
        audit_banned_tracked_files(root, state, args.git_staged)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[merci-audit] Error inesperado durante el audit: {exc}", file=sys.stderr)
        return 2

    print_report(state)

    if state.warns:
        print(
            f"\nResumen: {len(state.errors)} error(es), {len(state.warns)} advertencia(s).",
            file=sys.stderr,
        )
    elif state.errors:
        print(f"\nResumen: {len(state.errors)} error(es).", file=sys.stderr)
    else:
        print("✅ Merci Audit: sin hallazgos bloqueantes.", file=sys.stderr)

    return 1 if state.errors else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[merci-audit] Interrumpido por el usuario.", file=sys.stderr)
        raise SystemExit(130) from None
