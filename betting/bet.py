#!/usr/bin/env python3

from colorama import Fore, Style
import sys
try:
	################################################################################
	# config
	################################################################################
	GROUP_NAMES = {'Live-Team' }
  # GROUP_NAMES = {'Africa and Arab', 'Northern Eurasia', 'Asia West', 'Asia Pacific', 'North America', 'Europe', 'South Pacific', 'Asia East', 'Latin America'}
	STATS_AS_BET = {'Medians', 'Averages'}
	PLOT_FILE = 'graph.html'
	CONFIG_FILE = '.config'
	BETS_PATH = './bets/'
	DEFAULT_NUMBER_OF_PROBLEMS = 4
	DEFAULT_REFRESH = 60.0
	MIN_NAME_WIDTH = 9
	NUMBER_OF_TEAMS_OVERRIDE = None

	################################################################################
	# read args
	################################################################################
	import argparse
	################################################################################
	parser = argparse.ArgumentParser(prog='NWERC Bet Script')
	parser.add_argument(
		'-r',
		'--refresh',
		help='refresh rate in seconds (for plot)',
		nargs='?',
		const=DEFAULT_REFRESH,
		type=float)
	parser.add_argument(
		'-o',
		'--offline',
		help='just print bet table',
		action='store_true')
	parser.add_argument(
		'-y',
		'--yes',
		help='yes to all options',
		action='store_true')
	args = parser.parse_args()

	################################################################################
	# read config
	################################################################################
	import questionary
	from questionary.constants import DEFAULT_STYLE
	from prompt_toolkit import print_formatted_text
	from prompt_toolkit.formatted_text import FormattedText
	################################################################################

	def print_selected(message, choice, mark='?'):
		tokens = []
		tokens += [('class:qmark', mark)]
		tokens += [('class:question', f' {message} ')]
		tokens += [('class:answer', choice)]
		print_formatted_text(FormattedText(tokens), style=DEFAULT_STYLE)

	################################################################################
	# read config
	################################################################################
	import yaml
	from pathlib import Path
	################################################################################

	if not args.offline:
		config = None
		config_file = Path(CONFIG_FILE)
		if config_file.exists():
			with config_file.open('r') as stream:
				config = yaml.safe_load(stream)
		if config is None:
			config = {}

		def safe_config():
			with config_file.open('w') as stream:
				yaml.safe_dump(config, stream)

		def ask_config(message, key, hidden=False):
			if args.yes and key in config:
				selected = config[key]
				if hidden:
					selected = '*' * len(selected)
				print_selected(message, selected)
			else:
				if hidden:
					config[key] = questionary.password(message, config[key] if key in config else '').unsafe_ask()
				else:
					config[key] = questionary.text(message, config[key] if key in config else '').unsafe_ask()
				safe_config()

		ask_config('API-URL?', 'url')
		ask_config('Username?', 'username')
		ask_config('Password?', 'password', True)

	################################################################################
	# util
	################################################################################
	import datetime
	from dateutil import parser
	################################################################################
	def parse_time(t):
		h, m, s = map(float, t.split(':'))
		return datetime.timedelta(hours=h, minutes=m, seconds=s)

	################################################################################
	# access Domjudge
	################################################################################
	import requests
	################################################################################

	if not args.offline:
		class Domjudge(requests.Session):
			def __init__(self, *args, **kwargs):
				super(Domjudge, self).__init__(*args, **kwargs)

			def request(self, method, url, **kwargs):
				return super(Domjudge, self).request(method, config['url'] + url, **kwargs)

		with Domjudge() as domjudge:
			print('connecting...',end='\r')
			domjudge.auth = (config['username'], config['password'])

			contests = domjudge.get(f'contests').json()
			contests = [questionary.Choice(f'{c["id"]:>3}: {c["name"]}', c['id']) for c in contests]
			if len(contests) == 0:
				print_selected('Contests found:', '0', '!')
				sys.exit(1)
			default = None
			if 'contest' in config:
				for contest in contests:
					if contest.value == config['contest']:
						default = contest
			if args.yes and 'contest' in config:
				print_selected('Contest?', config['contest'])
			else:
				config['contest'] = questionary.select('Contest?', contests, default).unsafe_ask()
				safe_config()

			print()
			print('loading...',end='\r')

			contest = domjudge.get(f'contests/{config["contest"]}').json()
			start_time = parser.parse(contest['start_time'])
			end_time = parser.parse(contest['end_time'])
			duration = parse_time(contest['duration'])

			groups = domjudge.get(f'contests/{config["contest"]}/groups').json()
			participants_group_ids = set()
			for group in groups:
				if group['name'] in GROUP_NAMES:
					participants_group_ids.add(group['id'])
			assert participants_group_ids

			active = domjudge.get(f'users').json()
			active = {u['team_id'] for u in active if u['first_login_time'] is not None}

			#teams = domjudge.get(f'contests/{config["contest"]}/teams?category={participants_group_id}').json()
			teams = domjudge.get(f'contests/{config["contest"]}/teams').json()
			teams = {t['id'] for t in teams if any(i in t['group_ids'] for i in participants_group_ids)}
			print_selected('Total teams found:', str(len(teams)), '!')
			print_selected('Active teams found:', str(len(teams)), '!')
			print('loading...',end='\r')
			teams = teams & active

			problems = domjudge.get(f'contests/{config["contest"]}/problems').json()
			problems.sort(key=lambda p: p['ordinal'])
			problem_names = [p['name'] for p in problems]
			print_selected('Problems found:', str(len(problems)), '!')
			if len(problems) == 0:
				sys.exit(1)
			for i, problem in enumerate(problems):
				assert i == problem['ordinal']
				id = chr(i + ord('A'))
				print(f'  {id}: {problem["name"]}')
			problems = {p['id'] : p['ordinal'] for p in problems}

			submissions = []
			def update_submissions():#does the domjudge instance stay alive? ^^''
				global submissions
				scoreboard = domjudge.get(f'contests/{config["contest"]}/scoreboard').json()
				
				for t in scoreboard['rows']:
					if t['team_id'] in teams:
						submissions += [
							{
								'problem_id' : s['problem_id'],
								'team_id' : t['team_id'],
								'contest_time' : start_time + datetime.timedelta(minutes=s['time'])
							}
							for s in t['problems']
							if s['solved']
							and s['problem_id'] in problems.keys()
							and datetime.timedelta(minutes=s['time']) < duration
						]

				submissions.sort(key=lambda s: s['contest_time'])

			update_submissions()
			print_selected('Accepted submissions found:', str(len(submissions)), '!')
	else:
		problems = range(0, int(questionary.text('Number of problems?', str(DEFAULT_NUMBER_OF_PROBLEMS)).unsafe_ask()))
		if len(problems) == 0:
			sys.exit(1)
		teams = []

	evaluate = len(teams) > 0

	################################################################################
	# read bets
	################################################################################
	import re
	import hashlib
	################################################################################

	float_pattern = re.compile(r'\d*(|\.\d*)')
	bet_path = Path(BETS_PATH)
	bets = {}
	for bet_file in bet_path.glob('[!.]*'):
		cur_bets = [None] * len(problems)
		ok = True
		with open(bet_file) as bet:
			for line in bet:
				parts = line.split()
				if len(parts) == 2 and parts[0].isupper() and len(parts[0]) == 1 and float_pattern.match(parts[1]):
					problem = ord(parts[0]) - ord('A')
					solved = float(parts[1])
					if 0 <= problem < len(problems):
						ok &= cur_bets[problem] == None
						cur_bets[problem] = solved
					else:
						ok = False
		for bet in cur_bets:
			ok &= bet is not None and 0.0 <= bet <= 100.0
		if ok:
			bets[bet_file.stem] = cur_bets
		else:
			print(f"Could not parse {bet_file.stem}'s bet! (skipping)")
	print_selected('Valid bets found:', str(len(bets)), '!')

	################################################################################
	# statistics
	################################################################################
	import statistics
	################################################################################

	columns = [[bet[i] for bet in bets.values()] for i in range(len(problems))]
	stats = {}
	if len(bets) > 0:
		stats['Averages'] = [statistics.mean(y) for y in columns]
		stats['Medians'] = [statistics.median(y) for y in columns]
		stats['Minimums'] = [min(y) for y in columns]
		stats['Maximums'] = [max(y) for y in columns]

	################################################################################
	# KL
	################################################################################
	import collections
	import math
	import numbers
	################################################################################

	if evaluate:
		def calculate_KL(results, bets):
			def KL_term(p, q):
				if q == 0:
					return 1e8
				if p == 0:
					return 0
				return min(999.99, p * math.log(p/q) / math.log(2))

			def KL_score(p, q):
				return KL_term(p/100.0, q/100.0) + KL_term(1-p/100.0, 1-q/100.0)

			assert len(results) == len(bets)
			return [KL_score(p,q) for p, q in zip(results, bets)]

		def update_scores():
			global solved
			global results
			global times
			global scores
			global stats_scores

			solved = [set() for _ in problems]
			results = [100.0] * len(problems)
			times = [start_time]
			scores = {name : [sum(calculate_KL(results, bet))] for name, bet in bets.items()}
			stats_scores = {name : [sum(calculate_KL(results, bet))] for name, bet in stats.items()}
			for submission in submissions:
				i = problems[submission['problem_id']]
				solved[i].add(submission['team_id'])

				num_teams = len(teams)
				num_solved = len(solved[i])
				if NUMBER_OF_TEAMS_OVERRIDE is not None:
					num_teams = NUMBER_OF_TEAMS_OVERRIDE
					num_solved = min(num_solved, num_teams)
				results[i] = (100.0 * (num_teams - num_solved)) / num_teams

				times.append(submission['contest_time'])
				for name, bet in bets.items():
					scores[name].append(sum(calculate_KL(results, bet)))
				for name, bet in stats.items():
					stats_scores[name].append(sum(calculate_KL(results, bet)))

			stats['Results'] = results

		update_scores()

		table = []
		for name, bet in bets.items():
			cur_scores = calculate_KL(results, bet)
			table.append((name, sum(cur_scores), cur_scores))
		for name, bet in stats.items():
			if name in STATS_AS_BET:
				cur_scores = calculate_KL(results, bet)
				table.append(('*' + name, sum(cur_scores), cur_scores))
		table.sort(key=lambda e: e[1])

	################################################################################
	# show bets
	################################################################################

	def show_bets():
		max_name = max(MIN_NAME_WIDTH, max([len(name) for name in bets], default=0))
		hash_length = 16 if len(bets) > 0 else 0
		print()
		print(' '*max_name, end='   ')
		for i in range(len(problems)):
			id = chr(i + ord('A'))
			print(f'      {id}', end=' ')
		print()
		print(Fore.BLACK, Style.BRIGHT, '-' * (max_name + 3 + hash_length + len(problems)*8), Style.RESET_ALL, sep='')

		if len(bets) > 0:
			for name, bet in bets.items():
				print(f' {name:>{max_name}}:', end='  ')
				hash = f'{name}'
				for x in bet:
					hash += f'|{x:6.2f}'
					print(f'{x:6.2f}', end='  ')
				hash =  hashlib.sha256(hash.encode()).hexdigest()
				print(f'  ({hash[-10:]})')
			print(Fore.BLACK, Style.BRIGHT, '-' * (max_name + 3 + hash_length + len(problems)*8), Style.RESET_ALL, sep='')

		for name, values in stats.items():
			print(f' {name:>{max_name}}:', end='  ')
			for value in values:
				print(f'{value:6.2f}', end='  ')
			print()
		print()

	show_bets()

	if not evaluate or len(bets) == 0:
		sys.exit(0)

	################################################################################
	# show scores
	################################################################################

	def show_scores():
		columns = [[s[i] for _, _, s in table] for i in range(len(problems))]
		stats = {}
		stats['Averages'] = [statistics.mean(y) for y in columns]
		stats['Medians'] = [statistics.median(y) for y in columns]
		stats['Minimums'] = [min(y) for y in columns]
		stats['Maximums'] = [max(y) for y in columns]

		print_selected('Winner:', table[0][0], '!')
		max_name = max(MIN_NAME_WIDTH, max([len(name) for name in bets], default=0))
		print()
		print(' '*max_name, end='   ')
		print('  score', end=' ')
		print('  worst', end=' ')
		for i in range(len(problems)):
			id = chr(i + ord('A'))
			print(f'      {id}', end=' ')
		print()
		print(Fore.BLACK, Style.BRIGHT, '-' * (max_name + 3 + 8 + 8 + len(problems)*8), Style.RESET_ALL, sep='')

		for name, score, cur_scores in table:
			print(f' {name:>{max_name}}:', end='  ')
			print(f'{score:6.2f}', end='  ')
			worst = max(cur_scores)
			print(f'{worst:6.2f}', end='  ')
			for i, s in enumerate(cur_scores):
				pref, suf = '', ''
				pref, suf = (pref, suf) if s != worst else (Fore.YELLOW, Style.RESET_ALL)
				#pref, suf = (pref, suf) if s != stats['Maximums'][i] else (Fore.RED, Style.RESET_ALL)
				pref, suf = (pref, suf) if s != stats['Minimums'][i] else (Fore.GREEN, Style.RESET_ALL)
				print(f'{pref}{s:6.2f}{suf}', end='  ')
			print()
		print(Fore.BLACK, Style.BRIGHT, '-' * (max_name + 3 + 8 + 8 + len(problems)*8), Style.RESET_ALL, sep='')

		for name, values in stats.items():
			print(f' {name:>{max_name}}:', end='  ')
			print(f'      ', end='  ')
			print(f'      ', end='  ')
			for value in values:
				print(f'{value:6.2f}', end='  ')
			print()
		print()

	show_scores()

	################################################################################
	# plot
	################################################################################
	from plotly import offline
	import plotly.graph_objs as go
	import webbrowser
	import time
	################################################################################

	def update_plot():
		plot_data = []
		def add_scores(name, bet):
			trace = go.Scatter(
				x=times,
				y=score,
				mode='lines',
				name=name
			)
			plot_data.append(trace)

		for name, score in scores.items():
			add_scores(name, score)
		for name, score in stats_scores.items():
			if name in STATS_AS_BET:
				add_scores(name, score)

		layout = go.Layout(
			#xaxis=dict(
			#	autorange=True
			#),
			xaxis_range=[start_time, end_time],
			yaxis=dict(
				type='log',
				autorange=True
			),
			hovermode='x'
		)
		figure = go.Figure(data=plot_data, layout=layout)
		offline.plot(figure, filename=PLOT_FILE, auto_open=False)

	update_plot()

	if questionary.confirm('show plot?', erase_when_done=True).unsafe_ask():
		webbrowser.open(Path(PLOT_FILE).absolute().as_uri())
	if args.refresh is not None:
		print('last refreshed:', datetime.datetime.now().strftime('%H:%M:%S'), end='\r')
		while True:
			time.sleep(args.refresh)
			print('last refreshed:', datetime.datetime.now().strftime('%H:%M:%S'), end='\r')
			update_submissions()
			update_scores()
			update_plot()

except KeyboardInterrupt:
	print(f'{Fore.RED}Aborted!{Style.RESET_ALL}')
