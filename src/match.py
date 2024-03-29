import math

from display.display_message import DisplayMessage
from model.json_def import *
from model.prompts import *
from basic.basics import *


# Match

class InitiativeContext(BasicContext):
    def get_initiative(self, expression=None, display_message=None):
        if expression is None:
            expression = self.initiative
        if expression is None:
            expression = self.roll(get_d20())

        match_initiative = self.match_initiative
        if match_initiative is None:
            match_initiative = self.eval(expression, display_message=display_message)
            self.match_initiative = match_initiative
        return match_initiative

    def get(self, key):
        if key == INITIATIVE:
            return self.get_initiative()
        else:
            return super().get(key)


class MatchContext(BasicContext):
    def __init__(self, maximum_turns, properties=None, strategies=None, display_message=None):
        self.maximum_turns = maximum_turns
        self.board = Board(properties[BOARD_WIDTH], properties[BOARD_HEIGHT])
        self.alignments = []
        self.match_characters = []
        self.initiative_set = InitiativeSet()
        self.action_set_stack = []
        self.strategies = strategies
        super().__init__(properties, base=self.environment)
        for definition_name in properties[GAME_CHARACTERS]:
            characters = create_contexts(self.environment.characters[definition_name], MatchCharacter, base=self)
            for character in characters:
                character.set_match(self)
                self.match_characters.append(character)
                self.initiative_set.add_character(character)
                if character.alignment not in self.alignments:
                    self.alignments.append(character.alignment)
                character.trigger_hook(INITIALIZE, display_message=display_message)

        self.set_match(self)

    def get_turn(self):
        return self.initiative_set.turn

    def simulate(self, display=None):
        while self.is_ongoing():
            display_message = DisplayMessage(display)
            display_message.add_text("Characters:")
            for character in [character for character in self.match_characters if character.is_in_play()]:
                display_message.add_text(str(character))

            if len(self.action_set_stack) > 0:
                current_character = self.initiative_set.get_current_character()
                initiative = self.initiative_set.current_initiative
                turn = self.initiative_set.turn
                actions = self.action_set_stack.pop()
                strategy = self.strategies.get_strategy(current_character)

                display_message.add_section("Current Character: " + str(current_character))
                display_message.add_text("Current Initiative: " + str(initiative))
                display_message.add_text("Current Turn: " + str(turn))
                display_message.add_section("Strategy: " + strategy.name, level=2)
                # TODO: see note on 5ebb.report_strategies... shame on you
                # for node in strategy.nodes:
                #     display_message.add_text(str(node))
                display_message.add_section("Possible actions: ", level=1)
                for action in actions:
                    display_message.add_text(str(action))

                action = strategy.choose_action(self, actions)
                display_message.add_section("Action chosen: " + str(action))

                action.activate(display_message)
                for character in [character for character in self.match_characters if character.is_in_play()]:
                    character.trigger_hook(TICKER)

                display_message.input()
            else:
                character = self.initiative_set.get_next_character()
                if character is not None:
                    display_message.add_section("Current Turn: " + str(character))
                    self.action_set_stack.append(character.get_actions())

    def is_ongoing(self):
        return (self.is_conflict()) and (self.get_turn() <= self.maximum_turns)

    def is_conflict(self):
        alignments = []
        for character in self.match_characters:
            alignment = character.alignment
            if character.is_in_play() and alignment not in alignments:
                alignments.append(alignment)
                if len(alignments) > 1:
                    return True
        return False

    def get_fitness_set(self):
        fitness_set = {}
        for character in self.match_characters:
            cur_strategy_name = self.strategies.get_strategy(character).name
            if fitness_set.get(cur_strategy_name) is None:
                fitness_set[cur_strategy_name] = 0
            fitness_set[cur_strategy_name] += character.resources.get_total_value()
        return fitness_set

    def __str__(self):
        try:
            string = '<Game> ' + self.name
            for character in self.match_characters:
                string += '\n' + str(character)
            return string
        except Exception:
            return super().__str__()


