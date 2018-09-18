import json
import os
import paramiko
import shutil
import time

import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint

from all_possible_options import APO
from fem.create_cluster_inputs import ClusterInputsCreator
from fem.create_fem_input import create_fem_input
from fem.get_fem_main_results import get_fem_main_results
from structure.process_structure_log import process_structure_log
from structure.try_make_binary_structure_mc import try_make_binary_structure_mc
from try_remove_files import try_remove_files

from private_settings import ClusterSettingsKiae


import sys

class RemoteTaskConsecutiveBinaryMc:
    """
    Remote binary task where ar, Lr are fixed while disks number increases

    """

    def __init__(self,
            local_wd, remote_wd,
            ar, Lr, max_attempts,
            moduli,
            results_json,
            geo_subdir='geo', files_subdir='files'):

        self.local_wd = local_wd
        self.remote_wd = remote_wd
        self.geo_subdir = geo_subdir
        self.files_subdir = files_subdir
        self.ar = ar
        self.Lr = Lr
        self.max_attempts = max_attempts
        self.moduli = moduli
        self.results_json = results_json

        a = APO(type(self).__name__, local_wd=local_wd)

        self.disk_thickness = a.th
        self.vertices_number = a.vertices_number
        self.structure_exe = a.structure_exe
        self.structure_log_template = a.structure_log_template
        self.structure_settings_template = a.structure_settings_template
        self.structure_geo_fname_template = a.structure_geo_fname_template
        self.structure_stdout_template = a.structure_stdout_template
        self.structure_stderr_template = a.structure_stderr_template
        self.structure_new_geo_fname_template = a.structure_new_geo_fname_template
        self.remote_geo_fname = a.default_remote_geo_fname
        self.libs = a.libs
        self.gen_mesh_sh = a.default_gen_mesh_sh
        self.gen_mesh_log = a.default_gen_mesh_log
        self.gen_mesh_exe = a.gen_mesh_exe_fname
        self.gen_mesh_generated_mesh = a.gen_mesh_generated_mesh
        self.meshing_parameters = a.meshing_parameters
        self.process_mesh_sh = a.default_process_mesh_sh
        self.process_mesh_log = a.default_process_mesh_log
        self.process_mesh_exe = a.process_mesh_exe_fname
        self.process_mesh_input_mesh = a.process_mesh_input_mesh
        self.process_mesh_generated_mesh = a.process_mesh_generated_mesh
        self.process_mesh_generated_materials = a.proces_mesh_generated_materials
        self.fem_main_input_template = a.fem_main_input_template
        self.fem_main_sh_template = a.default_fem_main_sh_template
        self.fem_main_log_template = a.default_fem_main_log_template
        self.fem_main_exe = a.fem_main_exe_fname
        self.fem_main_local_input_template = a.fem_main_input_template
        self.fem_main_remote_input_template = a.fem_main_remote_input_template
        self.fem_main_results_template = a.fem_main_results_template
        self.fem_main_task_name_template = a.fem_main_remote_task_name_template
        self.completion_delay = 10#a.default_completion_delay
        self.cluster_home_dir = a.cluster_home_dir

        try:
            os.mkdir(local_wd)
        except FileExistsError:
            pass
        try:
            os.mkdir('{0}/{1}'.format(local_wd, geo_subdir))
        except FileExistsError:
            pass
        try:
            os.mkdir('{0}/{1}'.format(local_wd, files_subdir))
        except FileExistsError:
            pass

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
        self.cluster_main_dir = a.cluster_main_dir
        sftp.chdir(self.cluster_main_dir)
        if self.remote_wd not in sftp.listdir():
            sftp.mkdir(self.remote_wd)
        if  self.libs not in sftp.listdir('{0}/{1}'.format(
                self.cluster_main_dir, self.remote_wd)):
            sftp.mkdir('{0}/{1}'.format(self.remote_wd, self.libs))
        for fname in a.required_fnames:
            if fname not in sftp.listdir('{0}/{1}'.format(
                    self.cluster_main_dir, self.remote_wd)):
                cp_fname_command =  'cp {0}/{1}/{2} {0}/{3}/{2}'.format(
                    self.cluster_main_dir, self.cluster_donor_dir, fname,
                    self.remote_wd)
                self.ssh.exec_command(cp_fname_command)
        for lib in self.libs:
            if lib not in sftp.listdir('{0}/{1}/{2}'.format(
                    self.cluster_main_dir, self.remote_wd, self.libs)):
                cp_lib_command = 'cp {0}/{1}/{4}/{2} {0}/{3}/{4}/{2}'.format(
                    self.cluster_main_dir, a.cluster_donor_dir, lib,
                    self.remote_wd, self.libs)
                self.ssh.exec_command(cp_lib_command)

        # preapre sh options
        full_cluster_wd = '{0}/{1}'.format(self.cluster_main_dir, self.remote_wd)
        self.gen_mesh_options = a.sbatch_constant_options
        self.process_mesh_options = a.sbatch_constant_options
        self.fem_main_options = a.sbatch_constant_options
        for key in ('-n', '--cpus-per-task', '-t'):
            self.gen_mesh_options[key] = a.sbatch_changing_options[key]['gen_mesh']
            self.process_mesh_options[key] = (
                a.sbatch_changing_options[key]['gen_mesh'])
            self.fem_main_options[key] = (
                a.sbatch_changing_options[key]['fem_main'])
        self.gen_mesh_options['-D'] = full_cluster_wd
        self.process_mesh_options['-D'] = full_cluster_wd
        self.fem_main_options['-D'] = full_cluster_wd

    def single_loop(self, N):
        time_tag = str(int(time.time()))
        log_entry = dict()
        files_subdir = '{0}/{1}'.format(self.local_wd, self.files_subdir)
        geo_subdir = '{0}/{1}'.format(self.local_wd, self.geo_subdir)

        # structure
        structure_log = self.structure_log_template.format(files_subdir, time_tag)
        structure_settings = self.structure_settings_template.format(
            files_subdir, time_tag)
        geo_fname = self.structure_geo_fname_template.format(geo_subdir, time_tag)
        structure_stdout =  self.structure_stdout_template.format(
            files_subdir, time_tag)
        structure_stderr = self.structure_stderr_template.format(
            files_subdir, time_tag)
        if not try_make_binary_structure_mc(
                structure_log, structure_settings, geo_fname,
                self.ar, self.Lr, self.max_attempts, N,
                self.disk_thickness, self.vertices_number, self.structure_exe,
                stdout=structure_stdout, stderr=structure_stderr):
            print('  failed to create structure')
            try_remove_files(structure_log, structure_settings,
                structure_stdout, structure_stderr, geo_fname)
            return False
        structure_data = process_structure_log(structure_log)
        new_geo_fname = self.structure_new_geo_fname_template.format(
            geo_subdir, time_tag, structure_data['N_real'], self.Lr, self.ar)
        shutil.move(geo_fname, new_geo_fname)
        try_remove_files(structure_log, structure_settings,
                structure_stdout, structure_stderr)
        geo_fname = new_geo_fname
        del new_geo_fname
        del structure_log
        del structure_settings
        del structure_stdout
        del structure_stderr
        print('  structure done', time.asctime())

        # cluster, create inputs:
        full_cluster_wd = '{0}/{1}'.format(self.cluster_main_dir, self.remote_wd)
        cic = ClusterInputsCreator(
            cluster_wd='{0}/{1}/{2}'.format(
                self.cluster_main_dir, self.files_subdir, self.remote_wd),
            structure='binary')
        gen_mesh_local_sh = '{0}/{1}/{2}'.format(
            self.local_wd,  self.files_subdir, self.gen_mesh_sh)
        gen_mesh_remote_sh = '{0}/{1}'.format(
            self.cluster_home_dir, self.gen_mesh_sh)
        process_mesh_local_sh = '{0}/{1}/{2}'.format(
            self.local_wd,  self.files_subdir, self.process_mesh_sh)
        process_mesh_remote_sh = '{0}/{1}'.format(
            self.cluster_home_dir, self.process_mesh_sh)
        fem_main_local_shs = {
            axis: '{0}/{1}/{2}'.format(
                self.local_wd, self.files_subdir,
                self.fem_main_sh_template.format(axis))
            for axis in ['XX', 'YY', 'ZZ']
        }
        fem_main_remote_shs = {
            axis: '{0}/{1}'.format(
                self.cluster_home_dir, self.fem_main_sh_template.format(axis))
            for axis in ['XX', 'YY', 'ZZ']
        }
        fem_main_local_inputs = {
            axis: self.fem_main_local_input_template.format(
                files_subdir, time_tag, axis)
            for axis in ['XX', 'YY', 'ZZ']
        }
        fem_main_remote_inputs = {
            axis: self.fem_main_remote_input_template.format(time_tag, axis)
            for axis in ['XX', 'YY', 'ZZ']
        }
        fem_main_task_names = {
            axis: self.fem_main_task_name_template.format(time_tag, axis)
            for axis in ['XX', 'YY', 'ZZ']
        }
        fem_main_results_names = {
            axis: '{0}_results.txt'.format(
                self.fem_main_task_name_template.format(time_tag, axis))
            for axis in ['XX', 'YY', 'ZZ']
        }
        fem_main_log_names = {
            axis: '{0}_log.txt'.format(
                self.fem_main_task_name_template.format(time_tag, axis))
            for axis in ['XX', 'YY', 'ZZ']
        }
        fem_main_local_results_names = {
            axis: '{0}/{1}_results_{2}.txt'.format(files_subdir, time_tag, axis)
            for axis in ['XX', 'YY', 'ZZ']
        }

        # gen_mesh
        cic.create_sh(
            local_sh=gen_mesh_local_sh,
            log=self.gen_mesh_log,
            exe=self.gen_mesh_exe,
            argv=[self.remote_geo_fname, *self.meshing_parameters],
            sbatch_options=self.gen_mesh_options)

        # process_mesh
        cic.create_sh(
            local_sh=process_mesh_local_sh,
            log=self.process_mesh_log,
            exe=self.process_mesh_exe,
            argv=[],
            sbatch_options=self.process_mesh_options)

        # fem_main
        for axis in ['XX', 'YY', 'ZZ']:
            cic.create_sh(
                local_sh=fem_main_local_shs[axis],
                log=fem_main_log_names[axis],
                exe=self.fem_main_exe,
                argv=[fem_main_remote_inputs[axis]],
                sbatch_options=self.fem_main_options)
            create_fem_input(
                Lx=self.ar/2 * self.disk_thickness * self.Lr,
                moduli=self.moduli,
                input_fname=fem_main_local_inputs[axis],
                axis=axis,
                task_name=fem_main_task_names[axis],
                mesh_fname=self.process_mesh_generated_mesh,
                materials_fname=self.process_mesh_generated_materials)

        # fem, copy local files to cluster
        sftp = self.ssh.open_sftp()
        sftp.chdir(full_cluster_wd)
        sftp.put(geo_fname, self.remote_geo_fname)
        sftp.put(gen_mesh_local_sh, gen_mesh_remote_sh)
        sftp.put(process_mesh_local_sh, process_mesh_remote_sh)
        for axis in ['XX', 'YY', 'ZZ']:
            sftp.put(fem_main_local_shs[axis], fem_main_remote_shs[axis])
            sftp.put(fem_main_local_inputs[axis], fem_main_remote_inputs[axis])

        # fem, set and wait gen_mesh on cluster
        export_command = 'export LD_LIBRARY_PATH={0};'.format(self.libs)
        squeue_command = 'squeue --user=antonsk -o "%.10i %.50j %.2t %.10M %.50Z"'
        mv_command = 'mv {0}/{1} {0}/{2}'.format(
            full_cluster_wd,
            self.gen_mesh_generated_mesh,
            self.process_mesh_input_mesh)
        gen_mesh_command = ' '.join([
            export_command,
            'sbatch', gen_mesh_remote_sh])
        stdin, stdout, stderr = self.ssh.exec_command(gen_mesh_command)
        try:
            task_id = stdout.readlines()[0].split()[-1]
            print('  gen_mesh id', task_id)
        except IndexError:
            print('  gen_mesh failed to start')
            return False
        while True:
            stdin, stdout, stderr = self.ssh.exec_command(squeue_command)
            try:
                tasks = {
                    task_line.split()[0]: {
                        'task_name': task_line.split()[1],
                        'state': task_line.split()[2],
                        'running_time': task_line.split()[3],
                        'wd': task_line.split()[4]
                    } for task_line in stdout.readlines()[1:]
                }
            except IndexError:
                print('  {0} failed to start'.format(current_sh))
                return False
            if task_id not in tasks.keys():
                break
            time.sleep(1)
        time.sleep(self.completion_delay) # 'generated.vol' writing
        sftp.remove('{0}.err'.format(task_id))
        sftp.remove('{0}.out'.format(task_id))
        sftp.remove(self.gen_mesh_log)
        sftp.remove(self.remote_geo_fname)
        if self.gen_mesh_generated_mesh in sftp.listdir():
            self.ssh.exec_command(mv_command)
        else:
            print('gen_mesh failed')
            return False
        print('  fem_gen done', time.asctime())

        # fem, set and wait processMesh on cluster
        process_mesh_command = ' '.join([
            export_command, 'sbatch', process_mesh_remote_sh])
        stdin, stdout, stderr = self.ssh.exec_command(process_mesh_command)
        try:
            task_id = stdout.readlines()[0].split()[-1]
        except IndexError:
            print('  process_mesh failed to start')
            return False
        while True:
            stdin, stdout, stderr = self.ssh.exec_command(squeue_command)
            try:
                tasks = {
                    task_line.split()[0]: {
                        'task_name': task_line.split()[1],
                        'state': task_line.split()[2],
                        'running_time': task_line.split()[3],
                        'wd': task_line.split()[4]
                    } for task_line in stdout.readlines()[1:]
                 }
            except IndexError:
                print('  process_mesh.sh failed to start')
                return False
            if task_id not in tasks.keys():
                break
            time.sleep(1)
        time.sleep(self.completion_delay) # 'mesh.xdr' writing
        sftp.remove('{0}.err'.format(task_id))
        sftp.remove('{0}.out'.format(task_id))
        sftp.remove(self.process_mesh_log)
        if self.process_mesh_input_mesh in sftp.listdir():
            sftp.remove(self.process_mesh_input_mesh)
        else:
            print('process_mesh failed')
            return False
        print('  process_mesh done', time.asctime())
        
        for axis in ['XX', 'YY', 'ZZ']:
            # fem, set and wait fem_main on cluster
            fem_main_command = ' '.join([
                export_command, 'sbatch', fem_main_remote_shs[axis]])
            stdin, stdout, stderr = self.ssh.exec_command(fem_main_command)
            try:
                task_id = stdout.readlines()[0].split()[-1]
            except IndexError:
                print('  fem_main failed to start')
                return False
            while True:
                stdin, stdout, stderr = self.ssh.exec_command(squeue_command)
                try:
                    tasks = {
                        task_line.split()[0]: {
                            'task_name': task_line.split()[1],
                            'state': task_line.split()[2],
                            'running_time': task_line.split()[3],
                            'wd': task_line.split()[4]
                        } for task_line in stdout.readlines()[1:]
                    }
                except IndexError:
                    print('  fem_main.sh failed to start')
                    return False
                if task_id not in tasks.keys():
                    break
                time.sleep(1)
            time.sleep(self.completion_delay) # fem_main output writing

            sftp.remove(fem_main_log_names[axis])
            sftp.remove('{0}.out'.format(task_id))
            sftp.remove('{0}.err'.format(task_id))
            sftp.remove(fem_main_remote_inputs[axis])
            sftp.remove('stresses.txt')
            if fem_main_results_names[axis] in sftp.listdir():
                sftp.get(
                    fem_main_results_names[axis],
                    fem_main_local_results_names[axis])
                sftp.remove(fem_main_results_names[axis])
            else:
                print('fem_main along {0} failed'.format(axis))
                return False

            # logging
            fem_data = get_fem_main_results(
                fem_main_local_results_names[axis],
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
            json_name = '{0}/{1}'.format(self.local_wd, self.results_json)
            if self.results_json in os.listdir(self.local_wd):
                with open(json_name) as f:
                    try:
                        results_ready = json.load(f)
                    except json.decoder.JSONDecodeError:
                        pass
            results_ready.append(new_results_json_entry)
            with open(json_name, 'w') as f:
                json.dump(results_ready, f, indent=4)
            print('  fem main done along', axis, time.asctime())
        # clean remote directory
        sftp.remove(self.process_mesh_generated_mesh)
        sftp.remove(self.process_mesh_generated_materials)
        # clean local directory
        os.remove(gen_mesh_local_sh)
        os.remove(process_mesh_local_sh)
        for axis in ['XX', 'YY', 'ZZ']:
            os.remove(fem_main_local_shs[axis])
            os.remove(fem_main_local_inputs[axis])
        return True

    def run(self):
        N = 1
        consecutive_fails = 0
        print('\nstart looping')
        while consecutive_fails < 3:
            print('trying', N, 'disks')
            code = self.single_loop(N)
            if code:
                print('+')
                N += 1
                consecutive_fails = 0
            else:
                print('-')
                consecutive_fails += 1
            break

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
