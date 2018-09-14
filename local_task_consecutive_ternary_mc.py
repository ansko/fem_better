import json
import os
import resource
import shutil
import subprocess
import time

import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint

from all_possible_options import APO
from fem.create_fem_input import create_fem_input
from fem.get_fem_main_results import get_fem_main_results
from structure.process_structure_log import process_structure_log
from structure.try_make_ternary_structure_mc import try_make_ternary_structure_mc
from try_remove_files import try_remove_files


class LocalTaskConsecutiveTernaryMc:
    """
    Ternary task where ar, tau, Lr are fixed while disks number increases

    """

    def __init__(self,
            local_wd,
            ar, tau, Lr, max_attempts,
            moduli,
            results_json, # full name is local_wd/results_json
            geo_subdir='geo', files_subdir='files'):

        self.local_wd = local_wd
        self.geo_subdir = geo_subdir
        self.files_subdir = files_subdir
        self.ar = ar
        self.Lr = Lr
        self.tau = tau
        self.max_attempts = max_attempts
        self.moduli = moduli
        self.results_json = results_json

        a = APO(type(self).__name__, local_wd=local_wd)

        self.disk_thickness = a.th
        self.vertices_number = a.vertices_number
        self.structure_exe = a.structure_exe
        self.gen_mesh_exe= a.gen_mesh_exe
        self.process_mesh_exe = a.process_mesh_exe
        self.fem_main_exe = a.fem_main_exe
        self.structure_log_template = a.structure_log_template
        self.structure_settings_template = a.structure_settings_template
        self.structure_geo_fname_template = a.structure_geo_fname_template
        self.structure_stdout_template = a.structure_stdout_template
        self.structure_stderr_template = a.structure_stderr_template
        self.structure_new_geo_fname_template = a.structure_new_geo_fname_template
        self.fem_dir = a.fem_dir
        self.libs = a.libs
        self.my_libs = a.my_libs
        self.meshing_parameters = a.meshing_parameters
        self.fem_gen_stdout_template = a.fem_gen_stdout_template
        self.fem_gen_stderr_template = a.fem_gen_stderr_template
        self.gen_mesh_success = a.gen_mesh_success
        self.gen_mesh_generated_mesh = a.gen_mesh_generated_mesh
        self.process_mesh_input_mesh = a.process_mesh_input_mesh
        self.process_mesh_stdout_template = a.process_mesh_stdout_template
        self.process_mesh_stderr_template = a.process_mesh_stderr_template
        self.process_mesh_memory_limit = a.process_mesh_memory_limit
        self.process_mesh_success = a.process_mesh_success
        self.process_mesh_generated_mesh = a.process_mesh_generated_mesh
        self.proces_mesh_generated_materials = a.proces_mesh_generated_materials
        self.fem_main_input_template = a.fem_main_input_template
        self.fem_main_stderr_template = a.fem_main_stderr_template
        self.fem_main_stdout_template = a.fem_main_stdout_template
        self.fem_main_results_template = a.fem_main_results_template
        self.fem_main_task_name_template = a.fem_main_local_task_name_template
        self.fem_main_success = a.fem_main_success

        # create folder structure
        try:
            os.mkdir(local_wd)
        except FileExistsError:
            pass
        try:
            os.mkdir('{0}/{1}'.format(local_wd, files_subdir))
        except FileExistsError:
            pass
        try:
            os.mkdir('{0}/{1}'.format(local_wd, geo_subdir))
        except FileExistsError:
            pass
        self.local_wd = '{0}/{1}'.format(os.getcwd(), self.local_wd)


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
        if not try_make_ternary_structure_mc(
                structure_log, structure_settings, geo_fname,
                self.ar, self.tau, self.Lr, self.max_attempts, N,
                self.disk_thickness, self.vertices_number, self.structure_exe,
                stdout=structure_stdout, stderr=structure_stderr):
            print('  failed to create structure')
            try_remove_files(structure_log, structure_settings,
                structure_stdout, structure_stderr, geo_fname)
            return False
        structure_data = process_structure_log(structure_log)
        new_geo_fname = self.structure_new_geo_fname_template.format(
            geo_subdir, time_tag, structure_data['N_real'], self.Lr, self.ar,
            self.tau)
        shutil.move(geo_fname, new_geo_fname)
        try_remove_files(structure_log, structure_settings,
                structure_stdout, structure_stderr)
        geo_fname = new_geo_fname
        del new_geo_fname
        del structure_log
        del structure_settings
        del structure_stdout
        del structure_stderr
        print('  structure done')

        # fem
        fem_env = os.environ
        fem_env['LD_LIBRARY_PATH'] = '{0}/{1}:{0}/{2}'.format(
                self.fem_dir, self.libs, self.my_libs)

        # fem, gen_mesh
        meshing_parameters = [str(param) for param in self.meshing_parameters]
        fem_gen_stdout = self.fem_gen_stdout_template.format(
            files_subdir, time_tag)
        fem_gen_stderr = self.fem_gen_stderr_template.format(
            files_subdir, time_tag)
        code = subprocess.call(
            [self.gen_mesh_exe, geo_fname, *meshing_parameters],
            env=fem_env,
            cwd=self.local_wd,
            stdout=open(fem_gen_stdout, 'w'),
            stderr=open(fem_gen_stderr, 'w')) 
        if code not in self.gen_mesh_success:
            print('  failed to complete fem_gen:', code)
            try_remove_files(fem_gen_stdout, fem_gen_stderr,
                '{0}/{1}'.format(self.local_wd, self.gen_mesh_generated_mesh))
            return False
        shutil.move(
            '{0}/{1}'.format(self.local_wd, self.gen_mesh_generated_mesh),
            '{0}/{1}'.format(self.local_wd, self.process_mesh_input_mesh))
        try_remove_files(fem_gen_stdout, fem_gen_stderr)
        del meshing_parameters
        del fem_gen_stdout
        del fem_gen_stderr
        print('  gen_mesh done')

        # fem, process_mesh
        process_mesh_stdout = self.process_mesh_stdout_template.format(
            files_subdir, time_tag)
        process_mesh_stderr = self.process_mesh_stderr_template.format(
            files_subdir, time_tag)
        code = subprocess.call(
            self.process_mesh_exe,
            env=fem_env,
            cwd=self.local_wd,
            preexec_fn=lambda: resource.setrlimit(
                resource.RLIMIT_AS,
                (self.process_mesh_memory_limit,
                     self.process_mesh_memory_limit)),
            stdout=open(process_mesh_stdout, 'w'),
            stderr=open(process_mesh_stderr, 'w'))
        if code not in self.process_mesh_success:
            print('  failed to complete process_mesh:', code)
            try_remove_files(process_mesh_stdout, process_mesh_stderr,
                '{0}/{1}'.format(self.local_wd, self.process_mesh_input_mesh))
            return False
        try_remove_files(process_mesh_stdout, process_mesh_stderr,
            '{0}/{1}'.format(self.local_wd, self.process_mesh_input_mesh))
        print('  process_mesh done')


        # fem main
        for axis in ['XX', 'YY', 'ZZ']:
            fem_main_input = self.fem_main_input_template.format(
                files_subdir, time_tag, axis)
            fem_main_stdout = self.fem_main_stdout_template.format(
                files_subdir, time_tag, axis)
            fem_main_stderr = self.fem_main_stderr_template.format(
                files_subdir, time_tag, axis)
            fem_main_results_fname = self.fem_main_results_template.format(
                files_subdir, time_tag, axis)
            create_fem_input(
                Lx=self.ar/2 * self.disk_thickness * self.Lr,
                moduli=self.moduli,
                input_fname=fem_main_input,
                axis=axis,
                task_name=self.fem_main_task_name_template.format(
                    files_subdir, time_tag, axis),
                mesh_fname=self.process_mesh_generated_mesh,
                materials_fname='materials.bin')
            code = subprocess.call(
                [self.fem_main_exe, fem_main_input],
                env=fem_env,
                cwd=self.local_wd,
                stdout=open(fem_main_stdout, 'w'),
                stderr=open(fem_main_stderr, 'w'))
            if code not in self.fem_main_success:
                print('  fem_main along {0} failed:'.format(axis), code)
                try_remove_files(fem_main_stdout, fem_main_stderr, fem_main_input)
                return False
            fem_data = get_fem_main_results(fem_main_results_fname, axis=axis)
            new_results_json_entry = {
                'time_tag': time_tag,
                'ar': self.ar,
                'Lr': self.Lr,
                'tau': self.tau,
                'N': structure_data['N_real'],
                'axis': axis,
                'fi': fem_data['fi_filler'],
                'E': fem_data['E'],
                'Ef': self.moduli[0],
                'Em': self.moduli[1],
            }
            try_remove_files(fem_main_stdout, fem_main_stderr, fem_main_input)

            # output to .json:
            results_ready = []
            full_json_fname = '{0}/{1}'.format(self.local_wd, self.results_json)
            if self.results_json in os.listdir(self.local_wd):
                with open(full_json_fname) as f:
                    try:
                        results_ready = json.load(f)
                    except json.decoder.JSONDecodeError:
                        pass
            results_ready.append(new_results_json_entry)
            with open(full_json_fname, 'w') as f:
                json.dump(results_ready, f, indent=4)
            print('  fem_main done on', axis)
            del fem_main_input
            del fem_main_stdout
            del fem_main_stderr
            del fem_main_results_fname
            del fem_data
            del new_results_json_entry
            del results_ready
            del full_json_fname

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
            else:
                print('-')
                consecutive_fails += 1


if __name__ == '__main__':
    tau = 1
    ar = 5
    Lr = 10
    local_wd = 'local_ternary_Lr_{0}_ar_{1}_tau_{2}'.format(Lr, ar, tau)
    max_attempts = 100
    moduli = [232, 4, 1.5]
    results_json = 'ternary_Lr_{0}_ar_{1}_tau_{2}.json'.format(Lr, ar, tau)

    t = LocalTaskConsecutiveTernaryMc(
        local_wd=local_wd,
        ar=ar, tau=tau, Lr=Lr, max_attempts=max_attempts,
        moduli=moduli,
        results_json=results_json)
    t.run()