class InitiativeSet(BasicContext):
    def __init__(self, properties=None, name='', base=None):
        self.characters = []
        self.turn_order = {}
        self.turn = 0
        self.initiatives = []
        self.current_initiative = math.inf
        self.current_characters = []
        super().__init__(properties, name, base)

    # Returns None upon a change in initiative
    def get_next_character(self):
        character = None

        if len(self.current_characters) > 0:
            character = self.current_characters[0]
            if not character.is_turn:
                self.current_characters.pop()
                self.trigger_start()
                character = self.get_next_character()
        else:
            self.load_current_characters()
            self.trigger_start()
            self.turn += 1

        return character

    def trigger_start(self):
        if len(self.current_characters) > 0:
            character = self.current_characters[0]
            character.is_turn = True
            character.trigger_hook(START_OF_TURN)

    def load_current_characters(self):
        i = 0
        initiative = self.initiatives[i]
        while self.current_initiative <= initiative:
            i += 1
            if i >= len(self.initiatives):
                initiative = self.initiatives[0]
                break
            initiative = self.initiatives[i]
        self.current_initiative = initiative
        self.current_characters = [character for character in self.turn_order[initiative] if character.is_in_play()]

    def get_current_character(self):
        character = None
        if len(self.current_characters) > 0:
            character = self.current_characters[0]
        return character

    def add_character(self, character):
        initiative = character.get_initiative()
        turns = self.turn_order.get(initiative)
        if turns is None:
            turns = [character]
            self.turn_order[initiative] = turns
            self.initiatives.append(initiative)
        else:
            turns.append(character)

        self.characters.append(character)
        self.initiatives.sort(reverse=True)


