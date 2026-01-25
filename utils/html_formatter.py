"""
Простая утилита для безопасного форматирования HTML в Telegram боте
"""


def safe_html(text: str) -> str:
    """
    Безопасное экранирование HTML символов

    Args:
        text: Любой текст, который может содержать HTML символы

    Returns:
        Безопасный текст с экранированными символами

    Пример:
        >>> safe_html('Текст с <тегами> & символами')
        'Текст с &lt;тегами&gt; &amp; символами'
    """
    if not text:
        return ""

    # Важно: заменяем & первым!
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def bold(text: str) -> str:
    """Жирный текст: <b>текст</b>"""
    return f"<b>{safe_html(text)}</b>"


def italic(text: str) -> str:
    """Курсив: <i>текст</i>"""
    return f"<i>{safe_html(text)}</i>"


def code(text: str) -> str:
    """Моноширинный текст: <code>текст</code>"""
    return f"<code>{safe_html(text)}</code>"


def pre(text: str) -> str:
    """Блок кода: <pre>текст</pre>"""
    return f"<pre>{safe_html(text)}</pre>"


def link(text: str, url: str) -> str:
    """Ссылка: <a href="url">текст</a>"""
    return f'<a href="{url}">{safe_html(text)}</a>'


def underline(text: str) -> str:
    """Подчеркнутый текст: <u>текст</u>"""
    return f"<u>{safe_html(text)}</u>"


def strikethrough(text: str) -> str:
    """Зачеркнутый текст: <s>текст</s>"""
    return f"<s>{safe_html(text)}</s>"

