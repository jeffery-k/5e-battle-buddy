# Prompts
PROMPT_START = "Enter q to quit, i for info, and enter to start: "
PROMPT_YES_NO = "Enter Y or N: "
PROMPT_NUMERIC = "Enter a number: "
PROMPT_ENTER = "Press Enter to Continue: "

INVALID = "INPUT INVALID!"

# Regular Expressions
REGEX_LONG_PATH = '/'
REGEX_QUIT = 'q$|quit$'
REGEX_INFO = 'i$|info$'
REGEX_START = 'q$|i$|quit$|info$|$'
REGEX_BLANK = '$'
REGEX_ALL = '.*'

SEPARATOR = '_'
REGEX_AM = '.*_am$'
REGEX_SAVE = '.*_save$'

# Top-level Config Properties
MATCH = 'game'
MATCHES = 'games'
CONFIG = 'config'
CHARACTERS = 'characters'
CHARACTER = 'character'
SKILLS = 'skills'
ABILITIES = 'abilities'
RESOURCES = 'resources'
STRATEGY = 'strategy'
GAME_CHARACTERS = 'game_characters'

# Strategy Manager Properties
MAXIMUM_TURNS = 'maximum_turns'
SIMULATIONS_PER_GENERATION = 'simulations_per_generation'
NOVEL_STRATEGY_COUNT = 'novel_strategy_count'
CLONED_STRATEGY_COUNT = 'cloned_strategy_count'
MUTATED_STRATEGY_COUNT = 'mutated_strategy_count'
MERGED_STRATEGY_COUNT = 'merged_strategy_count'
MAX_STRATEGY_COMPLEXITY = 'max_strategy_complexity'
MUTATION_COEFFICIENT = 'mutation_coefficient'
FITNESS_IMPROVEMENT_THRESHOLD = 'fitness_improvement_threshold'
STRATEGY_GROUPING = 'strategy_grouping'

# Key 5ebb-JSON Properties
PROFILE = 'profile'
ARGUMENTS = 'arguments'
CONDITIONS = 'conditions'
EFFECTS = 'effects'
SUCCESS_EFFECTS = 'success_effects'
FAILURE_EFFECTS = 'failure_effects'
VALUE = 'value'
TYPE = 'type'
NAME = 'name'
BONUS = 'bonus'
CONTEXT = 'property'
PROTOTYPE = 'prototype'
PROTOTYPES = 'prototypes'
PROPERTIES = 'properties'
TRIGGER = 'trigger'
INITIAL = 'initial'
COMPULSORY = 'compulsory'
TARGETING = 'targeting'
TARGET = 'target'
HOOK = 'hook'

# Basic Functions
ADDITION = 'addition'
SUBTRACTION = 'subtraction'
MULTIPLICATION = 'multiplication'
DIVISION = 'division'
GREATER = 'greater'
LESS = 'less'
GREATER_OR_EQUAL = 'greater_or_equal'
LESS_OR_EQUAL = 'less_or_equal'
MAXIMUM = 'max'
MINIMUM = 'min'
MAP = 'map'
CONTAINS = 'contains'
ANY = 'any'
OR = 'or'
AND = 'and'
NOT = 'not'
GET = 'get'
EVAL = 'eval'

# Die
DIE_ROLL = 'roll'
DIE_COUNT = 'count'
DIE_SIDES = 'sides'

# Hooks
START_OF_TURN = 'start_turn'
END_OF_TURN = 'end_turn'
ROLL = 'roll'
MOVEMENT = 'movement'
THREATENED_ZONE_ENTRANCE = 'threatened_zone_entrance'
THREATENED_ZONE_EXIT = 'threatened_zone_exit'
DAMAGE_DONE = 'damage_done'
DAMAGE_TAKEN = 'damage_taken'
DEATH = 'death'
REMOVAL_FROM_PLAY = 'remove_from_play'
INITIALIZE = 'initialize'

# Affinities
HOSTILE = 'hostile'
FRIENDLY = 'friendly'
SELF = 'self'

# D&D Skills
ABSTAIN = 'abstain'
MOVEMENT_SKILL = 'movement'
DODGE = 'dodge'
ATTACK = 'attack'
ACTION_ATTACK = 'action_attack'
OPPORTUNITY_ATTACK = 'opportunity_attack'
DISENGAGE = 'disengage'

# D&D Targeting
SELF_TARGET = 'self'
SINGLE_TARGET = 'single_target'
RANGED_TARGET = 'ranged_attack'
TILE_TARGET = 'terrain_target'

# D&D Effects
END_TURN = 'end_turn'
MOVEMENT_EFFECT = 'movement'
SET = 'set'
CREDIT = 'credit'
DEBIT = 'debit'
ATTACK_EFFECT = 'attack'
DAMAGE_EFFECT = 'damage'
ADVANTAGE = 'advantage'
DISADVANTAGE = 'disadvantage'
REMOVE_FROM_PLAY = 'remove_from_play'

# D&D Properties
STRENGTH = 'strength'
DEXTERITY = 'dexterity'
CONSTITUTION = 'constitution'
INTELLIGENCE = 'intelligence'
WISDOM = 'wisdom'
CHARISMA = 'charisma'

ALIGNMENT = 'alignment'
POSITION = 'position'
INITIATIVE = 'initiative'
BOARD_WIDTH = 'board_width'
BOARD_HEIGHT = 'board_height'

LEVEL = 'level'
MAX_HP = 'max_hp'
INITIATIVE_BONUS = 'initiative_bonus'

MAX_QUANTITY = 'max_quantity'
HIT_POINT = 'hit_point'
CURRENT_ROLL = 'current_roll'
DAMAGE = 'damage'
RESOURCE_LEVEL = 'level'
QUANTITY = 'quantity'

# Temp Contexts
ATTACK_ATTRIBUTES = 'attack_attributes'
DAMAGE_ATTRIBUTES = 'damage_attributes'
ROLL_ATTRIBUTES = 'roll_attributes'
ATTRIBUTES = 'attributes'
ACTOR = 'actor'

HIT_METRIC = 'hit_metric'
SAVE_METRIC = 'save_metric'
HIT_CONDITIONS = 'hit_conditions'
