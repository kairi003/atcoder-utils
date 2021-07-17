#!python3.8
# -*- coding: utf-8 -*-

import json
import sys
import os
from typing import Iterable
import re
import time
import subprocess
from pathlib import Path
from atcoder import AtCoder


BASE_DIR = 'D:/Documents/Project/AtCoder'


def acset(contest_name, username, password):
    ac = AtCoder(username, password)
    contest = ac.get_contest(contest_name)

    print(f'SET {contest_name}')
    contest_dir = make_contest_dir(contest_name)
    make_task(contest_dir, 'a')

    wait = contest.get_sec_to_start()
    if wait > 0:
        wait += 10
        print(f'WAIT {wait} sec')
        time.sleep(wait)
    
    for task_name, in_samps, out_samps in contest.get_task_sample():
        task_dir = make_task(contest_dir, task_name)
        make_sample(task_dir, in_samps, out_samps)
    
    return


def make_contest_dir(contest_name) -> Path:
    contest_dir = Path(BASE_DIR) / contest_name
    contest_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(f'start {contest_name}')
    return contest_dir


def make_sample(task_dir: Path, in_samps: Iterable[str], out_samps: Iterable[str]) -> Path:
    in_dir = task_dir / 'in'
    in_dir.mkdir(parents=True, exist_ok=True)
    out_dir = task_dir / 'out'
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, in_samp in enumerate(in_samps):
        input_path = in_dir / f's{i:02}'
        input_path.write_text(in_samp)
        print(f'WRITE {input_path}')
    for i, out_samp in enumerate(out_samps):
        output_path = out_dir / f's{i:02}'
        output_path.write_text(out_samp)
        print(f'WRITE {output_path}')


def make_task(contest_dir: Path, _task_name: str) -> Path:
    task_name = re.sub(r'\A.+_', '', _task_name)
    task_dir = contest_dir / task_name
    tpl_path = task_dir / f'{task_name}.py'
    tpl_path.parent.mkdir(parents=True, exist_ok=True)
    tpl_body = Path(__file__).with_name('template.py').read_text().format(contest=contest_dir.name, task=task_name)
    tpl_path.write_text(tpl_body)
    print(f'WRITE {tpl_path}')
    return task_dir


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    profile_path = Path('user_profile.json')
    user_profile = json.loads(profile_path.read_text())
    args = sys.argv
    acset(args[1], **user_profile)