class MatchCharacter(InitiativeContext):
    def __init__(self, properties=None, name='', base=None):
        if name == '':
            name = properties[NAME]

        self.proficiencies = []
        self.proficiency_bonus = 0
        self.skills = []
        self.abilities = []
        self.position = None
        self.match_initiative = None
        self.match = None
        self.match_skills = {}
        self.hook_map = {}
        self.hook_targeting = {}
        self.in_play = True
        self.is_turn = False
        super().__init__(properties, name, base)

        self.alignment = MatchAlignment(name=properties[ALIGNMENT])
        self.resources = MatchResourceSet(character=self)
        self.effect_map[ATTACK_EFFECT] = self.attack
        self.effect_map[DAMAGE_EFFECT] = self.damage
        self.effect_map[CREDIT] = self.credit_effect
        self.effect_map[DEBIT] = self.debit_effect
        self.effect_map[SET] = self.set_effect
        self.effect_map[END_TURN] = self.end_turn
        self.effect_map[REMOVAL_FROM_PLAY] = self.remove_from_play

        hook_names = [INITIALIZE, ROLL, START_OF_TURN, END_OF_TURN, MOVEMENT, THREATENED_ZONE_ENTRANCE,
                      THREATENED_ZONE_EXIT, ATTACKING, ATTACKED, DAMAGE_DONE, DAMAGE_TAKEN, REMOVAL_FROM_PLAY, TICKER]
        for hook_name in hook_names:
            self.hook_map[hook_name] = []

        self.function_map[INITIATIVE] = self.get_initiative
        self.function_map[QUANTITY] = self.get_quantity
        self.function_map[IS_IN_PLAY] = self.is_in_play
        skills = [self.environment.skills[skill_name] for skill_name in self.skills]
        abilities = [self.environment.abilities[ability_name] for ability_name in self.abilities]
        for skill in create_contexts(skills, MatchSkill, base=self):
            self.match_skills[skill.name] = skill
        for ability in create_contexts(abilities, MatchAbility, base=self):
            self.hook_map[ability.hook[PROFILE]].append(ability)

        x = properties[POSITION][0]
        y = properties[POSITION][1]
        self.set(POSITION, Position(x, y))

    def trigger_hook(self, hook_name, display_message=None):
        for ability in self.hook_map[hook_name]:
            if self.check_conditions(ability.conditions, display_message=display_message):
                if display_message is not None:
                    display_message.add_section(self.get(NAME) + " triggered ability " + ability.get(NAME), level=2)
                targeting = get_targeting(self.hook_targeting.get(hook_name), base=self)
                targets = targeting.get_targets()
                target = None
                if len(targets) > 0:
                    target = targets[0]
                targeting.act(target, Trigger(ability.trigger), self, display_message=display_message)

    def get_actions(self):
        actions = []

        for skill_name in self.match_skills:
            skill = self.match_skills[skill_name]
            if self.check_conditions(skill.conditions):
                targeting = get_targeting(expression=skill[TARGETING], base=self)
                actions += targeting.get_actions(skill)

        if len(actions) == 0:
            actions.append(get_abstain_action(self))

        return actions

    def get_hp(self):
        return self.resources.get(HIT_POINT)

    def start_turn(self, expression=None, display_message=None):
        self.is_turn = True

    def end_turn(self, expression=None, display_message=None):
        self.is_turn = False

    def is_in_play(self, expression=None, display_message=None):
        return self.in_play

    def remove_from_play(self, expression=None, display_message=None):
        self.in_play = False

    def attack(self, expression, display_message=None):
        actor = self.get(ACTOR)

        attack_attributes = {
            TYPE: self.eval(expression[TYPE], display_message=display_message),
            HIT_METRIC: self.eval(expression[HIT_METRIC], display_message=display_message),
            SAVE_METRIC: self.eval(expression[SAVE_METRIC], display_message=display_message)
        }
        self.set_temp(ATTACK_ATTRIBUTES, TempAttributes(attack_attributes))
        actor.set_temp(ATTACK_ATTRIBUTES, TempAttributes(attack_attributes))
        actor.trigger_hook(ATTACKING)

        display_message.add_section("Attack to be done\n" + json.dumps(attack_attributes), level=2)
        if self.check_conditions(expression[HIT_CONDITIONS], display_message):
            damage_attributes = {
                TYPE: self.eval(expression[TYPE], display_message=display_message),
                DAMAGE: self.eval(expression[DAMAGE], display_message=display_message)
            }
            self.set_temp(DAMAGE_ATTRIBUTES, TempAttributes(damage_attributes))
            actor.set_temp(DAMAGE_ATTRIBUTES, TempAttributes(damage_attributes))
            self.trigger_hook(ATTACKED)
            display_message.add_section("Damage to be done\n" + json.dumps(damage_attributes), level=2)

            self.damage()

            self.clear_temp(DAMAGE_ATTRIBUTES)
            actor.clear_temp(DAMAGE_ATTRIBUTES)

        self.clear_temp(ATTACK_ATTRIBUTES)
        actor.clear_temp(ATTACK_ATTRIBUTES)

    def damage(self, display_message=None):
        actor = self.get(ACTOR)
        damage_attributes = self.get(DAMAGE_ATTRIBUTES)
        damage = damage_attributes.get(DAMAGE)

        self.resources.debit(self.resources.get(HIT_POINT), damage)
        self.trigger_hook(DAMAGE_TAKEN)
        actor.trigger_hook(DAMAGE_DONE)

    def roll(self, expression, display_message=None):
        self.set_temp(ROLL_ATTRIBUTES, {CURRENT_ROLL: super().roll(expression, display_message=display_message)})
        self.trigger_hook(ROLL)
        roll = self.get(ROLL_ATTRIBUTES)[CURRENT_ROLL]
        self.clear_temp(ROLL_ATTRIBUTES)
        return roll

    def credit_effect(self, expression, display_message=None):
        self.get_temp(expression.get(TARGET)).resources.get(expression[ARGUMENTS][0]).credit(
            self.eval(expression[ARGUMENTS][1], display_message=display_message))

    def debit_effect(self, expression, display_message=None):
        self.get_temp(expression.get(TARGET)).resources.get(expression[ARGUMENTS][0]).debit(
            self.eval(expression[ARGUMENTS][1], display_message=display_message))

    def set_effect(self, expression, display_message=None):
        self.get_temp(expression.get(TARGET)).resources.get(expression[ARGUMENTS][0]).set_func(
            self.eval(expression[ARGUMENTS][1], display_message=display_message))

    def get_quantity(self, expression, display_message=None):
        return self.resources.get(expression[VALUE]).quantity

    def get_temp(self, key, display_message=None):
        value = self.temp_atr.get(key)
        if value is None:
            value = self
        return value

    def get(self, key):
        if isinstance(key, str) and (re_match(REGEX_SAVE, key) or re_match(REGEX_AM, key)):
            attribute = key.split(SEPARATOR)[0]
            value = math.floor((self.get(attribute) - 10) / 2)
            if (attribute in self.proficiencies) and re_match(REGEX_SAVE, key):
                value += self.proficiency_bonus
            return value
        else:
            return super().get(key)

    def __str__(self):
        try:
            return (self.name + ' (' + str(self.position) + ') '
                    + str(self.resources.get(HIT_POINT).get_quantity()) + '/'
                    + str(self.resources.get(HIT_POINT).get_max_quantity()))
        except Exception:
            return super().__str__()


