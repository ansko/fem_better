class ClusterInputsCreator:
    shebang_line = '#!/bin/sh\n'
    source_line = '. /usr/share/Modules/init/sh\n'
    modules_line = 'module load mpi intel-compilers gcc49\n'

    def __init__(self, cluster_wd, structure):
        """
        Structure: 'binary' / 'ternary'
        Options: {
            '-n': ..., '-t': ..., '-D': ..., '-o': ..., '-e': ..., '-p': ...,
            '--cpus-per-task': ...
        }
        """
        self.cluster_wd = cluster_wd
        self.structure = structure

    def create_sh(self, local_sh, log, exe, argv, sbatch_options):
        """
        Creates a file local_sh with specified parameters. This file may be
        transfered into cluster and used after that as sbath task script.
        """
        try:
            with open(local_sh, 'w') as f:
                f.write(self.shebang_line)
                for k, v in sbatch_options.items():
                    f.write('#SBATCH {0} {1}\n'.format(k, v))
                argv = [str(arg) for arg in argv]
                f.write(self.source_line)
                f.write(self.modules_line)
                f.write(' '.join(['$MPIRUN', exe, *argv, '|', 'tee', log]))
                return True
        except KeyError:
            return False
