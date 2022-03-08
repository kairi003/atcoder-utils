#!python3
# -*- coding: utf-8 -*-

import json
import sys
import os
from typing import Iterable
import re
import subprocess
from pathlib import Path
from atcoder import *


BASE_DIR = 'D:/Documents/Project/AtCoder'


def acset(contest_id, username, password):
    ac = AtCoderSession()
    ac.login(username, password)
    if m := re.match(r'https://kenkoooo.com/atcoder/#/contest/show/([0-9a-z-]+)', contest_id):
        contest_id = m[1]
        contest = VirtualContest(contest_id, ac)
        contest_dir = make_contest_dir(contest, 'problems')
    else:
        contest = AtCoderContest(contest_id, ac)
        contest_dir = make_contest_dir(contest)
        make_task(contest_dir, 'a')

    for task in contest.get_tasks():
        task_dir = make_task(contest_dir, task)
        make_sample(task_dir, task.input_samples, task.output_samples)
    return


def make_contest_dir(contest:ContestBase, parent:str='') -> Path:
    contest_dir = Path(BASE_DIR) / parent / contest.name
    contest_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(f'start {contest_dir}')
    subprocess.run(f'start {contest.url}')
    subprocess.run(f'start {contest.url}/tasks')
    subprocess.run(f'start {contest.url}/tasks/{contest.name}_a')
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


def make_task(contest_dir: Path, task: AtCoderTask) -> Path:
    task_name = re.sub(r'\A.+_', '', task.name)
    task_dir = contest_dir / task_name
    tpl_path = task_dir / f'{task_name}.py'
    tpl_path.parent.mkdir(parents=True, exist_ok=True)
    tpl_body = Path(__file__).with_name('template.py').read_text()
    contest_url = task.contest.url if task.contest else ''
    tpl_body = tpl_body.format(task_url=task.url, contest_url=contest_url)
    tpl_path.write_text(tpl_body, encoding='utf8')
    print(f'WRITE {tpl_path}')
    return task_dir


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    profile_path = Path('user_profile.json')
    user_profile = json.loads(profile_path.read_text())
    args = sys.argv
    acset(args[1], **user_profile)
