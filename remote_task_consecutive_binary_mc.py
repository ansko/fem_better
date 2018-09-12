import json
import os
import shutil
import time

import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint

import paramiko

from fem.create_cluster_inputs import ClusterInputsCreator
from fem.create_fem_input import create_fem_input
from fem.get_fem_main_results import get_fem_main_results
from fem.run_fem_main_ternary_exe import run_fem_main_ternary_exe
from fem.run_gen_mesh_exe import run_gen_mesh_exe
from fem.run_process_mesh_exe import run_process_mesh_exe

from structure.process_structure_log import process_structure_log
from structure.try_make_binary_structure_mc import try_make_binary_structure_mc

from private_settings import ClusterSettingsKiae


class RemoteTaskConsecutiveBinaryMc:
    """
    Task where ar, tau, Lr are fixed while disks number increases

    """
    disk_thickness = 0.1
    vertices_number = 6
    structure_exe = './structure/binary_mc'
    gen_mesh_exe='/home/anton/FEMFolder/gen_mesh.x'
    process_mesh_exe='/home/anton/FEMFolder/processMesh.x'
    fem_main_ternary_exe='/home/anton/FEMFolder/FEManton2.o'
    libs = '/home/anton/FEMFolder/libs'
    my_libs = '/home/anton/FEMFolder/my_libs'
    task_name_template = 'E_'
    cluster_home_dir = '/hfs/head2-hfs2/users/antonsk'
    cluster_main_dir = '/s/ls2/users/antonsk'
    cluster_donor_dir ='FEM_multi_donor'
    completion_delay = 5 # delay after cluster task finish

    libs = [
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
        'materials.txt', 'matrices.txt', 'tensor.cpp', 'tensor.h'
    ]
    remote_geo_fname = '1.geo'

    def __init__(self, local_wd, remote_wd,
            ar, Lr,
            max_attempts,
            moduli,
            results_json,
            geo_dir='geo', files_dir='files'):
        try:
            os.mkdir(local_wd)
            os.mkdir('{0}/{1}'.format(local_wd, geo_dir))
            os.mkdir('{0}/{1}'.format(local_wd, files_dir))
        except FileExistsError:
            pass
        self.local_wd = local_wd
        self.remote_wd = remote_wd
        self.geo_dir = geo_dir
        self.files_dir = files_dir
        self.ar = ar
        self.Lr = Lr
        self.max_attempts = max_attempts
        self.moduli = moduli
        self.results_json = results_json

        # prepare folders on cluster
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(
            ClusterSettingsKiae().host,
            username=ClusterSettingsKiae().user,
            password=ClusterSettingsKiae().pwd,
            key_filename=ClusterSettingsKiae().key
        )
        sftp = self.ssh.open_sftp()
        sftp.chdir(self.cluster_main_dir)
        if self.remote_wd not in sftp.listdir():
            sftp.mkdir(self.remote_wd)
            sftp.mkdir('{0}/libs'.format(self.remote_wd))
        if 'libs' not in sftp.listdir('{0}/{1}'.format(
                self.cluster_main_dir, self.remote_wd)):
            sftp.mkdir('{0}/libs'.format(self.remote_wd))
        for fname in self.required_fnames:
            if fname not in sftp.listdir('{0}/{1}'.format(
                    self.cluster_main_dir, self.remote_wd)):
                cp_fname_command =  'cp {0}/{1}/{2} {0}/{3}/{2}'.format(
                    self.cluster_main_dir, self.cluster_donor_dir, fname,
                    self.remote_wd)
                self.ssh.exec_command(cp_fname_command)
        for lib in self.libs:
            if lib not in sftp.listdir('{0}/{1}/libs'.format(
                    self.cluster_main_dir, self.remote_wd)):
                cp_lib_command = 'cp {0}/{1}/libs/{2} {0}/{3}/libs/{2}'.format(
                    self.cluster_main_dir, self.cluster_donor_dir, lib,
                    self.remote_wd)
                self.ssh.exec_command(cp_lib_command)

    def single_loop(self, disks_number):
        time_tag = str(int(time.time()))
        log_entry = dict()

        # structure
        structure_log_fname = '{0}/{1}/{2}'.format(
            self.local_wd, self.files_dir,
            '{0}_structure_log'.format(time_tag))
        settings_fname = '{0}/{1}/{2}'.format(
            self.local_wd, self.files_dir,
            '{0}_structure_settings'.format(time_tag))
        geo_fname = '{0}/{1}/{2}.geo'.format(
            self.local_wd, self.geo_dir, time_tag)
        stdout_fname =  '{0}/{1}/{2}'.format(
            self.local_wd, self.files_dir,
            '{0}_structure_stdout'.format(time_tag))
        stderr_fname =  '{0}/{1}/{2}'.format(
            self.local_wd, self.files_dir,
            '{0}_structure_stderr'.format(time_tag))
        try_make_binary_structure_mc(
            structure_log_fname, settings_fname, geo_fname,
            self.ar, self.Lr, self.max_attempts,
            disks_number,
            disk_thickness=self.disk_thickness,
            vertices_number=self.vertices_number,
            stdout_exe=stdout_fname, stderr_exe=stderr_fname,
            structure_exe=self.structure_exe)
        structure_data = process_structure_log(structure_log_fname)
        geo_template = '{0}/{1}/{2}_N_{3}_Lr_{4}_ar_{5}.geo'
        new_geo_fname = geo_template.format(self.local_wd, self.geo_dir,
            time_tag, structure_data['N_real'], self.Lr, self.ar)
        shutil.move(geo_fname, new_geo_fname)
        geo_fname = new_geo_fname
        os.remove(stdout_fname)
        os.remove(stderr_fname)
        print('  structure done', time.asctime())

        # cluster, create inputs:
        cic = ClusterInputsCreator(cluster_wd='{0}/{1}'.format(
            self.cluster_main_dir, self.remote_wd))
        fem_gen_sh = '{0}/{1}/fem_gen.sh'.format(
            self.local_wd, self.files_dir, time_tag)
        process_mesh_sh = '{0}/{1}/process_mesh.sh'.format(
            self.local_wd, self.files_dir, time_tag)
        fem_main_sh = {
            'XX': '{0}/{1}/fem_main_XX.sh'.format(
                self.local_wd, self.files_dir, time_tag),
            'YY': '{0}/{1}/fem_main_YY.sh'.format(
                self.local_wd, self.files_dir, time_tag),
            'ZZ': '{0}/{1}/fem_main_ZZ.sh'.format(
                self.local_wd, self.files_dir, time_tag),
        }
        cic.create_fem_gen_sh(fem_gen_sh, params='{0} 0.15 2 2'.format(
            self.remote_geo_fname))
        cic.create_process_mesh_sh(process_mesh_sh)
        fem_input_template_fname = 'input_{0}'
        fem_input_template = '{0}/{1}/{2}_{3}'.format(
            self.local_wd, self.files_dir, time_tag, fem_input_template_fname)
        for axis in ['XX', 'YY', 'ZZ']:
            local_script_fname = fem_input_template.format(axis)
            remote_script_name = 'input_binary_{0}'.format(axis)
            create_fem_input(
                Lx=self.ar/2 * self.disk_thickness * self.Lr,
                moduli=self.moduli,
                input_fname=local_script_fname,
                axis=axis,
                task_name_template=self.task_name_template,
                mesh_fname='mesh.xdr',
                materials_fname='materials.bin')
            cic.create_fem_main_sh(
                sh_name=fem_main_sh[axis],
                axis=axis,
                fem_input_script=remote_script_name,
                fem_main_short_name='FEManton2.o')

        # cluster, copy files
        sftp = self.ssh.open_sftp()
        sftp.put(geo_fname, '{0}/{1}/{2}'.format(
            self.cluster_main_dir, self.remote_wd, self.remote_geo_fname))
        sftp.put(fem_gen_sh, '{0}/fem_gen.sh'.format(self.cluster_home_dir))
        sftp.put(process_mesh_sh, '{0}/fem_process.sh'.format(
            self.cluster_home_dir))
        for axis in ['XX', 'YY', 'ZZ']:
            sftp.put(fem_main_sh[axis], '{0}/fem_main_{1}.sh'.format(
                self.cluster_home_dir, axis))
            sftp.put(
                fem_input_template.format(axis),
                '{0}/{1}/input_binary_{2}'.format(
                    self.cluster_main_dir, self.remote_wd, axis))

        # cluster, set and wait fem_gen
        command = '; '.join([
            'export LD_LIBRARY_PATH=libs',
            'sbatch fem_gen.sh'
        ])
        stdin, stdout, stderr = self.ssh.exec_command(command)
        task_id = stdout.readlines()[0].split()[-1]
        stdin, stdout, stderr = self.ssh.exec_command(
            'squeue --user=antonsk -o "%.10i %.50j %.2t %.10M %.50Z"')
        while True:
            tasks = {
                task_line.split()[0]: {
                    'task_name': task_line.split()[1],
                    'state': task_line.split()[2],
                    'running_time': task_line.split()[3],
                    'wd': task_line.split()[4]
                } for task_line in stdout.readlines()[1:]
            }
            if task_id not in tasks.keys():
                break
            time.sleep(1)
        time.sleep(self.completion_delay) # 'generated.vol' writing
        if 'generated.vol' in sftp.listdir('{0}/{1}'.format(
                self.cluster_main_dir, self.remote_wd)):
            command = 'mv {0}/{1}/generated.vol {0}/{1}/out.mesh'.format(
                self.cluster_main_dir, self.remote_wd)
            self.ssh.exec_command(command)
        else:
            print('gen_mesh failed')
            return False
        self.ssh.exec_command('rm {0}/{1}/{2}.err'.format(
            self.cluster_main_dir, self.remote_wd, task_id))
        self.ssh.exec_command('rm {0}/{1}/{2}.out'.format(
            self.cluster_main_dir, self.remote_wd, task_id))
        self.ssh.exec_command('rm {0}/{1}/generated.vol'.format(
            self.cluster_main_dir, self.remote_wd))
        self.ssh.exec_command('rm {0}/{1}/log_gen_mesh'.format(
            self.cluster_main_dir, self.remote_wd))
        self.ssh.exec_command('rm {0}/{1}/{2}'.format(
            self.cluster_main_dir, self.remote_wd, self.remote_geo_fname))
        print('  fem_gen done', time.asctime())

        # cluster, set and wait processMesh
        command = '; '.join([
            'export LD_LIBRARY_PATH=libs',
            'sbatch fem_process.sh'
        ])
        stdin, stdout, stderr = self.ssh.exec_command(command)
        task_id = stdout.readlines()[0].split()[-1]
        stdin, stdout, stderr = self.ssh.exec_command(
            'squeue --user=antonsk -o "%.10i %.50j %.2t %.10M %.50Z"')
        while True:
            tasks = {
                task_line.split()[0]: {
                    'task_name': task_line.split()[1],
                    'state': task_line.split()[2],
                    'running_time': task_line.split()[3],
                    'wd': task_line.split()[4]
                } for task_line in stdout.readlines()[1:]
            }
            if task_id not in tasks.keys():
                break
            time.sleep(1)
        time.sleep(self.completion_delay) # 'mesh.xdr' writing
        if 'mesh.xdr' in sftp.listdir('{0}/{1}'.format(
                self.cluster_main_dir, self.remote_wd)):
            pass
        else:
            print('process_mesh failed')
            return False
        self.ssh.exec_command('rm {0}/{1}/{2}.err'.format(
            self.cluster_main_dir, self.remote_wd, task_id))
        self.ssh.exec_command('rm {0}/{1}/{2}.out'.format(
            self.cluster_main_dir, self.remote_wd, task_id))
        self.ssh.exec_command('rm {0}/{1}/out.mesh'.format(
            self.cluster_main_dir, self.remote_wd))
        self.ssh.exec_command('rm {0}/{1}/log_process_mesh'.format(
            self.cluster_main_dir, self.remote_wd))
        print('  process_mesh done', time.asctime())
        
        # cluster, set and wait fem_main
        for axis in ['XX', 'YY', 'ZZ']:
            command = '; '.join([
                'export LD_LIBRARY_PATH=libs',
                'sbatch fem_main_{0}.sh'.format(axis)
            ])
            stdin, stdout, stderr = self.ssh.exec_command(command)
            task_id = stdout.readlines()[0].split()[-1]
            stdin, stdout, stderr = self.ssh.exec_command(
                'squeue --user=antonsk -o "%.10i %.50j %.2t %.10M %.50Z"')
            while True:
                tasks = {
                    task_line.split()[0]: {
                        'task_name': task_line.split()[1],
                        'state': task_line.split()[2],
                        'running_time': task_line.split()[3],
                        'wd': task_line.split()[4]
                    } for task_line in stdout.readlines()[1:]
                }
                if task_id not in tasks.keys():
                    break
                time.sleep(1)
            time.sleep(self.completion_delay) # fem_main output writing
            results_fname = '{0}{1}_results.txt'.format(self.task_name_template,
                axis)
            log_fname = '{0}{1}_log.txt'.format(self.task_name_template,
                axis)
            if results_fname in sftp.listdir('{0}/{1}'.format(
                    self.cluster_main_dir, self.remote_wd)):
                sftp.get(
                    '{0}/{1}/{2}'.format(
                        self.cluster_main_dir, self.remote_wd, results_fname),
                    '{0}/{1}/{2}'.format(
                        self.local_wd, self.files_dir, results_fname))
            else:
                print('fem_main along {0} failed'.format(axis))
                return False
            self.ssh.exec_command('rm {0}/{1}/{2}'.format(
                self.cluster_main_dir, self.remote_wd, results_fname))
            self.ssh.exec_command('rm {0}/{1}/{2}'.format(
                self.cluster_main_dir, self.remote_wd, log_fname))
            self.ssh.exec_command('rm {0}/{1}/{2}.err'.format(
                self.cluster_main_dir, self.remote_wd, task_id))
            self.ssh.exec_command('rm {0}/{1}/{2}.out'.format(
                self.cluster_main_dir, self.remote_wd, task_id))
            self.ssh.exec_command('rm {0}/{1}/input_binary_{2}'.format(
                self.cluster_main_dir, self.remote_wd, axis))
            self.ssh.exec_command('rm {0}/{1}/log_fem_main_{2}'.format(
                self.cluster_main_dir, self.remote_wd, axis))
            self.ssh.exec_command('rm {0}/{1}/stresses.txt'.format(
                self.cluster_main_dir, self.remote_wd))

            # log
            fem_data = get_fem_main_results(
                '{0}/{1}/{2}'.format(
                    self.local_wd, self.files_dir, results_fname),
                axis=axis)
            new_results_json_entry = {
                'time_tag': time_tag,
                'ar': self.ar,
                'Lr': self.Lr,
                'N': structure_data['N_real'],
                'axis': axis,
                'fi': fem_data['fi_filler'],
                'E': fem_data['E'],
                'Ef': self.moduli[0],
                'Em': self.moduli[1],
            }

            results_ready = []
            if self.results_json in os.listdir(self.local_wd):
                with open('{0}/{1}'.format(self.local_wd, self.results_json)) as f:
                    try:
                        results_ready = json.load(f)
                    except json.decoder.JSONDecodeError:
                        pass
            results_ready.append(new_results_json_entry)
            with open('{0}/{1}'.format(self.local_wd, self.results_json), 'w') as f:
                json.dump(results_ready, f, indent=4)
            print('  fem main done along', axis, time.asctime())

        # clean remote files
        self.ssh.exec_command('rm {0}/{1}/mesh.xdr'.format(
            self.cluster_main_dir, self.remote_wd))
        self.ssh.exec_command('rm {0}/{1}/materials.bin'.format(
            self.cluster_main_dir, self.remote_wd))

        # clean local files
        os.remove(structure_log_fname)
        os.remove(settings_fname)
        os.remove(fem_gen_sh)
        os.remove(process_mesh_sh)
        os.remove(fem_main_sh['XX'])
        os.remove(fem_main_sh['YY'])
        os.remove(fem_main_sh['ZZ'])
        for axis in ['XX', 'YY', 'ZZ']:
            local_script_fname = fem_input_template.format(axis)
            os.remove(local_script_fname)
            results_fname = '{0}{1}_results.txt'.format(
                self.task_name_template, axis)
            shutil.move(
               '{0}/{1}/{2}'.format(self.local_wd, self.files_dir, results_fname),
               '{0}/{1}/{2}_binary_remote_{3}'.format(
                   self.local_wd, self.files_dir, time_tag, results_fname))
        return True

    def run(self):
        disks_number = 1
        consecutive_fails = 0
        while consecutive_fails < 3:
            code = self.single_loop(disks_number)
            if code:
                print(disks_number, '+')
                disks_number += 1
            else:
                consecutive_fails += 1


if __name__ == '__main__':
    ar = 5
    Lr = 5
    local_wd = 'remote_binary_Lr_{0}_ar_{1}'.format(Lr, ar)
    remote_wd = 'FEM_newdev2_0'
    max_attempts = 100
    moduli = [232, 1.5]
    results_json = 'binary_Lr_{0}_ar_{1}.json'.format(Lr, ar)

    t = RemoteTaskConsecutiveBinaryMc(
        local_wd=local_wd, remote_wd=remote_wd,
        ar=ar, Lr=Lr,
        max_attempts=max_attempts,
        moduli=moduli, results_json=results_json)
    t.run()
