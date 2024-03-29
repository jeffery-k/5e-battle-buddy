from match import *
from basic import *

from multiprocessing.pool import Pool


# Strategy


class StrategyManager(BasicContext):
    def __init__(self, match_data, expression):
        super().__init__()
        self.character_templates = []
        self.match_data = match_data
        self.match = None
        self.maximum_turns = expression[MAXIMUM_TURNS]
        self.simulations_per_strategy = expression[SIMULATIONS_PER_STRATEGY]
        self.novel_strategy_count = expression[NOVEL_STRATEGY_COUNT]
        self.cloned_strategy_count = expression[CLONED_STRATEGY_COUNT]
        self.mutated_strategy_count = expression[MUTATED_STRATEGY_COUNT]
        self.merged_strategy_count = expression[MERGED_STRATEGY_COUNT]
        self.max_strategy_complexity = expression[MAX_STRATEGY_COMPLEXITY]
        self.mutation_coefficient = expression[MUTATION_COEFFICIENT]
        self.fitness_improvement_threshold = expression[FITNESS_IMPROVEMENT_THRESHOLD]
        self.strategy_grouping = expression[STRATEGY_GROUPING]

        for definition_name in match_data[GAME_CHARACTERS]:
            characters = create_contexts(self.environment.characters[definition_name], MatchCharacter)
            for character in characters:
                self.character_templates.append(character)

        self.strategies = StrategyMap(self)

    def get_strategy_name(self, character):
        return character.eval(self.strategy_grouping)

    # Sole source of display_messages
    def step(self, display):
        display_message = DisplayMessage(display)
        match_context = MatchContext(self.maximum_turns, properties=self.match_data,
                                     strategies=self.strategies, display_message=display_message)
        display_message.input()
        match_context.simulate(display=display)

    def optimize(self, strategy_name):
        old_strategy = self.strategies[strategy_name]
        if old_strategy is None:
            old_strategy = Strategy(self, name=strategy_name, nodes=[])
        cloneable_strategies = [old_strategy]
        mutateable_strategies = [old_strategy]
        mergeable_strategies = [old_strategy]
        strategies = [old_strategy]

        last_fitness = -math.inf
        best_strategy = Strategy(self, name=strategy_name, nodes=[])
        while (last_fitness * self.fitness_improvement_threshold) < best_strategy.fitness:
            last_fitness = best_strategy.fitness

            for i in range(self.novel_strategy_count):
                strategies.append(Strategy(self, name=strategy_name))
            while len(cloneable_strategies) > 0:
                strategies.append(cloneable_strategies.pop())
            while len(mutateable_strategies) > 0:
                strategies.append(mutateable_strategies.pop().mutate())
            while len(mergeable_strategies) > 1:
                strategy1 = mergeable_strategies.pop()
                strategy2 = mergeable_strategies.pop()
                strategies.append(strategy1.merge(strategy2))

            with Pool() as pool:
                for strategy in strategies:
                    temp_strategies = StrategyMap(self, self.strategies.strategies)
                    temp_strategies[strategy_name] = strategy
                    fitness_set_values = pool.imap_unordered(
                        get_fitness,
                        self.get_match_context_generator(temp_strategies)
                        )
                    fitness_values = map(lambda fitness_set: fitness_set.get(strategy_name), fitness_set_values)
                    total_fitness = sum(fitness_values)

                    average_fitness = total_fitness / self.simulations_per_strategy
                    self.log("Strategy " + strategy.name + " averaged a fitness of " + str(average_fitness))
                    strategy.fitness = average_fitness

                    cloneable_strategies.append(strategy)
                    mutateable_strategies.append(strategy)
                    mergeable_strategies.append(strategy)

                    if strategy.fitness > best_strategy.fitness:
                        best_strategy = strategy

            cloneable_strategies = self.trim_cloneable(cloneable_strategies)
            mutateable_strategies = self.trim_mutateable(mutateable_strategies)
            mergeable_strategies = self.trim_mergeable(mergeable_strategies)
            random.shuffle(mergeable_strategies)

        self.strategies[strategy_name] = best_strategy

    def get_match_context_generator(self, temp_strategies):
        count = 0
        while count < self.simulations_per_strategy:
            count += 1
            match_context = MatchContext(self.maximum_turns, properties=self.match_data,
                                         strategies=temp_strategies)
            yield match_context

    def trim_cloneable(self, strategies):
        return trim(strategies, self.cloned_strategy_count, lambda strategy: strategy.fitness)

    def trim_mutateable(self, strategies):
        return trim(strategies, self.mutated_strategy_count, lambda strategy: strategy.fitness)

    def trim_mergeable(self, strategies):
        return trim(strategies, self.merged_strategy_count, lambda strategy: strategy.fitness)

    def get_random_weight(self):
        return random.randint(0, 10)


def get_fitness(match_context):
    match_context.simulate()
    return match_context.get_fitness_set()


class StrategyMap(BasicContext):
    def __init__(self, strategy_manager, strategies=None):
        self.strategy_manager = strategy_manager
        self.strategies = {}
        if strategies is not None:
            for strategy in strategies:
                self.strategies[strategy] = strategies[strategy]

        for character_template in strategy_manager.character_templates:
            strategy_name = character_template.eval(strategy_manager.strategy_grouping)
            if strategy_name not in self.strategies:
                self.strategies[strategy_name] = Strategy(self.strategy_manager, name=strategy_name, nodes=[])
        super().__init__()
        self.properties = self.strategies

    def get_strategy(self, character):
        strategy_name = self.strategy_manager.get_strategy_name(character)
        if self.strategies.get(strategy_name) is None:
            self.strategies[strategy_name] = Strategy(self, name=strategy_name)
        return self.strategies[strategy_name]

    def get(self, key):
        return self.strategies.get(key)


