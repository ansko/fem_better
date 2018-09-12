import json
import os
import shutil
import time

import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint

from fem.create_fem_input import create_fem_input
from fem.get_fem_main_results import get_fem_main_results
from fem.run_fem_main_ternary_exe import run_fem_main_ternary_exe
from fem.run_gen_mesh_exe import run_gen_mesh_exe
from fem.run_process_mesh_exe import run_process_mesh_exe

from structure.process_structure_log import process_structure_log
from structure.try_make_binary_structure_mc import try_make_binary_structure_mc


class LocalTaskConsecutiveBinaryMc:
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
    task_name_template = 'E_binary_local'

    def __init__(self, wd,
            ar, Lr,
            max_attempts,
            moduli,
            results_json,
            geo_dir='geo', files_dir='files'):
        try:
            os.mkdir(wd)
            os.mkdir('{0}/{1}'.format(wd, geo_dir))
            os.mkdir('{0}/{1}'.format(wd, files_dir))
        except FileExistsError:
            pass
        self.wd = wd
        self.geo_dir = geo_dir
        self.files_dir = files_dir
        self.ar = ar
        self.Lr = Lr
        self.max_attempts = max_attempts
        self.moduli = moduli
        self.results_json = results_json

    def single_loop(self, disks_number):
        time_tag = str(int(time.time()))
        log_entry = dict()

        # structure
        log_fname = '{0}/{1}/{2}'.format(
            self.wd, self.files_dir,
            '{0}_structure_log'.format(time_tag))
        settings_fname = '{0}/{1}/{2}'.format(
            self.wd, self.files_dir,
            '{0}_structure_settings'.format(time_tag))
        geo_fname = '{0}/{1}/{2}.geo'.format(
            self.wd, self.geo_dir, time_tag)
        stdout_fname =  '{0}/{1}/{2}'.format(
            self.wd, self.files_dir,
            '{0}_structure_stdout'.format(time_tag))
        stderr_fname =  '{0}/{1}/{2}'.format(
            self.wd, self.files_dir,
            '{0}_structure_stderr'.format(time_tag))
        try_make_binary_structure_mc(
            log_fname, settings_fname, geo_fname,
            self.ar, self.Lr, self.max_attempts,
            disks_number,
            disk_thickness=self.disk_thickness,
            vertices_number=self.vertices_number,
            stdout_exe=stdout_fname, stderr_exe=stderr_fname,
            structure_exe=self.structure_exe)
        structure_data = process_structure_log(log_fname)
        geo_template = '{0}/{1}/{2}_N_{3}_Lr_{4}_ar_{5}.geo'
        new_geo_fname = geo_template.format(self.wd, self.geo_dir,
            time_tag, structure_data['N_real'], self.Lr, self.ar)
        shutil.move(geo_fname, new_geo_fname)
        geo_fname = new_geo_fname
        os.remove(stdout_fname)
        os.remove(stderr_fname)
        print('  structure done')

        # fem, gen_mesh
        fem_gen_out =  '{0}/{1}/{2}'.format(
            self.wd, self.files_dir,
            '{0}_gen_mesh_stdout'.format(time_tag))
        fem_gen_err =  '{0}/{1}/{2}'.format(
            self.wd, self.files_dir,
            '{0}_gen_mesh_stderr'.format(time_tag))
        run_gen_mesh_exe(geo_fname=geo_fname,
            meshing_parameters=[0.15, 2, 2],
            gen_mesh_exe=self.gen_mesh_exe,
            libs=self.libs, my_libs=self.my_libs,
            stdout_exe=fem_gen_out, stderr_exe=fem_gen_err)
        os.remove(fem_gen_out)
        os.remove(fem_gen_err)
        print('  gen_mesh done')

        # fem, process_mesh
        process_mesh_out =  '{0}/{1}/{2}'.format(
            self.wd, self.files_dir,
            '{0}_process_mesh_stdout'.format(time_tag))
        process_mesh_err =  '{0}/{1}/{2}'.format(
            self.wd, self.files_dir,
            '{0}_process_mesh_stderr'.format(time_tag))
        run_process_mesh_exe(
            mesh_fname='generated.vol',
            process_mesh_exe='/home/anton/FEMFolder/processMesh.x',
            libs='/home/anton/FEMFolder/libs',
            my_libs='/home/anton/FEMFolder/my_libs',
            stdout_exe=process_mesh_out, stderr_exe=process_mesh_err,
            memory_ratio=0.3)
        os.remove(process_mesh_out)
        os.remove(process_mesh_err)
        print('  process_mesh done')

        # fem main
        fem_input_template_fname = 'input_{0}'
        fem_input_template = '{0}/{1}/{2}_{3}'.format(
            self.wd, self.files_dir, time_tag, fem_input_template_fname)
        for axis in ['XX', 'YY', 'ZZ']:
            script_fname = fem_input_template.format(axis)
            stdout_fname = '{0}/{1}/{2}_fem_main_{3}_out'.format(
                self.wd, self.files_dir, time_tag, axis)
            stderr_fname = '{0}/{1}/{2}_fem_main_{3}_err'.format(
                self.wd, self.files_dir, time_tag, axis)
            fem_main_results_fname = '{0}{1}_results.txt'.format(
                self.task_name_template, axis)
            create_fem_input(
                Lx=self.ar/2 * self.disk_thickness * self.Lr,
                moduli=self.moduli,
                input_fname=script_fname,
                axis=axis,
                task_name_template=self.task_name_template,
                mesh_fname='mesh.xdr',
                materials_fname='materials.bin')
            run_fem_main_ternary_exe(
                script_fname,
                fem_main_ternary_exe=self.fem_main_ternary_exe,
                libs=self.libs, my_libs=self.my_libs,
                stdout_exe=stdout_fname, stderr_exe=stderr_fname)
            fem_data = get_fem_main_results(fem_main_results_fname, axis=axis)
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
            os.remove(stdout_fname)
            os.remove(stderr_fname)
            os.remove(script_fname)
            shutil.move(fem_main_results_fname, '{0}/{1}/{2}_{3}'.format(
                self.wd, self.files_dir, time_tag, fem_main_results_fname))

            # output to .json:
            results_ready = []
            if self.results_json in os.listdir(self.wd):
                with open('{0}/{1}'.format(self.wd, self.results_json)) as f:
                    try:
                        results_ready = json.load(f)
                    except json.decoder.JSONDecodeError:
                        pass
            results_ready.append(new_results_json_entry)
            with open('{0}/{1}'.format(self.wd, self.results_json), 'w') as f:
                json.dump(results_ready, f, indent=4)
            print('  fem_main done on', axis)
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

            # clean-up after step finish
            for fname in ['mesh.xdr', 'out.mesh', 'stresses.txt']:
                if fname in os.listdir():
                    os.remove(fname)
            for axis in ['XX', 'YY', 'ZZ']:
                fem_main_log = '{0}log.txt'.format(self.task_name_template)
                if fem_main_log in os.listdir():
                    os.remove(fem_main_log)


if __name__ == '__main__':
    ar = 4
    Lr = 10
    wd = 'binary_Lr_{0}_ar_{1}'.format(Lr, ar)
    max_attempts = 100
    moduli = [232, 1.5]
    results_json = 'binary_Lr_{0}_ar_{1}.json'.format(Lr, ar)

    t = LocalTaskConsecutiveBinaryMc(wd=wd,
        ar=ar, Lr=Lr,
        max_attempts=max_attempts,
        moduli=moduli, results_json=results_json)
    t.run()
