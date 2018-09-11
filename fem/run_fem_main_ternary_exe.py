import os
import subprocess


def run_fem_main_ternary_exe(script_file,
        fem_main_ternary_exe='/home/anton/FEMFolder/FEManton3.o',
        libs='/home/anton/FEMFolder/libs', my_libs='/home/anton/FEMFolder/my_libs',
        stdout_exe=None, stderr_exe=None):
    """
    Runs FEMMain.o from the specified folder on single axis.

    Parameters:
        script_file         the file where task is specified
                                (axis along which the strain is applied, etc.)
        libs                directory where netgen libs are stored
        my_libs             directory where libs are stored that exist on cluster
                                but not on my pc

        stdout_exe          stdout of processMesh executable
        stderr_exe          stderr of processMesh executable

    """
    fem_env = os.environ
    fem_env['LD_LIBRARY_PATH'] = '{0}:{1}'.format(libs, my_libs)
    if stdout_exe:
        stdout_exe = open(stdout_exe, 'w')
    if stderr_exe:
        stderr_exe = open(stderr_exe, 'w')

    # run fem_main
    code = subprocess.call(
        [fem_main_ternary_exe, script_file],
        env=fem_env,
        stdout=stdout_exe, stderr=stderr_exe)

    if code == 0:
        return True
    return False


if __name__ == '__main__':
    def test_run_fem_main_ternary_exe():
        script_file = 'test_fem_input.txt'
        run_fem_main_ternary_exe(script_file)

    test_run_fem_main_ternary_exe() # ok
