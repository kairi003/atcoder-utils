#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
from typing import Iterable
import re
import subprocess
from pathlib import Path
import shutil
from atcoder import *

ENVDIR_NAME = '.acset'

def acset(contest_id: str, username: str, password: str, envdir: Path):
    ac = AtCoderSession()
    ac.login(username, password)
    if m := re.match(r'https://kenkoooo.com/atcoder/#/contest/show/([0-9a-z-]+)', contest_id):
        contest_id = m[1]
        contest = VirtualContest(contest_id, ac)
        contest_dir = make_contest_dir(contest, 'problems')
    else:
        contest = AtCoderContest(contest_id, ac)
        contest_dir = make_contest_dir(contest)
        make_task(contest_dir, AtCoderTask('', '_', ac, contest), envdir)

    for task in contest.get_tasks():
        task_dir = make_task(contest_dir, task, envdir)
        make_sample(task_dir, task.input_samples, task.output_samples)
    return


def make_contest_dir(contest:ContestBase, parent:str='') -> Path:
    contest_dir = Path('.') / parent / contest.name
    contest_dir.mkdir(parents=True, exist_ok=True)
    if Path(__file__).with_name('.vscode').exists():
        shutil.copytree(Path(__file__).with_name('.vscode'), contest_dir / '.vscode', dirs_exist_ok=True)
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
    for i, in_samp in enumerate(in_samps, start=1):
        input_path = in_dir / f's{i:02}'
        input_path.write_text(in_samp)
        print(f'WRITE {input_path}')
    for i, out_samp in enumerate(out_samps, start=1):
        output_path = out_dir / f's{i:02}'
        output_path.write_text(out_samp)
        print(f'WRITE {output_path}')


def make_task(contest_dir: Path, task: AtCoderTask, envdir: Path) -> Path:
    task_name = re.sub(r'\A.+_', '', task.name)
    task_dir = contest_dir / task_name
    print((envdir / 'template'))
    for tpl in (envdir / 'template').glob('template.*'):
        tpl_path = task_dir / (task_name + tpl.suffix)
        tpl_path.parent.mkdir(parents=True, exist_ok=True)
        tpl_body = tpl.read_text()
        contest_url = task.contest.url if task.contest else ''
        tpl_body = tpl_body.replace('{task_url}',task.url).replace('{contest_url}',contest_url)
        tpl_path.write_text(tpl_body, encoding='utf8')
        print(f'WRITE {tpl_path}')
    return task_dir


def main():
    class Namespace(argparse.Namespace):
        contest_id: str
    parser = argparse.ArgumentParser()
    parser.add_argument('contest_id', type=str)
    args = parser.parse_args(namespace=Namespace)
    contest_id = args.contest_id

    base_list = ['.', '~']
    for base in base_list:
        envdir = (Path(base) / ENVDIR_NAME).expanduser()
        if envdir.exists(): break
    envdir = envdir.absolute()
    config = json.loads((envdir / 'config.json').read_text())
    dir_path = Path(config['dir_path']).expanduser()
    dir_path.mkdir(parents=True, exist_ok=True)
    os.chdir(dir_path)
    acset(contest_id, **config['profile'], envdir=envdir)


if __name__ == "__main__":
    main()
