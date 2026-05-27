"""多计划打卡进度追踪器"""

import json
import os
from datetime import date, datetime

from .constants import _ZH

CHECKIN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'checkin.json')


class CheckInTracker:
    """数据结构 checkin.json:
    {
      "active": "plan_id",
      "plans": {
        "plan_id": {
          "name": "每周写公众号",
          "total": 32,
          "reward": "出国游一周",
          "start_date": "2026-04-20",
          "records": [{"date": "...", "note": "..."}, ...]
        }
      }
    }
    """

    def __init__(self):
        self.plans = {}
        self.active_id = None
        self._load()

    def _path(self):
        return CHECKIN_FILE

    def _load(self):
        try:
            with open(self._path(), 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'plans' in data:
                self.plans = data['plans']
                self.active_id = data.get('active')
            elif 'total' in data:
                pid = 'plan_1'
                self.plans = {pid: {
                    'name': '公众号写作计划' if _ZH else 'Writing Plan',
                    'total': data.get('total', 32),
                    'reward': data.get('reward', ''),
                    'start_date': data.get('start_date', date.today().isoformat()),
                    'records': data.get('records', []),
                }}
                self.active_id = pid
                self._save()
        except (FileNotFoundError, json.JSONDecodeError):
            self.plans = {}
            self.active_id = None

    def _save(self):
        data = {
            'active': self.active_id,
            'plans': self.plans,
        }
        with open(self._path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @property
    def active(self):
        if self.active_id and self.active_id in self.plans:
            return self.plans[self.active_id]
        return None

    @property
    def total(self):
        p = self.active
        return p['total'] if p else 0

    @property
    def done(self):
        p = self.active
        return len(p['records']) if p else 0

    @property
    def progress(self):
        return self.done / max(self.total, 1)

    @property
    def completed(self):
        return self.total > 0 and self.done >= self.total

    def has_plan(self):
        return self.active is not None

    def plan_names(self):
        result = []
        for pid, p in self.plans.items():
            result.append((pid, p['name'], len(p['records']), p['total']))
        return result

    def create_plan(self, name, total, reward='', start_date=None):
        pid = f'plan_{len(self.plans) + 1}_{int(datetime.now().timestamp())}'
        self.plans[pid] = {
            'name': name,
            'total': total,
            'reward': reward,
            'start_date': start_date or date.today().isoformat(),
            'records': [],
        }
        self.active_id = pid
        self._save()
        return pid

    def switch_plan(self, pid):
        if pid in self.plans:
            self.active_id = pid
            self._save()

    def delete_plan(self, pid):
        if pid in self.plans:
            del self.plans[pid]
            if self.active_id == pid:
                self.active_id = next(iter(self.plans), None)
            self._save()

    def checkin(self, note=''):
        p = self.active
        if not p:
            return
        today = date.today().isoformat()
        p['records'].append({'date': today, 'note': note})
        self._save()

    def checkin_plan(self, pid, note=''):
        p = self.plans.get(pid)
        if not p:
            return
        today = date.today().isoformat()
        p['records'].append({'date': today, 'note': note})
        self._save()

    def checked_today(self, pid):
        p = self.plans.get(pid)
        if not p:
            return False
        today = date.today().isoformat()
        return any(r['date'] == today for r in p['records'])

    def undo(self):
        p = self.active
        if p and p['records']:
            p['records'].pop()
            self._save()

    @property
    def streak(self):
        p = self.active
        if not p or not p['records']:
            return 0
        dates = sorted(set(r['date'] for r in p['records']), reverse=True)
        today = date.today()
        last = date.fromisoformat(dates[0])
        if (today - last).days > 1:
            return 0
        streak = 1
        for i in range(1, len(dates)):
            prev = date.fromisoformat(dates[i])
            curr = date.fromisoformat(dates[i - 1])
            if (curr - prev).days == 1:
                streak += 1
            elif (curr - prev).days == 0:
                continue
            else:
                break
        return streak

    @property
    def days_since_last(self):
        p = self.active
        if not p or not p['records']:
            return -1
        last_date = max(r['date'] for r in p['records'])
        return (date.today() - date.fromisoformat(last_date)).days

    def summary(self):
        p = self.active
        if not p:
            return '暂无打卡计划' if _ZH else 'No active plan'

        name = p['name']
        done = len(p['records'])
        total = p['total']
        reward = p.get('reward', '')

        if _ZH:
            s = f'📋 {name}\n进度: {done}/{total}'
            if done >= total:
                s += f'\n🎉 全部完成！'
                if reward:
                    s += f'奖励: {reward}'
            else:
                s += f'\n剩余: {total - done}'
                try:
                    start = date.fromisoformat(p.get('start_date', ''))
                    today_d = date.today()
                    weeks_passed = max((today_d - start).days, 0) / 7
                    expected = min(int(weeks_passed * 2), total)
                    diff = done - expected
                    if diff >= 0:
                        s += ' ✅ 进度正常'
                    else:
                        s += f' ⚠️ 落后 {-diff}'
                except Exception:
                    pass
                if reward:
                    s += f'\n🎁 奖励: {reward}'
        else:
            s = f'📋 {name}\nProgress: {done}/{total}'
            if done >= total:
                s += f'\n🎉 Done!'
                if reward:
                    s += f' Reward: {reward}'
            else:
                s += f'\nRemaining: {total - done}'
                if reward:
                    s += f'\n🎁 Reward: {reward}'
        return s