class TempAttributes(BasicContext):
    def __init__(self, attributes):
        super().__init__(properties=attributes)


class MatchAlignment(InitiativeContext):
    def __init__(self, properties=None, name='', base=None):
        self.match_initiative = None
        super().__init__(properties, name, base)

        self.function_map[INITIATIVE] = self.get_initiative


class MatchSkill(BasicContext):
    def __init__(self, properties=None, name='', base=None):
        self.targeting = None
        self.conditions = []
        self.trigger = None
        super().__init__(properties, name, base)


class MatchAbility(BasicContext):
    def __init__(self, properties=None, name='', base=None):
        self.hook = None
        self.conditions = []
        self.trigger = None
        super().__init__(properties, name, base)


def get_abstain_action(character):
    skill = MatchSkill(name=ABSTAIN)
    skill.trigger = {EFFECTS: [{PROFILE: END_TURN}]}
    targeting = get_targeting(expression={PROFILE: SELF_TARGET}, base=character)

    return MatchAction(character, skill, character, targeting, base=character)


class MatchAction(BasicContext):
    def __init__(self, actor=None, skill=None, target=None, targeting=None, properties=None, name='', base=None):
        self.actor = actor
        self.target = target
        self.targeting = targeting
        self.skill_name = skill.name
        self.trigger = skill.get(TRIGGER)
        if name == '':
            name = skill.name
        super().__init__(properties=properties, name=name, base=base)

    def activate(self, display_message=None):
        self.targeting.act(self.target, Trigger(self.trigger), actor=self.actor, display_message=display_message)

    def __str__(self):
        return ('<' + type(self).__name__ + '> ' + self.actor.name
                + ' does ' + self.skill_name + ' at ' + self.target.name)


class Targeting(BasicContext):
    def __init__(self, properties=None, name='', base=None):
        if name == '':
            name = properties.get(PROFILE)
        super().__init__(properties, name, base)

    def get_actions(self, skill):
        targets = self.get_targets()
        return [MatchAction(self.base, skill, target, self, base=skill) for target in targets]

    def get_targets(self):
        return []

    def act(self, context, trigger, actor=None, display_message=None):
        trigger = context.re_context(trigger)
        if trigger.check_conditions(display_message=display_message):
            for effect in trigger.success_effects:
                context.affect(effect, actor, display_message=display_message)
        else:
            for effect in trigger.failaure_effects:
                context.affect(effect, actor, display_message=display_message)
        for effect in trigger.effects:
            context.affect(effect, actor, display_message=display_message)


class SelfTargeting(Targeting):
    def __init__(self, properties=None, name='', base=None):
        super().__init__(properties, name, base)

    def get_targets(self):
        return [self.base]


class SingleTargeting(Targeting):
    def __init__(self, properties=None, name='', base=None):
        super().__init__(properties, name, base)

    def get_targets(self):
        return [character for character in self.get_match().match_characters if character is not self.base]


