import subprocess


def try_make_binary_structure_mc(
        log_fname, settings_fname, geo_fname,
        ar, Lr, max_attempts, disks_number,
        disk_thickness=0.1, vertices_number=6,
        stdout_exe=None, stderr_exe=None, structure_exe='./structure/binary_mc'):

    """
    Creates the structure of the ternary composite where fillers are
    represented as disks and interface is represented as bigger disks
    with the same center and orientation; the matrix is a cube.

    Required parameters for MX_exfoliation are:
        Lx, thickness, outer_radius, vertices_number,
        disks_number, max_attempts, LOG, geo_fname

    Parameters:
        geo_fname        the name of the output file with structure in CSG format
        log_fname        the name of the log file
        settings_fname   the name of the (temporary) file where setting for the
                             structure executabel will be stored
        ar               aspect ratio of the disk
        Lr               the ratio between the filler's radius and the box size
        max_attempts     maximal number of attempts to place fillers
        disks_number     the number of the fillers in the box

        disk_thickness   the thickness of the disk (should not determine the
                             properties of the system; plays role of the
                             distance unit)
        vertices_number  the number of the vertices in the polygon that is
                            top/bottom of the disk (6 seems to be the best value)

        stdout_exe       the name of the file with strucutre executable stdout
        stderr_exe       the name of the file with strucutre executable stderr
        structure_exe    the name of the executable that creates the structure
    """
    # Create settings file for structure executable
    with open(settings_fname, 'w') as f:
        f.write('Lx {0}\n'.format(ar/2 * disk_thickness * Lr))
        f.write('thickness {0}\n'.format(disk_thickness))
        f.write('outer_radius {0}\n'.format(ar/2 * disk_thickness))
        f.write('vertices_number {0}\n'.format(vertices_number))
        f.write('disks_number {0}\n'.format(disks_number))
        f.write('max_attempts {0}\n'.format(max_attempts))
        f.write('LOG {0}\n'.format(log_fname))
        f.write('geo_fname {0}\n'.format(geo_fname))

    # Run executable
    if stdout_exe:
        stdout_exe = open(stdout_exe, 'w')
    if stderr_exe:
        stderr_exe = open(stderr_exe, 'w')
    code = subprocess.call(
        [structure_exe, settings_fname],
        stdout=stdout_exe, stderr=stderr_exe)
    if code == 0:
        return True
    return False
