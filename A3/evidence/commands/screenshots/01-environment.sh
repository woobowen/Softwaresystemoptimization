set -eu
printf '$ bash A3/evidence/commands/screenshots/01-environment.sh\n'
printf 'Saved school-server environment (evidence/environment/school_gpu.json):\n'
python3 - <<'FIELDS'
import json
m=json.load(open('A3/evidence/environment/school_gpu.json'))
print('OS:',m['os_release']['PRETTY_NAME'])
for line in m['lscpu'].splitlines():
 if line.startswith(('Model name:', 'Socket(s):', 'CPU(s):')): print(line)
ram=int(m['free'].splitlines()[1].split()[1])
print(f'RAM: {ram} bytes ({ram/2**30:.3f} GiB)')
print('Python:',m['python'].split()[0])
print('PyTorch:',m['torch'])
print('PyTorch CUDA runtime:',m['torch_cuda_build'])
print('Triton:',m['triton'])
print('GPU:',m['gpu']['name'])
print('GPU memory:',m['gpu']['memory_bytes'],'bytes')
print('Compute capability:',m['gpu']['compute_capability'])
print('GPU UUID -> process cuda:0:',m['cuda_visible_devices'])
print('Python executable:',m['python_executable'])
print('Experiment directory:',m['cwd'])
print('CPU threads:',m['cpu_threads'])
FIELDS
printf '\nGPU resource snapshot before the main naive experiment:\n'
cat A3/evidence/commands/gpu_before_gpu-naive.txt
