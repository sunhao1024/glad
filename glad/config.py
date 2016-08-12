class ConfigException(Exception):
    pass


class InvalidConfig(ConfigException):
    pass


class OptionRequired(InvalidConfig):
    def __init__(self, name, option):
        ConfigException.__init__(self, 'Required option {!r} not set'.format(name))

        self.name = name
        self.option = option


class ConstraintException(InvalidConfig):
    def __init__(self, message, constraint):
        InvalidConfig.__init__(self, message)

        self.constraint = constraint


class RequirementNotSatisfied(ConstraintException):
    pass


class InvalidOption(ConfigException):
    def __init__(self, name):
        ConfigException.__init__(self, 'Invalid option {!r}'.format(name))

        self.name = name


def identity(x):
    return x


def one_of(choices):
    def validator(x):
        if x not in choices:
            raise ValueError('invalid choice {!r}, expected one of {!r}', x, choices)

    validator.__config__doc__ = 'One of: {!r}'.format(choices)
    return validator


class ConfigOption(object):
    def __init__(self, description, converter=None, default=None, required=False):
        self.converter = converter
        if self.converter is None:
            self.converter = identity

        self.description = description
        self.default = default
        self.required = required

        try:
            self.description = '{}. {}'.format(
                self.description.rstrip('. '),
                self.converter.__config_doc__
            )
        except AttributeError:
            pass

        if self.default and self.required:
            raise ValueError(
                'ConfigOption cannot have a default and be required at the same time.'
            )

    def to_parser_arguments(self):
        args = dict(
            type=self.converter,
            help=self.description,
        )

        if self.required:
            args['required'] = True
        else:
            if self.converter is bool:
                args['action'] = 'store_false' if self.default else 'store_true'
                args.pop('type')
            else:
                args['default'] = self.default

        return args


class Constraint(object):
    def validate(self, config):
        pass


class RequirementConstraint(object):
    """
    Specifies a simple requirement constraint.
    If a list of options are given (True), the requirement needs to be True as well.
    This only checks for the variables boolean values.
    """
    def __init__(self, options, require, error_formatter=None):
        self.options = options
        self.require = require

        if len(self.options) == 0:
            raise ValueError('At least one option required')

        self._error_formatter = error_formatter
        if self._error_formatter is None:
            self._error_formatter = self._format_error

    def validate(self, config):
        if all(config[option] for option in self.options) and not config[self.require]:
            raise RequirementNotSatisfied(self._error_formatter(self, config), self)

    @staticmethod
    def _format_error(constraint, config):
        plural = len(constraint.options) > 1
        options = ', '.join(constraint.options[:-1])
        if options:
            options = '{} and {}'.format(options, constraint.options[-1])
        else:
            options = constraint.options[0]

        return 'option{s} {options} require{not_s} option {require}'.format(
            options=options,
            require=constraint.require,
            s='s' if plural else '',
            not_s='' if plural else 's'
        )


class Config(object):
    """
    Base for all glad configurations. The class with initiliaze the options
    with it iself. Every uppercase name will be assumed to be a configuration option
    and should be of type ConfigOption:

        class MyAwesomeConfig(Config):
            DEBUG = ConfigOption(
                converter=bool,
                default=False
                description='Enables debug output'
            )
            ITERATIONS = ConfigOption(
                converter=int,
                required=True
                description='Number of iterations'
            )

        config = MyAwesomeConfig()
        config['DEBUG'] = True

        # update config from file
        # ...
        # now make sure every required option has been set
        config.validate()

        if config['DEBUG']:
            print 'debug information'

        Special Constraints can be specified in the __constraints__ variable.

            class MyConstraintConfig(MyAwesomeConfig):
                __constraints__ = [
                    RequirementConstraint(['DEBUG'], 'iterations')
                ]

        The constraints will be checked when calling `.valid` or `.validate()`
    """

    def __init__(self):
        self._options = dict()
        self._values = dict()

        # initialize options, every uppercase name = option
        for name in dir(self):
            if name.isupper():
                option = self._options[name] = getattr(self, name)

                if not option.required:
                    self._values[name] = option.default

    def set(self, name, value, convert=True):
        try:
            option = self._options[name]
        except KeyError:
            raise InvalidOption(name)

        if convert:
            value = option.converter(value)
        self._values[name] = value

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def __getitem__(self, item):
        return self._values[item]

    def __setitem__(self, key, value):
        self.set(key, value, convert=True)

    @property
    def valid(self):
        """
        Checks if every required option has been set.

        :return: True if everything has been set otherwise False
        """
        try:
            self.validate()
        except InvalidConfig:
            return False
        return True

    def validate(self):
        """
        Checks if every required option has been set.
        Throws InvalidConfig if a required option is missing.
        This also checks all specified constraints.

        Should be overwritten by subclasses if necessary.
        """
        for name, option in self._options.items():
            if option.required:
                if not name in self._values:
                    raise OptionRequired(name, option)

        constraints = getattr(self, '__constraints__', [])
        for constraint in constraints:
            constraint.validate(self)

    def update_from_object(self, obj, convert=True, ignore_additional=False):
        for name in dir(obj):
            if not name.startswith('_'):
                try:
                    self.set(name, getattr(obj, name), convert=convert)
                except InvalidOption:
                    if not ignore_additional:
                        raise

    def init_parser(self, parser):
        for name, option in self._options.items():
            parser_name = '--' + name.lower().replace('_', '-')

            parser.add_argument(
                parser_name,
                dest=name,
                **option.to_parser_arguments()
            )

    def to_dict(self, transform=None):
        if transform is None:
            transform = identity

        result = dict()

        for name, value in self._values.items():
            result[transform(name)] = value

        return result
