import os
import subprocess


def run_gen_mesh_exe(geo_fname,
        meshing_parameters=[0.15, 2, 2],
        gen_mesh_exe='/home/anton/FEMFolder/gen_mesh.x',
        libs='/home/anton/FEMFolder/libs', my_libs='/home/anton/FEMFolder/my_libs',
        stdout_exe=None, stderr_exe=None):
    """
    Runs gen_mesh.x from the specified folder.

    Parameters:
        geo_fname           the name of the strucutre file

        meshing_parameters  meshing accuracy parameters ([0.15, 2, 2] are ok)
        gen_mesh_exe        name of the gen_mesh executable
        libs                directory where netgen libs are stored
        my_libs             directory where libs are stored that exist on cluster
                                but not on my pc

        stdout_exe          stdout of gen_mesh executable
        stderr_exe          stderr of gen_mesh executable
    """
    fem_env = os.environ
    fem_env['LD_LIBRARY_PATH'] = '{0}:{1}'.format(libs, my_libs)
    if stdout_exe:
        stdout_exe = open(stdout_exe, 'w')
    if stderr_exe:
        stderr_exe = open(stderr_exe, 'w')

    code = subprocess.call(
        [gen_mesh_exe, geo_fname, *[str(p) for p in meshing_parameters]],
        env=fem_env,
        stdout=stdout_exe, stderr=stderr_exe)
    if code == 0:
        return True
    return False


if __name__ == '__main__':
    def test_run_gen_mesh_exe():
        geo_fname = 'test.geo'
        run_gen_mesh_exe(geo_fname)

    test_run_gen_mesh_exe() # ok