class Strategy(BasicContext):
    id = 8888

    def __init__(self, strategy_manager, name='', nodes=None):
        if name == '':
            name = str(self.id)
            self.id += 1
        super().__init__(name=name)
        self.strategy_manager = strategy_manager
        self.name = name
        self.fitness = 0
        if nodes is None:
            nodes = [Node(strategy_manager, self, strategy_manager.get_random_weight())]
        self.nodes = nodes

    def merge(self, strategy):
        strategy = Strategy(self.strategy_manager, self.name, self.nodes + strategy.nodes)
        strategy.nodes = trim(strategy.nodes,
                              self.strategy_manager.max_strategy_complexity)
        return strategy

    def mutate(self):
        return Strategy(self.strategy_manager, self.name)

    # TODO: choose_action should filter nodes by condition *before* calculating weights
    def choose_action(self, match, action_list):
        weights = {}
        for action in action_list:
            weights[action] = 0
            for node in self.nodes:
                weights[action] += node.weigh(action)

        best_action = None
        largest_weight = -math.inf
        for action in weights:
            weight = weights[action]
            if weight > largest_weight:
                largest_weight = weight
                best_action = action

        return best_action


# keep immutable
class Node(BasicContext):
    def __init__(self, strategy_manager, strategy, weight=0):
        super().__init__()
        self.strategy_manager = strategy_manager
        self.strategy = strategy
        self.weight = weight
        self.condition = MetaCondition(strategy_manager)
        self.action = MetaAction(strategy_manager, strategy)

    def mutate(self):
        return Node(self.strategy_manager, self.strategy, self.weight + random.randint(-1, 1))

    def weigh(self, action):
        if self.check_action(action):
            return self.weight
        else:
            return 0

    def check_action(self, action):
        return self.condition.check(action) and self.action.check(action)

    def __str__(self):
        string = ''
        string += 'If ' + str(self.condition) + ', then ' + str(self.action)
        string += '\n' + THIN_DIVIDER + '\nwith weight [' + str(self.weight) + ']'
        return string


class MetaCondition(BasicContext):
    def __init__(self, strategy_manager=None, properties=None, name='', base=None):
        super().__init__(properties, name, base)
        self.strategy_manger = strategy_manager
        self.target = random.choice(strategy_manager.character_templates)
        self.status = get_meta_status(strategy_manager)

    def check(self, action):
        return self.status.check(select(action.get_match().match_characters,
                                        lambda character: character.name == self.target.name))

    def __str__(self):
        string = ''
        string += '[' + self.target.name + '] has ' + str(self.status)
        return string


def get_meta_status(strategy_manager):
    # TODO: you know what
    if random.randint(0, 1) == 0:
        return HealthMetaStatus(strategy_manager, random.randint(0, 10))
    else:
        return DamageMetaStatus(strategy_manager, random.randint(0, 10))


class HealthMetaStatus(BasicContext):
    def __init__(self, strategy_manager=None, value=0, properties=None, name='', base=None):
        super().__init__(properties, name, base)
        self.strategy_manager = strategy_manager
        self.value = value

    # TODO: change to a percentile check
    def check(self, target):
        return target.get_hp().get_quantity() > self.value

    def __str__(self):
        string = ''
        string += '[health] greater than [' + str(self.value) + ']'
        return string


class DamageMetaStatus(BasicContext):
    def __init__(self, strategy_manager=None, value=0, properties=None, name='', base=None):
        super().__init__(properties, name, base)
        self.strategy_manager = strategy_manager
        self.value = value

    # TODO: change to a percentile check
    def check(self, target):
        return target.get_hp().get_damage() > self.value

    def __str__(self):
        string = ''
        string += '[damage] greater than [' + str(self.value) + ']'
        return string


class MetaAction(BasicContext):
    def __init__(self, strategy_manager=None, strategy=None, properties=None, name='', base=None):
        super().__init__(properties, name, base)
        self.strategy_manager = strategy_manager
        actors = [character for character in strategy_manager.character_templates
                  if strategy_manager.get_strategy_name(character) is strategy.name]
        self.actor = MetaCharacter(strategy_manager, characters=actors)
        act_names = [] if self.actor.character is None else list(self.actor.character.skills)
        name = ''
        if len(act_names) > 0:
            name = random.choice(act_names)
        self.act = MetaAct(strategy_manager, name=name)

    def check(self, action):
        return self.actor.check(action.actor) and self.act.check(action)

    def __str__(self):
        string = ''
        string += '[' + str(self.actor) + '] ' + str(self.act)
        return string


class MetaAct(BasicContext):
    def __init__(self, strategy_manager=None, properties=None, name='', base=None):
        super().__init__(properties, name, base)
        self.strategy_manager = strategy_manager
        self.target = MetaCharacter(strategy_manager)

    def check(self, action):
        return self.target.check(action.target) and action.name == self.name

    def __str__(self):
        string = ''
        name = self.name
        if name == '':
            name = 'anything'
        string += 'do [' + name + '] at [' + str(self.target) + ']'
        return string


class MetaCharacter(BasicContext):
    def __init__(self, strategy_manager=None, characters=None, properties=None, name='', base=None):
        super().__init__(properties, name, base)
        self.strategy_manager = strategy_manager
        if characters is None:
            characters = [character for character in strategy_manager.character_templates]
            characters.append(None)
        self.character = random.choice(characters)

    def check(self, target):
        character = self.character
        if character is None:
            return True
        else:
            return target.name == character.name

    def __str__(self):
        if self.character is None:
            return 'Anyone'
        else:
            return self.character.name
