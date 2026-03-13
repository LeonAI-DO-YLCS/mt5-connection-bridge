import os

patch_file = '.jules-patches/s6-governance.patch'
with open(patch_file, 'r', encoding='utf-8') as f:
    content = f.read()

files = content.split('diff --git a/')
for f in files:
    if not f.strip(): continue
    lines = f.split('\n')
    header = lines[0]
    fname = header.split(' b/')[0]
    
    if fname in ['config/parity-coverage-matrix.yaml', 'config/governance-checklist.yaml', 'scripts/validate_governance.py']:
        print(f"Extracting {fname}...")
        
        out = []
        starts_hunk = False
        for line in lines:
            if line.startswith('@@ '):
                starts_hunk = True
                continue
            if starts_hunk:
                if line.startswith('+'):
                    out.append(line[1:])
                elif line.startswith(' '):
                    out.append(line[1:])
                elif line.startswith('-'):
                    pass
                elif line == '':
                    pass
                else:
                    break # Reached end of diff
        
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with open(fname, 'w', encoding='utf-8') as outf:
            outf.write('\n'.join(out) + '\n')
        print(f"Created/Updated {fname}")
