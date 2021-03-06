import datetime
import dateutil.parser
import dateutil.tz
import markdown as Markdown
import os
import re

from flask import Blueprint
from jinja2 import Markup, evalcontextfilter, contextfunction, Template
from time import time

NAME = "Basic Bootstrap 3 template"

blueprint = Blueprint('base', __name__)

@contextfunction
def read_file(context, path, absolute=False):
    """
    Read the file at `path`, rendering the file contents as a template 
    with the caller's context. If `absolute` is True, use absolute path,
    otherwise path is assumed to be relative to Tarbell template root dir.
    """

    if not absolute:
        path = os.path.join(os.path.dirname(__file__), '..', path)
    try:
        return open(path, 'r').read().encode('utf-8')
    except IOError:
        return None

@contextfunction
def render_file(context, path, absolute=False):
    file_contents = read_file(context, path, absolute)
    template = Template(file_contents)
    return template.render(**context)


@blueprint.app_context_processor
def context_processor():
    """
    Add helper functions to context for all projects.
    """
    return {
        'read_file': read_file,
        'render_file' :render_file
    }


@blueprint.app_template_filter()
def process_text(text, scrub=True):
    try:
        return Markup(text)
    except TypeError:
        return ""


@blueprint.app_template_filter()
def drop_cap(text):
    """
    Add drop-cap class to beginning of content.
    """
    if type(text).__name__ == 'Markup':
        return text
    if text:
        content = '<span class="drop-cap">%s</span>%s' % (text[:1], text[1:])
    else:
        content = ''
    return Markup(content)


@blueprint.app_template_filter()
def format_date(value, format='%b. %d, %Y', convert_tz=None):
    """
    Format a date.
    """
    if isinstance(value, float) or isinstance(value, int):
        seconds = (value - 25569) * 86400.0
        parsed = datetime.datetime.utcfromtimestamp(seconds)
    else:
        parsed = dateutil.parser.parse(value)
    if convert_tz:
        local_zone = dateutil.tz.gettz(convert_tz)
        parsed = parsed.astimezone(tz=local_zone)

    return parsed.strftime(format)

@blueprint.app_template_filter()
def strong_to_b(value):
    """
    Replaces enclosing <strong> and </strong>s with <p><b>s
    """
    value = re.sub(r'^<p><strong>(.+?)</strong></p>$', u'<p><b>\\1</b></p>', value)
    return value


@blueprint.app_template_filter()
def strip_p(value):
    """
    Removes enclosing <p> and </p> tags from value.
    """
    value = re.sub(r'^<p>(.+?)</p>$', u'\\1', value)
    return value


@blueprint.app_template_filter()
def wrap_p(value):
    """
    Adds enclosing <p> and </p> tags to value.
    """
    return '<p>%s</p>' % value


@blueprint.app_template_filter()
def replace_windows_linebreaks(value):
    """
    Replace all \r (the Windows/MS-style linebreak character) with
    better-tasting, lower-fat unix-style \ns. Takes a string, returns
    a string.
    """
    return re.sub(r'\r', '\n', value)


@blueprint.app_template_filter('paragraphs')
def get_paragraphs(value):
    """
    Take a block of text and return an array of paragraphs. Only works if
    paragraphs are denoted by <p> tags and not double <br>.
    Use `br_to_p` to convert text with double <br>s to <p> wrapped paragraphs.
    """
    value = re.sub(r'</p>\w*<p>', u'</p>\n\n<p>', value)
    paras = re.split('\n{2,}', value)
    return paras


@blueprint.app_template_filter()
def br_to_p(value):
    """
    Converts text where paragraphs are separated by two <br> tags to text
    where the paragraphs are wrapped by <p> tags.
    """
    value = re.sub(r'<br\s*/*>\s*<br\s*/*>', u'\n\n', value)
    paras = re.split('\n{2,}', value)
    paras = [u'<p>%s</p>' % p.strip() for p in paras if p]
    paras = u'\n\n'.join(paras)
    return paras


@blueprint.app_template_filter()
def section_heads(value):
    """
    Search through a block of text and replace <p><b>text</b></p>
    with <h4 class="section-head">text</h4
    """
    value = re.sub(r'<p>\w*<b>(.+?)</b>\w*</p>', u'<h4 class="section-head">\\1</h4>', value)
    return value


@blueprint.app_template_filter()
@evalcontextfilter
def linebreaks(eval_ctx, value):
    """Converts newlines into <p> and <br />s."""
    value = re.sub(r'\r\n|\r|\n', '\n', value)  # normalize newlines
    paras = re.split('\n{2,}', value)
    paras = [u'<p>%s</p>' % p.replace('\n', '<br />') for p in paras]
    paras = u'\n\n'.join(paras)
    return Markup(paras)


@blueprint.app_template_filter()
@evalcontextfilter
def linebreaksbr(eval_ctx, value):
    """Converts newlines into <p> and <br />s."""
    value = re.sub(r'\r\n|\r|\n', '\n', value)  # normalize newlines
    paras = re.split('\n{2,}', value)
    paras = [u'%s' % p.replace('\n', '<br />') for p in paras]
    paras = u'\n\n'.join(paras)
    return Markup(paras)


@blueprint.app_template_filter()
def markdown(value):
    """Run text through markdown process"""
    return Markup(Markdown.markdown(value))
