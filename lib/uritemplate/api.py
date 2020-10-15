"""

uritemplate.base
===============

This module contains the very simple API provided by uritemplate.

"""
from uritemplate.template import URITemplate


def expand(uri, var_dict=None, **kwargs):
    """Expand the template with the given parameters.

    :param str uri: The templated URI to expand
    :param dict var_dict: Optional dictionary with variables and values
    :param kwargs: Alternative way to pass arguments
    :returns: str

    Example::

        expand('https://base.github.com{/end}', {'end': 'users'})
        expand('https://base.github.com{/end}', end='gists')

    .. note:: Passing values by both parts, may override values in
              ``var_dict``. For example::

                  expand('https://{var}', {'var': 'val1'}, var='val2')

              ``val2`` will be used instead of ``val1``.

    """
    return URITemplate(uri).expand(var_dict, **kwargs)


def partial(uri, var_dict=None, **kwargs):
    """Partially expand the template with the given parameters.

    If all of the parameters for the template are not given, return a
    partially expanded template.

    :param dict var_dict: Optional dictionary with variables and values
    :param kwargs: Alternative way to pass arguments
    :returns: :class:`URITemplate`

    Example::

        t = URITemplate('https://base.github.com{/end}')
        t.partial()  # => URITemplate('https://base.github.com{/end}')

    """
    return URITemplate(uri).partial(var_dict, **kwargs)


def variables(uri):
    """Parse the variables of the template.

    This returns all of the variable names in the URI Template.

    :returns: Set of variable names
    :rtype: set

    Example::

        variables('https://base.github.com{/end})
        # => {'end'}
        variables('https://base.github.com/repos{/username}{/repository}')
        # => {'username', 'repository'}

    """
    return set(URITemplate(uri).variable_names)
