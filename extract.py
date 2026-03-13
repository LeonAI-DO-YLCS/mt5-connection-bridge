import os

patch_file = '.jules-patches/s5-conformance.patch'
with open(patch_file, 'r', encoding='utf-8') as f:
    content = f.read()

files = content.split('diff --git a/')
for f in files:
    if not f.strip(): continue
    lines = f.split('\n')
    header = lines[0]
    fname = header.split(' b/')[0]
    
    # We only care about new conformance files
    if fname.startswith('app/conformance/probes/') or fname in ['app/conformance/runner.py', 'app/conformance/reporter.py', 'app/conformance/__main__.py', 'app/models/conformance.py']:
        print(f"Extracting {fname}...")
        
        # Determine if it's a new file (will have 'new file mode')
        is_new = any(l.startswith('new file mode') for l in lines[:5])
        
        if is_new:
            out = []
            starts_hunk = False
            for line in lines:
                if line.startswith('@@ '):
                    starts_hunk = True
                    continue
                if starts_hunk:
                    # For new files, all lines are either '+' or '\\ No newline at end of file'
                    if line.startswith('+'):
                        out.append(line[1:])
                    elif line.startswith('\\ '):
                        pass
                    elif line == '':
                        # empty line without '+' in diff? Sometimes git puts a space instead of '+', but for new files it's all '+'
                        pass
            
            os.makedirs(os.path.dirname(fname), exist_ok=True)
            with open(fname, 'w', encoding='utf-8') as outf:
                outf.write('\n'.join(out) + '\n')
            print(f"Created {fname}")
