#!/usr/bin/env python3

import os
import sys
import re
import subprocess
import time
from pathlib import Path


def add_top(string, head):
    return re.sub(r'^', head, string, flags=re.MULTILINE)

def strtr(string, to):
    return re.sub(r'\r\n|\r|\n', to, string)

def arg_parse(args: list[str]) -> list[str]:
    args[0] = 'python'
    if len(args) == 1:
        filelist = os.listdir('./')
        scriptfile = [f for f in filelist if '.py' in f][0]
        args.append(scriptfile)
    return args


def main():

    cmd = arg_parse(sys.argv)
    print(f'cmd: {cmd}')
    in_dir = Path('./in')
    out_dir = Path('./out')
    for i, input_path in enumerate(in_dir.glob('*')):

        # show TEST No.
        print(f'{input_path.name}:')

        # show INPUT
        input_str = strtr(input_path.read_text().rstrip(), '\n')
        print(add_top(input_str, '<<'))

        # processing test
        t = time.time()
        proc = subprocess.run(cmd, input=input_str.encode() ,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        tr = time.time() - t

        # show OUTPUT
        output_str = strtr(proc.stdout.decode().rstrip(), '\n')
        print(add_top(output_str, '>>'))

        # show true output
        model_path = out_dir / input_path.name
        if model_path.exists():
            model_str = strtr(model_path.read_text().rstrip(), '\n')
            print(add_top(model_str, '~~'))
        else:
            model_str = None
        # judge
        print(f'result: {output_str == model_str}, {tr * 1000} ms\n')


if __name__ == "__main__":
    main()
