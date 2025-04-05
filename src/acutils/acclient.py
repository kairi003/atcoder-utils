#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import time
from urllib.parse import urljoin
from datetime import datetime, timezone, timedelta
import re
from typing import Generator, Optional
from bs4 import BeautifulSoup, Tag
from requests import Session
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from http.cookiejar import MozillaCookieJar
from pathlib import Path

__all__ = [
    'AtCoderSession',
    'AtCoderTask',
    'AtCoderPrintTask',
    'ContestBase',
    'AtCoderContest',
    'VirtualContest',
]

RETRY_COUNT = 10
#USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'


class AtCoderSession(Session):
    def __init__(self):
        super().__init__()
        retries = Retry(total=RETRY_COUNT, backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504])
        self.mount("https://", HTTPAdapter(max_retries=retries))
        #self.headers = {'User-Agent': USER_AGENT}

    def login(self, cookies_path: Path):
        jar = MozillaCookieJar(str(cookies_path.absolute()))
        jar.load(ignore_discard=True, ignore_expires=True)
        self.cookies = jar
        login_url = 'https://atcoder.jp/settings'
        res = self.get(login_url, allow_redirects=False)
        if res.status_code != 200:
            raise Exception('cookie is expired')
        jar.save(ignore_discard=True, ignore_expires=True)


class AtCoderTask:
    def __init__(self, url: Optional[str]=None, name: Optional[str]=None,  ses: Optional[Session] = None, contest:Optional['ContestBase']=None):
        self.url = url
        self.name = name if name else url.split('/')[-1]
        self.ses = ses if ses is not None else Session()
        self.contest = contest
        self.input_samples = []
        self.output_samples = []
        self._get_samples()

    def _get_samples(self):
        if not self.url:
            return
        res = self.ses.get(self.url)
        soup = BeautifulSoup(res.content, 'lxml')
        for sec in soup.select('#task-statement section'):
            h3 = sec.select_one('h3')
            pre = sec.select_one('pre')
            if h3 is None or pre is None:
                continue
            text = re.sub(r'\r\n?', '\n', pre.text.strip()) + '\n'
            if '入力例' in h3.text:
                self.input_samples.append(text)
            elif '出力例' in h3.text:
                self.output_samples.append(text)
        return

class AtCoderPrintTask(AtCoderTask):
    def __init__(self, name: str, task_statement: Tag, contest: 'ContestBase'):
        self.url = f'{contest.url}/tasks/{contest.name}_{name}'
        self.name = name
        self.ses = None
        self.contest = contest
        self.input_samples = []
        self.output_samples = []
        self._get_samples(task_statement)
    
    def _get_samples(self, task_statement: Tag):
        for part in task_statement.select('.part'):
            h3 = part.select_one('h3')
            pre = part.select_one('pre')
            if h3 is None or pre is None:
                continue
            text = re.sub(r'\r\n?', '\n', pre.text.strip()) + '\n'
            if '入力例' in h3.text:
                self.input_samples.append(text)
            elif '出力例' in h3.text:
                self.output_samples.append(text)
        return


class ContestBase(ABC):
    name: str
    id: str
    title: str
    url: str
    ses: Session

    @abstractmethod
    def __init__(self, id_: str, ses: Optional[Session]): pass

    @abstractmethod
    def get_tasks(self) -> Generator[AtCoderTask, None, None]: pass


class AtCoderContest(ContestBase):
    WAIT = 1

    def __init__(self, id_: str, ses: Optional[Session]):
        self.name = id_
        self.id = id_
        self.title = id_
        self.url = f'https://atcoder.jp/contests/{id_}'
        self.ses = ses if ses is not None else AtCoderSession()
        self.start_time, self.end_time = self.get_time()

    def get_time(self) -> tuple[datetime, datetime]:
        res = self.ses.get(self.url)
        start_time_str = re.search(
            r'var startTime = moment\("(.+)"\);', res.text)[1]
        end_time_str = re.search(
            r'\s*var endTime = moment\("(.+)"\);', res.text)[1]
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
        return start_time, end_time

    def get_tasks(self) -> Generator[AtCoderTask, None, None]:
        zero = timedelta(seconds=-5)
        while (d := self.start_time - datetime.now(timezone.utc)) > zero:
            print(f'\rContest begins in {d}', end='\r')
            time.sleep(self.WAIT)
        tasks_url = f'{self.url}/tasks_print/'
        res = self.ses.get(tasks_url)
        soup = BeautifulSoup(res.content, 'lxml')
        for task_statement in soup.select('#task-statement'):
            task_content = task_statement.parent
            task_name = task_content.select_one('.h2').text.split('-', 1)[0].strip().lower()
            yield AtCoderPrintTask(task_name, task_statement, self)
            #yield AtCoderTask(task_url, task_name, self.ses, self)


class VirtualContest(ContestBase):
    def __init__(self, id_: str, ses: Optional[Session]=None):
        self.url = f'https://kenkoooo.com/atcoder/#/contest/show/{id_}'
        self.ses = ses if ses is not None else AtCoderSession()
        self.api_url = f'https://kenkoooo.com/atcoder/internal-api/contest/get/{id_}'
        self.data = self.ses.get(self.api_url).json()
        self.id: str = self.data['info']['id']
        self.title: str = self.data['info']['title']
        self.name: str = f'{self.title}_{self.id}'

    def get_tasks(self) -> Generator[AtCoderTask, None, None]:
        mp_url = 'https://kenkoooo.com/atcoder/resources/merged-problems.json'
        mp = {item['id']: item for item in self.ses.get(mp_url).json()}
        for i, p in enumerate(self.data['problems'], start=1):
            c_id = mp[p['id']]['contest_id']
            task_url = f"https://atcoder.jp/contests/{c_id}/tasks/{p['id']}"
            yield AtCoderTask(task_url, f'{i:02}_{p["id"]}', self.ses, self)
