#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import time
from urllib.parse import urljoin
from datetime import datetime, timezone, timedelta
import re
from typing import Generator, Optional
from bs4 import BeautifulSoup
from requests import Session
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

RETRY_COUNT = 10
#USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'


class AtCoderSession(Session):
    def __init__(self):
        super().__init__()
        retries = Retry(total=RETRY_COUNT, backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504])
        self.mount("https://", HTTPAdapter(max_retries=retries))
        #self.headers = {'User-Agent': USER_AGENT}

    def login(self, username: str, password: str):
        login_url = 'https://atcoder.jp/login'
        res = self.get(login_url)
        login_page = BeautifulSoup(res.content, 'lxml')
        form = login_page.select_one('#main-container form')
        form_values = {f['name']: f.get('value', '')
                       for f in form.select('input')}
        form_values['username'] = username
        form_values['password'] = password
        response = self.post(login_url, params=form_values)
        if response.url != 'https://atcoder.jp/home':
            raise Exception('username or password is wrong')


class AtCoderTask:
    def __init__(self, url: Optional[str]=None, name: Optional[str]=None,  ses: Optional[Session] = None, contest:Optional['ContestBase']=None):
        self.url = url
        self.name = name if name else url.split('/')[-1]
        self.ses = ses if ses is not None else Session()
        self.contest = contest
        self._get_samples()

    def _get_samples(self):
        self.input_samples = []
        self.output_samples = []
        if not self.url:
            return
        res = self.ses.get(self.url)
        soup = BeautifulSoup(res.content, 'lxml')
        for sec in soup.select('#task-statement section'):
            h3 = sec.select_one('h3')
            pre = sec.select_one('pre')
            if h3 is None or pre is None:
                continue
            text = re.sub(r'\r\n?', '\n', pre.text.strip())
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
        tasks_url = f'{self.url}/tasks/'
        res = self.ses.get(tasks_url)
        soup = BeautifulSoup(res.content, 'lxml')
        for tr in soup.select('tbody tr'):
            a = tr.select_one("a[href*='/tasks/']")
            if a is None:
                continue
            task_url = urljoin(tasks_url, a['href'])
            task_name = a.text.strip().lower()
            yield AtCoderTask(task_url, task_name, self.ses, self)


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
