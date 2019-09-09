import os
import json
from src.display import Display
from src.strategy import *


# Driver

def unload_config(config):
    environment = Environment()
    BasicContext.environment = environment

    environment.characters = get_concretes(config[CHARACTERS])
    environment.skills = get_concretes(config[SKILLS])
    environment.abilities = get_concretes(config[ABILITIES])
    environment.resources = get_concretes(config[RESOURCES])

    match_data = get_concretes(config[MATCHES])[config[MATCH]]
    return StrategyManager(match_data, config[STRATEGY])


def load_config():
    config = load('config.json')
    for file in config['configs']:
        deep_fill(config, load(file))
    return config


def load(path):
    if not re_match(REGEX_LONG_PATH, path):
        path = os.getcwd() + '/config/' + path
    return json.load(open(path))


def get_concretes(expression):
    values = {}
    concretes = {}

    for key in expression:
        value = expression[key]
        if is_list(value):
            concretes[key] = collapse_set(value, expression)
        else:
            if value.get(NAME) is None:
                value[NAME] = key
            if value.get(PROTOTYPE) is None:
                value[PROTOTYPE] = False

            prototypes = []
            if PROTOTYPES in value:
                prototypes = value[PROTOTYPES]

            for prototype in prototypes:
                deep_fill(value, values[prototype])

            values[key] = value

    for v_key in values:
        value = values[v_key]
        if not value.get(PROTOTYPE):
            properties = pop(value, PROPERTIES)
            if properties is not None:
                for p_key in properties:
                    p_value = properties[p_key]
                    value = map_dict(value, lambda x: check_and_replace(x, p_key, p_value))

            concretes[v_key] = value

    return concretes


def report_strategies(manager, display):
    for strategy_name in manager.strategies:
        report_strategy(manager.strategies[strategy_name], display)


def report_strategy(strategy, display):
    report = 'Strategy: ' + strategy.name
    for node in strategy.nodes:
        report += '======='
        report += str(node)
    display.input(string=report, prompt='Press enter to continue:')


def main():
    display = Display()
    config = load_config()
    # display.print(json.dumps(config))
    manager = unload_config(config)
    optimization_count = 0

    while True:
        # user_input = display.input("There have been " + str(optimization_count)
        #                            + " optimization(s) made.\n"
        #                            + "Enter q to quit, i for info, the name of a strategy to optimize it,"
        #                            + " or nothing to optimize all strategies")
        user_input = ''

        if re_match(REGEX_QUIT, user_input):
            quit(1)
        elif re_match(REGEX_INFO, user_input):
            report_strategies(manager, display)
        elif re_match(REGEX_BLANK, user_input):
            for strategy_name in manager.strategies:
                strategy = manager.strategies[strategy_name]
                manager.optimize(strategy.name)
                optimization_count += 1
                report_strategy(strategy, display)
        else:
            strategy = manager.strategies[user_input]
            if strategy is None:
                display_invalid(display)
            else:
                manager.optimize(strategy.name)
                optimization_count += 1
                report_strategy(strategy, display)


if __name__ == '__main__':
    main()