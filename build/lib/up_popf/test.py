# Import the PDDLReader and PDDLWriter classes
from unified_planning.io import PDDLReader, PDDLWriter
from unified_planning.shortcuts import *

reader = PDDLReader()
problem = reader.parse_problem('/home/davide/planners/unified-planning/unified_planning/test/pddl/matchcellar/domain.pddl', '/home/davide/planners/unified-planning/unified_planning/test/pddl/matchcellar/problem.pddl')

print(problem)

with OneshotPlanner(name="popf", problem_kind=problem.kind) as planner:
    print(planner.name)
    result = planner.solve(problem)
    plan = result.plan
    if plan is not None:
        print("%s returned:" % planner.name)
        for start, action, duration in plan.timed_actions:
            print("%s: %s [%s]" % (float(start), action, float(duration)))
    else:
        print("No plan found.")