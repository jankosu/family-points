#!/usr/bin/env python3
"""Rodzinne Punkty - backend Flask (logika + API), bez HTML w kodzie."""
import os
import math
from datetime import date
from pathlib import Path

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import timedelta
from werkzeug.security import check_password_hash
import secrets
import time

from tasks import base_for, EXTRA, KIDS, all_task_defs

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY'),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
)


@app.before_request
def require_login():
    if request.endpoint == 'static' or request.path == '/login':
        return None
    if not session.get('user'):
        if request.path.startswith('/api/'):
            return jsonify(error='Zaloguj się do aplikacji'), 401
        return redirect(url_for('login'))
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
        if not token or not secrets.compare_digest(token, session.get('csrf', '')):
            return jsonify(error='Nieprawidłowy token formularza. Odśwież stronę.'), 400


@app.after_request
def private_response(response):
    if request.endpoint != 'static':
        response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('index'))
    session.setdefault('csrf', secrets.token_urlsafe(32))
    error, status = None, 200
    if request.method == 'POST':
        token = request.form.get('csrf_token', '')
        if not token or not secrets.compare_digest(token, session['csrf']):
            error, status = 'Odśwież stronę i spróbuj ponownie.', 400
        else:
            now = time.time()
            address = request.remote_addr or 'unknown'
            with store.con() as c:
                c.execute('BEGIN IMMEDIATE')
                c.execute('DELETE FROM login_attempts WHERE attempted < ?', (now - 300,))
                count = c.execute('SELECT count(*) FROM login_attempts WHERE address=?', (address,)).fetchone()[0]
                if count < 10:
                    c.execute('INSERT INTO login_attempts VALUES (?, ?)', (address, now))
            if count >= 10:
                error, status = 'Za dużo prób. Spróbuj ponownie za 5 minut.', 429
            else:
                password_hash = os.environ.get('LOGIN_PASSWORD_HASH', '')
                password_ok = bool(password_hash) and check_password_hash(password_hash, request.form.get('password', ''))
                username_ok = request.form.get('username', '') == os.environ.get('LOGIN_USER', 'rodzic')
                if password_ok and username_ok:
                    with store.con() as c:
                        c.execute('DELETE FROM login_attempts WHERE address=?', (address,))
                    session.clear()
                    session['user'] = os.environ.get('LOGIN_USER', 'rodzic')
                    session['csrf'] = secrets.token_urlsafe(32)
                    session.permanent = True
                    return redirect(url_for('index'))
                error, status = 'Nieprawidłowy login lub hasło.', 401
    return render_template('login.html', error=error), status


@app.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

DB_PATH = os.getenv('POINTS_DB', '/var/lib/rodzinne-punkty/points.db')
PARENT_PIN = os.getenv('PARENT_PIN', '1234')

import sqlite3
from contextlib import contextmanager


