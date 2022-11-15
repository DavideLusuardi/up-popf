import sys
import os
import subprocess

def main():
    if len(sys.argv) != 4:
        exit(1) # TODO
    
    domain_filename, problem_filename, plan_filename = sys.argv[1:4]
    popf_executable = os.path.join(os.environ.get('POPF_HOME'), 'compile', 'popf2', 'popf3-clp')
    cmd = [popf_executable, domain_filename, problem_filename]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    try:
        out_err_bytes = process.communicate()
        proc_out, proc_err = [[x.decode()] for x in out_err_bytes]
        proc_out = ''.join(proc_out)
        proc_err = ''.join(proc_err)
    except subprocess.TimeoutExpired:
        exit(1) # TODO
    retval = process.returncode

    # print(f"retval: {retval}")
    # print(f"proc_err: {proc_err}")
    # print(f"proc_out: {proc_out}")

    plan = proc_out.split(';;;; Solution Found\n')[-1]
    # print(plan)

    with open(plan_filename, "w") as f:
        f.write(plan)

    exit(retval)

if __name__ == '__main__':
    main()