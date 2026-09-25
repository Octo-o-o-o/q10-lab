# -*- coding: utf-8 -*-
"""Python 3.2-compatible read-only projection for the existing Term49 surface."""
from __future__ import print_function
import json
import calendar
import math
import os
import re
import sys
import time

def sample_ms(value):
    if not isinstance(value, str): return None
    match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?(Z|[+-]\d{2}:\d{2})$', value)
    if match is None: return None
    try:
        seconds = calendar.timegm(time.strptime(match.group(1), '%Y-%m-%dT%H:%M:%S'))
        zone = match.group(3)
        if zone != 'Z':
            hours = int(zone[1:3]); minutes = int(zone[4:6])
            if hours > 23 or minutes > 59: return None
            seconds -= (hours * 3600 + minutes * 60) * (1 if zone[0] == '+' else -1)
        return seconds * 1000 + int((match.group(2) or '0').ljust(6, '0')) / 1000
    except (ValueError, OverflowError): return None

def read_projection(path, now=None):
    now = int(time.time() * 1000) if now is None else now
    try:
        if os.path.getsize(path) > 1048576:
            return None
        with open(path, 'r', encoding='utf-8') as stream:
            value = json.load(stream)
        if value.get('schema') != 'octoooo.display.v1' or value.get('available') is not True:
            return None
        created = value.get('generated_at'); expires = value.get('expires_at')
        if not isinstance(created, (int, float)) or not isinstance(expires, (int, float)) or not created <= now < expires or expires - created > 30000:
            return None
        rows = []
        for index, raw in enumerate(value.get('usage', [])[:100]):
            provider = raw.get('provider') if raw.get('provider') in ['codex', 'claude', 'claude-code', 'cursor', 'openai', 'anthropic'] else 'AI'
            account = raw.get('account', '')
            if not re.match(r'^账号 [0-9]{1,4}$', account): account = '账号 {0}'.format(index + 1)
            window = raw.get('window') if raw.get('window') in ['primary', 'secondary', 'tertiary', 'five-hour', '5h', 'weekly', 'week', 'daily', 'day', 'monthly', 'month'] else '其他窗口'
            percent = raw.get('value')
            if isinstance(percent, bool) or not isinstance(percent, (int, float)) or not math.isfinite(percent) or percent < 0 or percent > 10000: percent = None
            observed = sample_ms(raw.get('observed_at')); reset = sample_ms(raw.get('reset_at'))
            stale = raw.get('stale') is not False or observed is None or observed > now or now - observed > 300000 or (reset is not None and reset <= now)
            rows.append({'provider': provider, 'account': account, 'window': window, 'percent': percent, 'stale': stale})
        out = {'synthetic': value.get('synthetic') is True, 'usage': rows}
        for name in ['pending', 'running', 'completed']:
            n = value.get(name)
            out[name] = n if isinstance(n, int) and not isinstance(n, bool) and 0 <= n <= 1000000 else 0
        return out
    except (OSError, ValueError, TypeError, AttributeError):
        return None

def render_projection(value, page=0):
    lines = ['Octoooo · 只读', time.strftime('%H:%M'), '']
    if value is None:
        lines += ['未连接 / 授权缓存已清除', '回主设备检查连接与授权。']
    else:
        lines += ['合成演示 · 未连接' if value['synthetic'] else '受限设备投影', '{0} 待查看 · {1} 运行中 · {2} 已完成'.format(value['pending'], value['running'], value['completed']), '用量 · 已用比例']
        rows = value['usage']; pages = max(1, (len(rows) + 3) // 4); page = page % pages
        for row in rows[page*4:(page+1)*4]:
            percent = '未知' if row['percent'] is None else '{0:g}%'.format(row['percent'])
            lines += [row['provider'] + ' · ' + row['account'], row['window'] + ' · ' + percent + (' · 过期' if row['stale'] else '')]
        lines += ['第 {0}/{1} 页'.format(page+1, pages)]
    return '\n'.join(lines + ['', 'J/N 下一页 · K/P 上一页 · Q 退出', '不执行任务，不自动标为已读。']) + '\n'

def run_monitor(args, read_key, write_out, clear_screen):
    page = 0
    while True:
        value = read_projection(args.octoooo_file)
        if sys.stdout.isatty(): clear_screen()
        pages = max(1, (len(value['usage']) + 3) // 4) if value is not None else 1
        if args.all:
            for index in range(pages): write_out(render_projection(value, index))
        else: write_out(render_projection(value, page))
        sys.stdout.flush()
        if args.once or args.all: return 0
        if sys.stdin.isatty(): key = read_key(min(5, max(1, args.interval)))
        else: time.sleep(min(5, max(1, args.interval))); key = None
        if key in ['q', 'Q', 'x', 'X', '\x03']: return 0
        if key in ['j', 'J', 'n', 'N']: page += 1
        if key in ['k', 'K', 'p', 'P']: page -= 1
