import os
import resource
import shutil
import subprocess


def run_process_mesh_exe(mesh_fname='generated.vol',
        process_mesh_exe='/home/anton/FEMFolder/processMesh.x',
        libs='/home/anton/FEMFolder/libs', my_libs='/home/anton/FEMFolder/my_libs',
        stdout_exe=None, stderr_exe=None, memory_ratio=0.3):
    """
    Runs processMesh.x from the specified folder producing 'mesh.xdr'.

    Parameters:
        mesh_fname          name of the mesh generated by gen_mesh.x
        process_mesh_exe    name of the processMesh executable
        libs                directory where netgen libs are stored
        my_libs             directory where libs are stored that exist on cluster
                                but not on my pc

        stdout_exe          stdout of processMesh executable
        stderr_exe          stderr of processMesh executable

        memory_ratio        the fraction of whole memory that may be used;
                                otherwise crash is highly possible
    """
    fem_env = os.environ
    fem_env['LD_LIBRARY_PATH'] = '{0}:{1}'.format(libs, my_libs)
    if stdout_exe:
        stdout_exe = open(stdout_exe, 'w')
    if stderr_exe:
        stderr_exe = open(stderr_exe, 'w')
    memory_limitation = 1024**3 * 8 * memory_ratio

    # mesh_fname -> 'out.mesh'
    shutil.move(mesh_fname, 'out.mesh')

    # run processMesh
    code = subprocess.call(
        process_mesh_exe,
        env=fem_env,
        preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS,
            (memory_limitation, memory_limitation)),
        stdout=stdout_exe, stderr=stderr_exe)

    if code in [0, 2]:
        return True
    return False


if __name__ == '__main__':
    def test_run_process_mesh_exe():
        run_process_mesh_exe()

    test_run_process_mesh_exe() # ok