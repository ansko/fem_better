import sys


class APO:
    """
    APO - short name for AllPossibleOptions

    It is an attempt to avoid any hardcode
    """

    """
    structure properties that may be changed, but these are quite ok
    """
    th = 0.1
    vertices_number = 6
    meshing_parameters = [0.15, 2, 2]

    """
    some default values
    """
    # local
    default_fem_dir = '/home/anton/FEMFolder'
    default_structure_exe_dir = '/home/anton/AspALL/Projects/NEW_DEV'
    # remote
    sbatch_changing_options = {
        '-n': {
            'gen_mesh': 1,
            'process_mesh': 1,
            'fem_main': 1
        },
        '--cpus-per-task': {
            'gen_mesh': 8,
            'process_mesh': 8,
            'fem_main': 8
        },
        '-t': {
            'gen_mesh': '0:59:59',
            'process_mesh': '0:59:59',
            'fem_main': '2:59:59'
        }
    }
    sbatch_constant_options = {
        '-o': '%j.out',
        '-e': '%j.err',
        '-p': 'hpc2-16g-3d',
    }
    cluster_main_dir = '/s/ls2/users/antonsk'
    cluster_home_dir = '/home/users/antonsk'
    default_gen_mesh_sh = 'gen_mesh.sh'
    default_gen_mesh_log = 'gen_mesh.log'
    default_process_mesh_sh = 'process_mesh.sh'
    default_process_mesh_log = 'process_mesh.log'
    default_fem_main_sh_template = 'fem_main_{0}' # axis
    default_fem_main_log_template = 'fem_main_{0}.log' # axis
    default_remote_geo_fname = 'remote.geo'
    default_completion_delay = 150

    """
    executable file names without full path
    """
    all_structure_exe_names = {
        'LocalTaskConsecutiveBinaryMc': '{0}/binary_mc'.format(
            default_structure_exe_dir),
        'RemoteTaskConsecutiveBinaryMc': '{0}/binary_mc'.format(
            default_structure_exe_dir),
        'LocalTaskConsecutiveTernaryMc': '{0}/ternary_mc'.format(
            default_structure_exe_dir),
        'RemoteTaskConsecutiveTernaryMc': '{0}/ternary_mc'.format(
            default_structure_exe_dir)
    }
    gen_mesh_exe_fname = 'gen_mesh.x'
    process_mesh_exe_fname = 'processMesh.x'
    all_fem_main_exes = {
        'binary': 'FEManton2.o',
        'ternary': 'FEManton3.o'
    }

    """
    realy hardcoded values
    instead of changing them everywhere, change only here
    """
    libs = 'libs'
    my_libs = 'my_libs'
    geo_subdirectory = 'geo'
    other_files_subdirectory = 'files'
    gen_mesh_generated_mesh = 'generated.vol'
    process_mesh_input_mesh = 'out.mesh'
    process_mesh_generated_mesh = 'mesh.xdr'
    proces_mesh_generated_materials = 'materials.bin'
    gen_mesh_success = [0]
    process_mesh_success = [0, 2]
    fem_main_success = [0]
    process_mesh_memory_limit = 0.3 * 8 * 1024**3 # 30% of my 8GB RAM
    libs_names = [
        'libnglib.la', 'libmesh.la', 'libmesh.so.0.0.0', 'libocc.so.0',
        'libslepc.so', 'libcsg.so', 'libmesh_dbg.so.0.0.0', 'libocc.so.0.0.0',
        'libgeom2d.so.0.0.0', 'libinterface.so.0.0.0', 'libstl.so', 'libocc.so',
        'libcsg.so.0.0.0', 'libpetsc.so.3.7', 'libslepc.so.3.7.3',
        'libmesh_devel.so.0.0.0', 'libinterface.la', 'libnetcdf.so.7.2.0',
        'libnetcdf.so.7', 'libcsg.so.0', 'libocc.la', 'libnglib.so',
        'libmesh_opt.so.0.0.0', 'libpetsc.so', 'libstl.so.0.0.0', 'libnetcdf.so',
        'libmesh_dbg.so.0', 'libgeom2d.so.0', 'libinterface.so', 'libmesh_opt.so',
        'libinterface.so.0', 'libslepc.so.3.7', 'libpetsc.so.3.7.5',
        'libmesh_dbg.so', 'libmesh_opt.so.0', 'libmesh.so', 'libmesh_devel.so',
        'libstl.la', 'libstl.so.0', 'libmesh.so.0', 'libgeom2d.so',
        'libgeom2d.la', 'libcsg.la', 'libmesh_devel.so.0'
    ]
    required_fnames = [
        'gen_mesh.x', 'processMesh.x', 'FEManton3.o', 'FEManton2.o',
        'materials.txt', 'matrices.txt',
    ]
    cluster_donor_dir = 'FEM_multi_donor'


    """
    templates for full names of files and directories
    """
    all_local_wd_templates = {
        'binary': 'binary_Lr_{0}_ar_{1}', # Lr, ar
        'ternary': 'ternary_Lr_{0}_ar_{1}_tau_2' # Lr, ar, tau
    }
    all_structure_log_templates = {
        'binary': '{0}/{1}_binary_structure_log', # files_subdir, tag
        'ternary': '{0}/{1}_ternary_structure_log' # files_subdir, tag
    }
    all_structure_settings_templates = {
        'binary': '{0}/{1}_binary_structure_settings', # files_subdir, tag
        'ternary': '{0}/{1}_ternary_structure_settings' # files_subdir, tag
    }
    # file where CSG result of structure exe will be stored
    all_structure_geo_fname_tempaltes = {
        'binary': '{0}/{1}_binary.geo', # local_wd, tag
        'ternary': '{0}/{1}_ternary.geo', # local_wd, tag
    }
    all_structure_stdout_templates = {
        'binary': '{0}/{1}_binary_structure_stdout', # files_subdir, tag
        'ternary': '{0}/{1}_ternary_structure_stdout', # files_subdir, tag
    }
    all_structure_stderr_templates = {
        'binary': '{0}_binary_structure_stderr',
        'ternary': '{0}_ternary_structure_stderr',
    }
    # new name for output of structure exe
    # that depends on the structure properties
    all_structure_new_geo_fname_tempaltes = {
        'binary': '{0}/{1}_N_{2}_Lr_{3}_ar_{4}.geo', # files subdir, tag, N
                                                     # Lr, ar
        'ternary': '{0}/{1}_N_{2}_Lr_{3}_ar_{4}_tau_{5}.geo' # files subdir,
                                                     # tag, N, Lr, ar, tau
    }
    fem_gen_stdout_template = '{0}/{1}_fem_gen_stdout' # files_subdir, tag
    fem_gen_stderr_template = '{0}/{1}_fem_gen_stderr' # files_subdir, tag
    process_mesh_stdout_template = '{0}/{1}_process_mesh_stdout' # files_subdir,
                                                                 # tag
    process_mesh_stderr_template = '{0}/{1}_process_mesh_stderr' # files_subdir,
                                                                 # tag
    all_fem_main_input_templates = {
        'binary': '{0}/{1}_binary_fem_main_input_{2}', # files_subdir, tag, axis
        'ternary': '{0}/{1}_ternary_fem_main_input_{2}' # files_subdir, tag, axis
    }
    all_fem_main_stdout_templates = {
        'binary': '{0}/{1}_binary_fem_main_stdout_{2}', # files_subdir, tag, axis
        'ternary': '{0}/{1}_binary_fem_main_stdout_{2}', # files_subdir, tag, axis
    }
    all_fem_main_stderr_templates = {
        'binary': '{0}/{1}_binary_fem_main_stderr_{2}', # files_subdir, tag, axis
        'ternary': '{0}/{1}_binary_fem_main_stderr_{2}', # files_subdir, tag, axis
    }
    # these 2 must correspond to each other
    # !!!
    all_fem_main_results_templates = {
        'binary': '{0}/{1}_binary_E_{2}_results.txt', # files_subdir, tag, axis
        'ternary': '{0}/{1}_binary_E_{2}_results.txt', # files_subdir, tag, axis
    }
    all_fem_main_local_task_name_templates = {
        'binary': '{0}/{1}_binary_E_{2}', # files_subdir, tag, axis
        'ternary': '{0}/{1}_binary_E_{2}', # files_subdir, tag, axis
    }
    all_fem_main_remote_task_name_templates = {
        'binary': '{0}_binary_E_{1}', # tag, axis
        'ternary': '{0}_binary_E_{1}', # tag, axis
    }
    all_fem_main_remote_input_templates = {
        'binary': '{0}_binary_E_{1}', # tag, axis
        'ternary': '{0}_binary_E_{1}', # tag, axis
    }
    # !!!

    def __init__(self, task_name, **kwargs):

        # looking for provided parameters
        try:
            self.fem_dir = kwargs['fem_dir']
        except KeyError:
            self.fem_dir = self.default_fem_dir
        try:
            local_wd = kwargs['local_wd']
        except:
            local_wd = '.'


        self.structure_exe = self.all_structure_exe_names[task_name]

        task_name_lower = task_name.lower()
        if 'local' in task_name_lower:
            place = 'local'
        elif 'remote' in task_name_lower:
            place = 'remote'
        else:
            print('unknown task type (nor local or remote):', task_name)
            sys.exit()

        if 'binary' in task_name_lower:
            structure = 'binary'
        elif 'ternary' in task_name_lower:
            structure = 'ternary'
        else:
            print('unknown task type (nor binary or ternary):', task_name)

        # executables
        self.gen_mesh_exe = '{0}/{1}'.format(self.fem_dir, self.gen_mesh_exe_fname)
        self.process_mesh_exe = '{0}/{1}'.format(
            self.fem_dir, self.process_mesh_exe_fname)
        fem_main_exe_fname = self.all_fem_main_exes[structure]
        self.fem_main_exe = '{0}/{1}'.format(self.fem_dir, fem_main_exe_fname)
        self.fem_main_exe_fname = fem_main_exe_fname

        # structure templates
        self.structure_log_template = self.all_structure_log_templates[structure]
        self.structure_settings_template = (
            self.all_structure_settings_templates[structure])
        self.structure_geo_fname_template = (
            self.all_structure_geo_fname_tempaltes[structure])
        self.structure_stdout_template = (
            self.all_structure_stdout_templates[structure])
        self.structure_stderr_template = (
            self.all_structure_stderr_templates[structure])
        self.structure_new_geo_fname_template = (
            self.all_structure_new_geo_fname_tempaltes[structure])
        self.fem_main_input_template = (
            self.all_fem_main_input_templates[structure])
        self.fem_main_stdout_template = (
            self.all_fem_main_stdout_templates[structure])
        self.fem_main_stderr_template = (
            self.all_fem_main_stderr_templates[structure])
        self.fem_main_results_template = (
            self.all_fem_main_results_templates[structure])
        self.fem_main_remote_task_name_template = (
            self.all_fem_main_remote_task_name_templates[structure])
        self.fem_main_local_task_name_template = (
            self.all_fem_main_local_task_name_templates[structure])
        self.fem_main_remote_input_template = (
            self.all_fem_main_remote_input_templates[structure])

        print('Options set successfully:')
        print('  structure exe name ==', self.structure_exe)
        print('  fem_main exe name ==', self.fem_main_exe)
