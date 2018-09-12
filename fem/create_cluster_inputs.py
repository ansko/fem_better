class ClusterInputsCreator:
    shebang_line = '#!/bin/sh\n'
    source_line = '. /usr/share/Modules/init/sh\n'
    modules_line = 'module load mpi intel-compilers gcc49\n'
    runner_line_template = '$MPIRUN {0} {1} | tee {2}' # exe, argv, log

    def __init__(self, cluster_wd):
        self.cluster_wd = cluster_wd
        self.sbatch_changing_options = {
            '-n': {
                'fem_gen': 1,
                'process_mesh': 1,
                'fem_main': 1
            },
            '--cpus-per-task': {
                'fem_gen': 8,
                'process_mesh': 8,
                'fem_main': 8
            },
            '-t': {
                'fem_gen': '0:59:59',
                'process_mesh': '0:59:59',
                'fem_main': '2:59:59'
            }
        }
        self.sbatch_constant_options = {
            '-D': self.cluster_wd,
            '-o': '%j.out',
            '-e': '%j.err',
            '-p': 'hpc2-16g-3d',
        }

    def create_fem_gen_sh(self, sh_name, params='0.15 2 2'):
        full_exe_name = '{0}/gen_mesh.x'.format(self.cluster_wd)
        log_name = '{0}/log_{1}'.format(self.cluster_wd, 'gen_mesh')
        with open(sh_name, 'w') as f:
            f.write(self.shebang_line)
            #for key in self.sbatch_constant_options.keys():
            for key in ['-D', '-o', '-e', '-p']:
                f.write('#SBATCH {0} {1}\n'.format(
                    key, self.sbatch_constant_options[key]))
            for key in self.sbatch_changing_options.keys():
                f.write('#SBATCH {0} {1}\n'.format(
                    key, self.sbatch_changing_options[key]['fem_gen']))
            f.write(self.source_line)
            f.write(self.modules_line)
            f.write(self.runner_line_template.format(
                full_exe_name, params, log_name))

    def create_process_mesh_sh(self, sh_name):
        full_exe_name = '{0}/processMesh.x'.format(self.cluster_wd)
        log_name = '{0}/log_{1}'.format(self.cluster_wd, 'process_mesh')
        with open(sh_name, 'w') as f:
            f.write(self.shebang_line)
            #for key in self.sbatch_constant_options.keys():
            for key in ['-D', '-o', '-e', '-p']:
                f.write('#SBATCH  {0} {1}\n'.format(
                    key, self.sbatch_constant_options[key]))
            for key in self.sbatch_changing_options.keys():
                f.write('#SBATCH {0} {1}\n'.format(
                    key, self.sbatch_changing_options[key]['process_mesh']))
            f.write(self.source_line)
            f.write(self.modules_line)
            f.write(self.runner_line_template.format(full_exe_name, '', log_name))

    def create_fem_main_sh(self, sh_name, axis, fem_input_script,
            fem_main_short_name):
        full_exe_name = '{0}/{1}'.format(self.cluster_wd, fem_main_short_name)
        log_name = '{0}/log_{1}_{2}'.format(self.cluster_wd, 'fem_main', axis)
        with open(sh_name, 'w') as f:
            f.write(self.shebang_line)
            #for key in self.sbatch_constant_options.keys():
            for key in ['-D', '-o', '-e', '-p']:
                f.write('#SBATCH {0} {1}\n'.format(
                    key, self.sbatch_constant_options[key]))
            for key in self.sbatch_changing_options.keys():
                f.write('#SBATCH {0} {1}\n'.format(
                    key, self.sbatch_changing_options[key]['fem_main']))
            f.write(self.source_line)
            f.write(self.modules_line)
            f.write(self.runner_line_template.format(
                full_exe_name, fem_input_script, log_name))

if __name__ == '__main__':
    cluster_inputer = ClusterInputsCreator(cluster_wd='cluster_wd_000', N=1)
    cluster_inputer.create_fem_gen_sh(sh_name='fem_gen.sh', params='0.15 2 2')
    cluster_inputer.create_process_mesh_sh(sh_name='process_mesh.sh')
    for axis in ['XX', 'YY', 'ZZ']:
        cluster_inputer.create_fem_main_sh(
            sh_name='fem_main_{0}.sh'.format(axis),
            axis=axis,
            fem_input_script='input_{0}'.format(axis),
            fem_main_short_name='fem_main_2')
