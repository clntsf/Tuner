from misc_util import sanitize_filepath
import os; from shutil import rmtree
from subprocess import run

check_installs = True
print('Installing Tuner package. Please wait...')
# --- Makes sure the user has the latest version of pip installed --- #
if check_installs:
    try: run(['pip', 'install', 'pip', '-U'], capture_output=False)
    except FileNotFoundError:
        run(['curl', 'https://bootstrap.pypa.io/get-pip.py', '-o', 'get-pip.py', '&&', 'python3', 'get-pip.py'], capture_output=True)
        os.remove('get-pip.py')

    # --- Make sure the user has needed dependencies installed and up to date --- #

    dependencies=['wxpython']
    for module_name in dependencies:
        run(['pip','install',module_name,'-U'], capture_output=True)
        print(f'{module_name} up to date.')

# --- Move this script's enclosing folder (containing the main scripts) into a specified directory --- #
this_dir, root_dir = os.path.realpath(__file__), os.getenv('HOME')
enclosing_folder = this_dir[:this_dir.rfind('/')]

# --- Make sure 'bin' folder to enclose the script exists --- #
run(['mkdir',f'{root_dir}/bin'], capture_output=True)

# --- Clean the filepath names for subprocess.run --- #
enclosing_folder_clean = sanitize_filepath(enclosing_folder)

# --- Move the installer's enclosing folder to its destination --- #
run(['mv',enclosing_folder_clean,f'{root_dir}/bin'],capture_output=True)

# --- Add the bin folder to path --- #
new_path_dir = f'PATH="{root_dir}/bin:$PATH"'

lines = open(f'{root_dir}/.zprofile','r').read().split('\n')
lines += not(new_path_dir in lines) and [new_path_dir] or []

with open(f'{root_dir}/.zprofile','w') as writer:
    writer.write('\n'.join(lines))

# --- Make the main file an executable, move it into the bin folder, and send completion message --- #
run(['chmod','+x',f'{root_dir}/bin/Tuner-main/tuner.py'],capture_output=False)
run(['mv',f'{root_dir}/bin/Tuner-main/tuner.py',f'{root_dir}/bin/tuner'],capture_output=False)
os.remove(f'{root_dir}/main.zip')
print('Package successfully installed. \nEnter "tuner" into the terminal at any time to start the app')
