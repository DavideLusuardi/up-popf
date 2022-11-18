import os
import sys
import re
from fractions import Fraction
from typing import IO, Any, Callable, Optional, List, Tuple, Union, cast

import unified_planning as up
from unified_planning.io.pddl_writer import PDDLWriter
from unified_planning.model import ProblemKind
from unified_planning.engines import OptimalityGuarantee, PlanGenerationResult, PlanGenerationResultStatus
from unified_planning.engines import PDDLPlanner, Credits
from unified_planning.exceptions import UPException


credits = Credits('POPF',
                  'Davide Lusuardi',
                  'davide.lusuardi@studenti.unitn.it',
                  'https://nms.kcl.ac.uk/planning/software/popf.html',
                  'GPLv3',
                  'POPF is forwards-chaining temporal planner.',
                  'POPF is forwards-chaining temporal planner.')


class popfPDDLPlanner(PDDLPlanner):

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return 'POPF'

    @staticmethod
    def get_credits(**kwargs) -> Optional['Credits']:
        return credits

    def _plan_from_file(
        self,
        problem: "up.model.Problem",
        plan_filename: str,
        get_item_named: Callable[
            [str],
            Union[
                "up.model.Type",
                "up.model.Action",
                "up.model.Fluent",
                "up.model.Object",
                "up.model.Parameter",
                "up.model.Variable",
            ],
        ],
    ) -> "up.plans.Plan":
        """
        Takes a problem, a filename and a map of renaming and returns the plan parsed from the file.

        :param problem: The up.model.problem.Problem instance for which the plan is generated.
        :param plan_filename: The path of the file in which the plan is written.
        :param get_item_named: A function that takes a name and returns the original up.model element instance
            linked to that renaming.
        :return: The up.plans.Plan corresponding to the parsed plan from the file
        """
        actions: List = []
        with open(plan_filename) as plan:
            is_tt = False
            for line in plan.readlines():
                if re.match(r"^\s*(;.*)?$", line):
                    continue
                line = line.lower()
                s_ai = re.match(r"^\s*\(\s*([\w?-]+)((\s+[\w?-]+)*)\s*\)\s*$", line)
                t_ai = re.match(
                    r"^\s*(\d+\.\d+):\s*\(\s*([\w-]+)([\s\w-]*)\)\s*\[(\d+\.\d+)\]\s*$", # TODO
                    # r"^\s*(\d+)\s*:\s*\(\s*([\w?-]+)((\s+[\w?-]+)*)\s*\)\s*(\[\s*(\d+)\s*\])?\s*$",
                    line,
                )
                if s_ai:
                    assert is_tt == False
                    name = s_ai.group(1)
                    params_name = s_ai.group(2).split()
                elif t_ai:
                    is_tt = True
                    start = Fraction(t_ai.group(1))
                    name = t_ai.group(2)
                    params_name = [arg.strip() for arg in t_ai.group(3).split()]
                    dur = None
                    if t_ai.group(4) is not None:
                        dur = Fraction(t_ai.group(4))
                else:
                    raise UPException(
                        "Error parsing plan generated by " + self.__class__.__name__
                    )

                action = get_item_named(name)
                assert isinstance(action, up.model.Action), "Wrong plan or renaming."
                parameters = []
                for p in params_name:
                    obj = get_item_named(p)
                    assert isinstance(obj, up.model.Object), "Wrong plan or renaming."
                    parameters.append(problem.env.expression_manager.ObjectExp(obj))
                act_instance = up.plans.ActionInstance(action, tuple(parameters))
                if is_tt:
                    actions.append((start, act_instance, dur))
                else:
                    actions.append(act_instance)
        if is_tt:
            return up.plans.TimeTriggeredPlan(actions)
        else:
            return up.plans.SequentialPlan(actions)

    def _get_cmd(self, domain_filename: str,
                 problem_filename: str, plan_filename: str) -> List[str]:
        executable = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'plan.py')
        cmd = [sys.executable, executable, domain_filename, problem_filename, plan_filename]
        return cmd

    def _result_status(
        self,
        problem: "up.model.Problem",
        plan: Optional["up.plans.Plan"],
        retval: int = None, # Default value for legacy support
        log_messages = None,
        ) -> "up.engines.results.PlanGenerationResultStatus":

        if retval is None or retval in (0, 1):
            if plan is None:
                return PlanGenerationResultStatus.UNSOLVABLE_INCOMPLETELY
            else:
                return PlanGenerationResultStatus.SOLVED_SATISFICING
        else:
            return up.engines.results.PlanGenerationResultStatus.INTERNAL_ERROR

    @staticmethod
    def satisfies(optimality_guarantee: 'OptimalityGuarantee') -> bool:
        if optimality_guarantee == OptimalityGuarantee.SATISFICING:
            return True
        return False

    @staticmethod
    def supported_kind() -> 'ProblemKind':
        supported_kind = ProblemKind()
        supported_kind.set_problem_class('ACTION_BASED')
        supported_kind.set_problem_type("SIMPLE_NUMERIC_PLANNING")
        supported_kind.set_problem_type("GENERAL_NUMERIC_PLANNING")
        supported_kind.set_time('CONTINUOUS_TIME')
        supported_kind.set_time('DISCRETE_TIME')
        supported_kind.set_time('DURATION_INEQUALITIES')
        supported_kind.set_expression_duration('STATIC_FLUENTS_IN_DURATION')
        supported_kind.set_expression_duration('FLUENTS_IN_DURATION')
        supported_kind.set_numbers('CONTINUOUS_NUMBERS')
        supported_kind.set_numbers('DISCRETE_NUMBERS')
        supported_kind.set_conditions_kind('NEGATIVE_CONDITIONS')
        supported_kind.set_conditions_kind('DISJUNCTIVE_CONDITIONS')
        supported_kind.set_conditions_kind('EQUALITY')
        supported_kind.set_effects_kind('CONDITIONAL_EFFECTS')
        supported_kind.set_effects_kind('INCREASE_EFFECTS')
        supported_kind.set_effects_kind('DECREASE_EFFECTS')
        supported_kind.set_typing('FLAT_TYPING')
        supported_kind.set_typing('HIERARCHICAL_TYPING')
        supported_kind.set_fluents_type('NUMERIC_FLUENTS')
        supported_kind.set_fluents_type('OBJECT_FLUENTS')
        supported_kind.set_quality_metrics('ACTIONS_COST')
        return supported_kind

    @staticmethod
    def supports(problem_kind: 'ProblemKind') -> bool:
        return problem_kind <= popfPDDLPlanner.supported_kind()

