#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import webbrowser
import argparse
import json
import sys
from typing import Iterable
import re
import subprocess
from pathlib import Path
import shutil
from .acclient import *

CONFIG_NAME = '.acset'

class ACSetConfig:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.load()

    def load(self) -> dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f'Config file not found at: {self.config_path}')
        data = json.loads(self.config_path.read_text())
        if not isinstance(data, dict):
            raise ValueError(f'Config file is not a valid JSON: {self.config_path}')
        self.dir_path = self.load_path(data['dir_path'])
        self.cookies_path = self.load_path(data['cookies_path'])
        self.template_path = self.load_path(data['template_path'])
        self.browser_open: bool = data.get('browser_open', True)
        self.exec_command: list[str] | None = data.get('exec_command', None)
    
    def load_path(self, path: str) -> Path:
        p = self.config_path.parent / Path(path).expanduser()
        return p.resolve()
    
    @classmethod
    def find_config(cls) -> 'ACSetConfig':
        config_paths = [
            Path.cwd() / CONFIG_NAME / 'config.json',
            Path.home() / CONFIG_NAME / 'config.json',
            Path.home() / '.config' / CONFIG_NAME / 'config.json',
        ]
        for config_path in config_paths:
            if config_path.exists():
                return cls(config_path)
        raise FileNotFoundError(f'Config file not found at: {config_paths}')
    


class ACSet:
    def __init__(self, config: ACSetConfig):
        self.config = config
    
    def acset(self, contest_id: str):
        ac = AtCoderSession()
        ac.login(self.config.cookies_path)
        if m := re.match(r'https://kenkoooo.com/atcoder/#/contest/show/([0-9a-z-]+)', contest_id):
            contest_id = m[1]
            contest = VirtualContest(contest_id, ac)
            contest_dir = self.make_contest_dir(contest, 'problems')
        else:
            contest = AtCoderContest(contest_id, ac)
            contest_dir = self.make_contest_dir(contest)
            self.make_task(contest_dir, AtCoderTask('', '_', ac, contest))

        for task in contest.get_tasks():
            task_dir = self.make_task(contest_dir, task)
            self.make_sample(task_dir, task.input_samples, task.output_samples)
        return
    
    
    def make_contest_dir(self, contest: ContestBase, parent: str = '') -> Path:
        contest_dir = self.config.dir_path / parent / contest.name
        contest_dir.mkdir(parents=True, exist_ok=True)
        if Path(__file__).with_name('.vscode').exists():
            shutil.copytree(Path(__file__).with_name('.vscode'),
                            contest_dir / '.vscode', dirs_exist_ok=True)
        if self.config.browser_open:
            webbrowser.open(f'{contest.url}')
            webbrowser.open(f'{contest.url}/tasks')
            webbrowser.open(f'{contest.url}/tasks/{contest.name}_a')
        if self.config.exec_command is not None:
            command = self.config.exec_command 
            subprocess.run([*command, str(contest_dir)])
        return contest_dir
    
    def make_sample(self, task_dir: Path, in_samps: Iterable[str], out_samps: Iterable[str]) -> Path:
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


    def make_task(self, contest_dir: Path, task: AtCoderTask) -> Path:
        task_name = re.sub(r'\A.+_', '', task.name)
        task_dir = contest_dir / task_name
        template_path = self.config.template_path
        print(template_path)
        for tpl in template_path.glob('template.*'):
            tpl_path = task_dir / (task_name + tpl.suffix)
            tpl_path.parent.mkdir(parents=True, exist_ok=True)
            tpl_body = tpl.read_text()
            contest_url = task.contest.url if task.contest else ''
            tpl_body = tpl_body.replace('{task_url}', task.url).replace(
                '{contest_url}', contest_url)
            tpl_path.write_text(tpl_body, encoding='utf8')
            print(f'WRITE {tpl_path}')
        return task_dir
        

def main():
    class Namespace(argparse.Namespace):
        contest_id: str | None = None
        setup: Path | None = None
    parser = argparse.ArgumentParser()
    parser.add_argument('contest_id', type=str, nargs='?', default=None)
    parser.add_argument('--setup',
                        nargs='?',
                        type=Path,
                        const=Path.home(),
                        default=None,
                        help='make config dir to specified path'
                        )
    args = parser.parse_args(namespace=Namespace)

    if args.setup:
        template_path = Path(__file__).parent / 'config_template/acset'
        config_path = args.setup / CONFIG_NAME
        shutil.copytree(template_path, config_path, dirs_exist_ok=False)
        print(f'Config dir created at {config_path}', file=sys.stderr)
        return
    if args.contest_id is None:
        raise ValueError('contest_id is required')
    
    contest_id = args.contest_id

    config = ACSetConfig.find_config()
    ACSet(config).acset(contest_id)
    return


if __name__ == "__main__":
    main()