# TODO: add more targeting
def get_targeting(expression=None, base=None):
    if expression is None:
        return SelfTargeting(properties={}, base=base)
    elif expression.get(PROFILE) == SINGLE_TARGET:
        return SingleTargeting(properties=expression, base=base)
    elif expression.get(PROFILE) == RANGED_TARGET:
        return SingleTargeting(properties=expression, base=base)
    else:
        return SelfTargeting(properties=expression, base=base)


class Trigger(BasicContext):
    def __init__(self, properties=None, name='', base=None):
        super().__init__(properties, name=name, base=base)
        self.conditions = properties.get(CONDITIONS)
        self.effects = properties.get(EFFECTS)
        self.success_effects = properties.get(SUCCESS_EFFECTS)
        self.failure_effects = properties.get(FAILURE_EFFECTS)

        if self.conditions is None:
            self.conditions = []
        if self.effects is None:
            self.effects = []
        if self.success_effects is None:
            self.success_effects = []
        if self.failure_effects is None:
            self.failure_effects = []

    def check_conditions(self, conditions=None, display_message=None):
        if conditions is None:
            conditions = self.conditions
        return super().check_conditions(conditions, display_message=display_message)


class MatchResourceSet(BasicContext):
    def __init__(self, character=None, properties=None, name='', base=None):
        if properties is None:
            properties = {}

        if properties.get(RESOURCES) is None:
            resources = {}
        else:
            resources = properties.get(RESOURCES)

        if character is None:
            if properties is not None:
                character = properties.get(CHARACTER)
        else:
            properties[CHARACTER] = character

        self.resource_definitions = self.environment.resources
        self.resources = resources
        self.character = character
        super().__init__(properties, name, base)

    def get_total_value(self):
        value = 0
        for resource_name in self.resources:
            resource = self.resources[resource_name]
            value += resource.quantity * resource.value
        return value

    def get(self, key):
        if key in self.resource_definitions:
            value = self.resources.get(key)
            if value is None:
                return MatchResource(self.resource_definitions[key], self, name=key)
            else:
                return value
        else:
            return super().get(key)

    def credit(self, resource, value):
        self.set_func(resource, resource.quantity + value)

    def debit(self, resource, value):
        self.set_func(resource, resource.quantity - value)

    def set_func(self, resource, value):
        name = resource.name
        resource.quantity = value
        if value > resource.max_quantity:
            value = resource.max_quantity

        if value > 0:
            self.resources[name] = resource
        else:
            if name in self.resources:
                self.resources.pop(name)


class MatchResource(BasicContext):
    def __init__(self, properties=None, resource_set=None, name='', base=None, display_message=None):
        self.quantity = 0
        self.value = 0
        super().__init__(properties, name, base)

        self.resource_set = resource_set
        self.character = resource_set.character
        self.initial = self.character.eval(properties.get(INITIAL), display_message=display_message)
        self.max_quantity = self.character.eval(properties.get(MAX_QUANTITY), display_message=display_message)
        self.compulsory = self.character.eval(properties.get(COMPULSORY), display_message=display_message)

        if self.initial is None:
            self.initial = 0
        if self.max_quantity is None:
            self.max_quantity = math.inf
        if self.compulsory is None:
            self.compulsory = False

    def set_initial(self):
        self.resource_set.set_func(self, self.initial)

    def credit(self, value):
        self.resource_set.credit(self, value)

    def debit(self, value):
        self.resource_set.debit(self, value)

    def set_func(self, value):
        self.resource_set.set_func(self, value)

    def get_quantity(self):
        return self.quantity

    def get_max_quantity(self):
        return self.max_quantity

    def get_damage(self):
        return self.max_quantity - self.quantity if self.max_quantity is not None else self.quantity


class Board(BasicContext):
    def __init__(self, width=1, height=1, properties=None, name='', base=None):
        super().__init__(properties, name, base)
        self.width = width
        self.height = height


class Position(BasicContext):
    def __init__(self, x=0, y=0, properties=None, name='', base=None):
        super().__init__(properties, name, base)
        self.x = x
        self.y = y

    def __str__(self):
        try:
            return '[' + str(self.x) + ', ' + str(self.y) + ']'
        except Exception:
            return super().__str__()

    def get(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            return super().get(key)
