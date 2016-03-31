"""Write output files for configurations."""
import collections
import json
import logging

import gogoutils

from .utils import get_template

LOG = logging.getLogger(__name__)


def write_variables(app_configs=None, out_file='', git_short=''):
    """Append _application.json_ configurations to _out_file_ and .exports.

    Variables are written in INI style, e.g. UPPER_CASE=value. The .exports file
    contains 'export' prepended to each line for easy sourcing.

    Args:
        app_configs (dict): Environment configurations from _application.json_
            files, e.g. {'dev': {'elb': {'subnet_purpose': 'internal'}}}.
        out_file (str): Name of INI file to append to.
        git_short (str): Short name of Git repository, e.g. forrest/core.

    Returns:
        True upon successful completion.
    """
    generated = gogoutils.Generator(*gogoutils.Parser(git_short).parse_url())

    json_configs = {}
    for env, configs in app_configs.items():
        rendered_configs = json.loads(get_template('configs.json.j2',
                                                   env=env,
                                                   app=generated.app))
        LOG.debug('Rendered config template:\n%s', rendered_configs)
        json_configs[env] = dict(collections.ChainMap(configs,
                                                      rendered_configs))

    config_lines = []
    for env, configs in json_configs.items():
        for resource, app_properties in sorted(configs.items()):
            try:
                for app_property, value in sorted(app_properties.items()):
                    variable = '{env}_{resource}_{app_property}'.format(
                        env=env,
                        resource=resource,
                        app_property=app_property).upper()

                    raw_value = json.dumps(value)
                    if isinstance(value, dict):
                        safe_value = "'{0}'".format(raw_value)
                    else:
                        safe_value = raw_value

                    line = "{variable}={value}".format(variable=variable,
                                                       value=safe_value)

                    LOG.debug('INI line: %s', line)
                    config_lines.append(line)
            except AttributeError:
                continue

    with open(out_file, 'at') as jenkins_vars:
        LOG.info('Appending variables to %s.', out_file)
        jenkins_vars.write('\n'.join(config_lines))

    with open(out_file + '.exports', 'wt') as export_vars:
        LOG.info('Writing sourceable variables to %s.', export_vars.name)
        export_vars.write('\n'.join('export {0}'.format(line)
                                    for line in config_lines))

    with open(out_file + '.json', 'wt') as json_handle:
        LOG.debug('Total JSON dict:\n%s', json_configs)
        json.dump(json_configs, json_handle)

    return True