class FamilyPoints:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def con(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def _init_db(self):
        with self.con() as c:
            c.execute('CREATE TABLE IF NOT EXISTS login_attempts(address TEXT, attempted REAL)')
            c.execute('CREATE INDEX IF NOT EXISTS login_attempts_address ON login_attempts(address)')
            c.execute('CREATE TABLE IF NOT EXISTS checks('
                      'day TEXT, child TEXT, task TEXT, checked INTEGER, '
                      'PRIMARY KEY(day, child, task))')
            c.execute('CREATE TABLE IF NOT EXISTS rewards('
                      'id INTEGER PRIMARY KEY, title TEXT, cost INTEGER, active INTEGER DEFAULT 1, '
                      'unit_minutes INTEGER)')
            cols = {r['name'] for r in c.execute('PRAGMA table_info(rewards)')}
            if 'unit_minutes' not in cols:
                c.execute('ALTER TABLE rewards ADD COLUMN unit_minutes INTEGER')
            c.execute('CREATE TABLE IF NOT EXISTS redemptions('
                      'id INTEGER PRIMARY KEY, child TEXT, cost INTEGER, created TEXT)')
            if not c.execute('SELECT count(*) FROM rewards').fetchone()[0]:
                c.executemany('INSERT INTO rewards(title, cost, unit_minutes) VALUES(?, ?, ?)', [
                    ('Wybór deseru lub śniadania', 15, None),
                    ('20 min ekranów / wybór filmu', 8, 20),
                    ('Wybór piątkowej kolacji', 30, None),
                    ('Godzina z rodzicem na aktywność', 40, None),
                    ('Mała nagroda lub lokalne wyjście', 60, None),
                    ('Kino, basen lub duża aktywność', 90, None),
                    ('20 min YouTube', 16, 20),
                ])

    def tasks(self, d, k):
        if k not in {child['id'] for child in KIDS}:
            raise ValueError('Nieznane dziecko')
        base = base_for(date.fromisoformat(d))
        with self.con() as c:
            checked = {r['task']: bool(r['checked']) for r in
                       c.execute('SELECT task, checked FROM checks WHERE day=? AND child=?', (d, k))}
        return [
            {'id': x[0], 'title': x[1], 'points': x[2], 'period': x[3], 'kind': kind,
             'checked': checked.get(x[0], False)}
            for kind, arr in [('base', base), ('extra', EXTRA)] for x in arr
        ]

    def summary(self, d, k):
        ts = self.tasks(d, k)
        base = [x for x in ts if x['kind'] == 'base']
        today = sum(x['points'] for x in ts if x['checked'])
        with self.con() as c:
            got = sum(self._historic_points(r['task']) for r in
                      c.execute('SELECT task FROM checks WHERE child=? AND checked=1', (k,)))
            spent = c.execute('SELECT COALESCE(SUM(cost), 0) FROM redemptions WHERE child=?', (k,)).fetchone()[0]
        return {
            'today_points': today,
            'base_complete': all(x['checked'] for x in base),
            'base_done': sum(x['checked'] for x in base),
            'base_total': len(base),
            'balance': got - spent,
        }

    def _historic_points(self, task_id):
        return all_task_defs().get(task_id, (None, 0))[1]

    def toggle(self, d, k, t, on):
        ts = self.tasks(d, k)
        valid = {x['id'] for x in ts}
        if t not in valid:
            raise ValueError('Nieznane zadanie')
        with self.con() as c:
            c.execute(
                'INSERT INTO checks VALUES(?, ?, ?, ?) '
                'ON CONFLICT(day, child, task) DO UPDATE SET checked=excluded.checked',
                (d, k, t, int(bool(on))))

    def rewards(self):
        with self.con() as c:
            return [dict(x) for x in c.execute(
                'SELECT id, title, cost, unit_minutes FROM rewards WHERE active=1 ORDER BY cost, id')]

    def add_reward(self, t, cost):
        if not t.strip() or not isinstance(cost, int) or not 0 < cost < 1000:
            raise ValueError('Podaj nazwę i cenę 1-999.')
        with self.con() as c:
            c.execute('INSERT INTO rewards(title, cost) VALUES(?, ?)', (t.strip(), cost))

    def redeem(self, k, rid, minutes=None):
        r = next((x for x in self.rewards() if x['id'] == int(rid)), None)
        if not r:
            raise ValueError('Nagroda niedostępna')
        cost = r['cost']
        if r['unit_minutes']:
            if not minutes or not isinstance(minutes, int) or minutes <= 0:
                raise ValueError('Podaj liczbę minut (dodatnia liczba całkowita).')
            units = math.ceil(minutes / r['unit_minutes'])
            cost = units * r['cost']
        if self.summary(date.today().isoformat(), k)['balance'] < cost:
            raise ValueError('Za mało punktów')
        with self.con() as c:
            c.execute('INSERT INTO redemptions(child, cost, created) VALUES(?, ?, ?)',
                      (k, cost, date.today().isoformat()))
        return cost

    def history(self, k, limit=200):
        if k not in {child['id'] for child in KIDS}:
            raise ValueError('Nieznane dziecko')
        titles = {tid: t[0] for tid, t in all_task_defs().items()}
        events = []
        with self.con() as c:
            for r in c.execute('SELECT day, task FROM checks WHERE child=? AND checked=1', (k,)):
                events.append({'date': r['day'], 'label': titles.get(r['task'], r['task']),
                                'points': self._historic_points(r['task'])})
            for r in c.execute('SELECT created, cost FROM redemptions WHERE child=?', (k,)):
                events.append({'date': r['created'], 'label': 'Wymiana na nagrodę', 'points': -r['cost']})
        events.sort(key=lambda e: e['date'], reverse=True)
        return events[:limit]


store = FamilyPoints(DB_PATH)


@app.get('/')
def index():
    return render_template('index.html', kids=KIDS)


@app.get('/api/state')
def api_state():
    d = request.args.get('date', date.today().isoformat())
    return jsonify({
        'children': [{**k, 'tasks': store.tasks(d, k['id']), 'summary': store.summary(d, k['id'])} for k in KIDS],
        'rewards': store.rewards(),
    })


@app.get('/api/history')
def api_history():
    if request.args.get('pin', '') != PARENT_PIN:
        return jsonify({'error': 'Nieprawidłowy PIN rodzica'}), 403
    child = request.args.get('child', '')
    try:
        return jsonify({'events': store.history(child)})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.post('/api/toggle')
def api_toggle():
    b = request.get_json(force=True) or {}
    try:
        store.toggle(b['day'], b['child'], b['task'], b['checked'])
        return jsonify({'ok': True})
    except (KeyError, ValueError) as e:
        return jsonify({'error': str(e) or 'Błędne dane'}), 400


@app.post('/api/reward')
def api_reward():
    b = request.get_json(force=True) or {}
    try:
        if b.get('pin') != PARENT_PIN:
            raise ValueError('Nieprawidłowy PIN rodzica')
        store.add_reward(b.get('title', ''), b.get('cost'))
        return jsonify({'ok': True}), 201
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({'error': str(e) or 'Błędne dane'}), 400


@app.post('/api/redeem')
def api_redeem():
    b = request.get_json(force=True) or {}
    try:
        cost = store.redeem(b['child'], b['id'], b.get('minutes'))
        return jsonify({'ok': True, 'cost': cost})
    except (KeyError, ValueError) as e:
        return jsonify({'error': str(e) or 'Błędne dane'}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8088')))
