"""Render a contribution calendar with Python's standard library and GitHub CLI."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import subprocess

QUERY = '''{ user(login:"jeffkimkimo") { contributionsCollection {
  contributionCalendar { totalContributions weeks {
    contributionDays { date contributionCount }
  } }
} } }'''


def render(payload):
    if payload.get('errors'):
        raise ValueError('GitHub returned GraphQL errors')
    calendar = payload['data']['user']['contributionsCollection']['contributionCalendar']
    weeks = calendar['weeks']
    days = [d for w in weeks for d in w['contributionDays']]
    if not days:
        raise ValueError('Contribution calendar is empty')
    counts = [d['contributionCount'] for d in days]
    total = calendar['totalContributions']
    active = sum(c > 0 for c in counts)
    peak = max(counts)
    palette = ['#233341', '#31594f', '#4b8974', '#80baa0', '#f0b47c']
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="450" viewBox="0 0 1200 450" role="img" aria-labelledby="title desc">',
           '<title id="title">Jeffkim’s contribution reel</title>',
           f'<desc id="desc">GitHub contributions from {days[0]["date"]} to {days[-1]["date"]}: {total} contributions across {active} active days. Peak day: {peak} contributions. Brighter calendar squares indicate more daily contributions.</desc>',
           '<rect width="1200" height="450" rx="24" fill="#111b27"/>',
           '<path d="M28 58V28H58M1142 28H1172V58M28 392V422H58M1142 422H1172V392" fill="none" stroke="#a8d8c0" stroke-width="2"/>']

    def text(x, y, content, size=14, color='#a7b5be', extra=''):
        svg.append(f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" fill="{color}" {extra}>{escape(str(content))}</text>')

    text(60, 66, 'THE CONTRIBUTION REEL', 15, '#a8d8c0', 'letter-spacing="3"')
    text(60, 108, 'Small commits. A bigger picture.', 30, '#f5efdf', 'font-weight="700"')
    text(60, 140, f'{days[0]["date"]}  —  {days[-1]["date"]}', 14)
    for x, value, label, color in [(680, total, 'CONTRIBUTIONS', '#a8d8c0'), (860, active, 'ACTIVE DAYS', '#f5efdf'), (1030, peak, 'PEAK DAY', '#f0b47c')]:
        text(x, 103, f'{value:,}', 32, color, 'font-weight="700"')
        text(x, 132, label, 10, '#a7b5be', 'letter-spacing="1"')
    svg.append('<path d="M60 164H1140" stroke="#2b3b47"/>')
    pitch = min(19.5, 1030 / len(weeks))
    cell = pitch - 4
    start_x, start_y = 97, 211
    month_seen = None
    last_label = -10
    for column, week in enumerate(weeks):
        for day in week['contributionDays']:
            dt = date.fromisoformat(day['date'])
            row = (dt.weekday() + 1) % 7
            x, y = start_x + column * pitch, start_y + row * 20
            count = day['contributionCount']
            level = 0 if count == 0 else min(4, 1 + int(3 * count / max(peak, 1)))
            svg.append(f'<rect x="{x:.1f}" y="{y}" width="{cell:.1f}" height="16" rx="4" fill="{palette[level]}"><title>{day["date"]}: {count} contributions</title></rect>')
            month = (dt.year, dt.month)
            if month != month_seen:
                if column - last_label >= 3:
                    text(round(x, 1), 196, dt.strftime('%b'), 11)
                    last_label = column
                month_seen = month
    for row, label in [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]:
        text(60, start_y + row * 20 + 12, label, 11)
    text(60, 395, 'ONE FRAME AT A TIME.', 12, '#a8d8c0', 'letter-spacing="2"')
    text(775, 395, 'Less', 12)
    for i, color in enumerate(palette):
        svg.append(f'<rect x="{817 + i * 23}" y="382" width="16" height="16" rx="4" fill="{color}"/>')
    text(941, 395, 'More', 12)
    text(1030, 395, 'DAILY ACTIVITY', 10)
    svg.append('</svg>')
    return '\n'.join(svg) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, help='Use an existing GitHub GraphQL JSON response')
    args = parser.parse_args()
    raw = args.input.read_text() if args.input else subprocess.check_output(
        ['gh', 'api', 'graphql', '-f', f'query={QUERY}'], text=True, timeout=60)
    output = render(json.loads(raw))
    target = Path(__file__).resolve().parents[1] / 'assets' / 'contributions.svg'
    target.write_text(output)
    print(f'Generated {target.name}')


if __name__ == '__main__':
    main()
