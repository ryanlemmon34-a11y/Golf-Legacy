"""The rules of the world in words, versioned: how golfers get into fields, keep and earn tour cards, and
which amateur and college golf they may play. Text only -- the rules themselves live in the code that
applies them (season, cards, careers, qualification); this module is what the observer shows and links to.

Every archived season records the RULES_VERSION it was played under (seasons archived before versions
were recorded have none: the observer says so rather than assuming today's rules applied). A rule's
`since` is the version that introduced or last changed it.

`explain(route)` turns a recorded entry route (the code kept for every start, e.g. 'PREMIER CONDITIONAL',
'ORDER OF MERIT 12', 'U5') into (rule id, a short readable sentence). The original code is always kept
beside it.
"""
from __future__ import annotations

import re

RULES_VERSION = '2026-10-30'
VERSIONS = (
    ('2026-10-30', 'Winners\' exemptions count whatever a golfer\'s membership (a non-member champion earns a '
                   'Premier card and exempt entry); open amateur golf follows where an amateur lives as well as '
                   'nationality; the college eligibility ledger; round scores, conditions and each golfer\'s prize '
                   'money recorded for every event.'),
)
EARLIER = ('Seasons archived before rules versions were recorded were played under earlier rules. The '
           'differences that matter for reading old results: a winner without a Premier card held no '
           'exemption into Premier fields and could not earn a card by winning; amateur circuits followed '
           'nationality only.')

# id -> (title, text, since). Titles are short; texts say exactly what the code does.
RULES = {
    'premier-rights': (
        'Premier Tour playing rights',
        'Fixed on 1 January for every Premier member, in this priority order for Premier events: exempt (won a '
        'major in the last five seasons or a Premier event in the last two), full (top 125 of last season\'s '
        'Premier money list), graduate (earned the card on a Challenger tour or at Q-School), conditional '
        '(everyone else who kept a card). Within a class, members of the event\'s own circuit go first. Exempt '
        'and full members are ordered by world ranking, graduates and conditional members by this season\'s '
        'Premier money (a reshuffle). A win during the season makes a member exempt from that week on.',
        '2026-10-30'),
    'winner-exemption': (
        'Winners\' exemptions',
        'A major in the last five seasons or a Premier event in the last two (this season\'s wins included, from '
        'the week they are won) is an exemption whatever the winner\'s membership. A professional holding one '
        'without a Premier card enters Premier events as exempt (after exempt members of the event\'s own '
        'circuit, alongside exempt members of other circuits), and may still play their own tour\'s events.',
        '2026-10-30'),
    'premier-cards': (
        'Premier Tour cards',
        'At the end of each season: the top 200 of the Premier money list (all Premier events and majors) and '
        'exempt winners keep their cards; everyone else drops to their region\'s Challenger tour. Promoted: '
        'Challenger Tour Americas top 25, Europe top 20, Asia and Japan top 8, Latin America and Canada top 5; '
        'Premier Q-School final top 5 and ties; Europe Q-School top 20. A full-time professional without a card '
        'earns one with a winner\'s exemption, or with Premier money above the last member to keep a card, and '
        'joins the Premier circuit their home Challenger tour promotes to. An amateur holding a winner\'s '
        'exemption (an amateur major champion) who turns professional starts on that circuit. Part-time '
        'professionals are not carded. The top 10 on Premier Tour Europe and top 5 on Asia-Pacific move to '
        'Americas (a fixed hierarchy, not a choice).',
        '2026-10-30'),
    'lower-cards': (
        'Challenger, Regional and Mini tour cards',
        'Challenger tours keep their best members by money list, enough to stay at full size (at least half), '
        'and take each Regional tour\'s top 8, each Mini tour\'s top 4, Q-School graduates and players losing '
        'Premier cards. Regional tours keep at least 60% and take each Mini tour\'s next 6. Mini tours are open. '
        'Home tours follow nationality.',
        None),
    'tour-member': (
        'Tour members',
        'Members of the event\'s own tour enter first, in order of world ranking (Mini tours: by a fair draw).',
        None),
    'other-member': (
        'Members of other tours',
        'Professionals from other tours fill places the event\'s members leave: those from a higher tour first, '
        'then the same level, then lower, by world ranking.',
        None),
    'visitor-places': (
        'Premier members in Challenger events',
        'A Challenger event keeps up to 10% of its places for visiting Premier members (by world ranking); '
        'national opens are open to all professionals.',
        None),
    'home-player': (
        'National opens',
        'Professionals from the host country enter a national open ahead of other non-members.',
        None),
    'amateur-invitation': (
        'Amateur invitations',
        'Amateurs may take a few sponsor\'s invitations in professional events (Premier 4, other tours 8), by '
        'amateur ranking, after the professionals entitled to a place.',
        None),
    'college-lineup': (
        'College lineups',
        'College golfers play their college events like a team lineup: fewest starts this season first, with '
        'ranking worth a head start of a few starts, so the best play most and newcomers still get starts.',
        None),
    'open-amateur': (
        'Open amateur events',
        'Ordinary amateur events of a circuit are open to the circuit\'s members, amateurs of its countries, '
        'amateurs living in its countries, and college golfers studying there (up to 1.5 times the usual field '
        'when more want to play).',
        '2026-10-30'),
    'amateur-home-circuit': (
        'An amateur\'s home circuit',
        'An amateur\'s home circuit is the one where they live: a graduate who stays where they studied keeps '
        'playing amateur golf there, and one who moves takes up the circuit of their new home. Nationality '
        'still opens their own country\'s circuit, and national championships follow nationality only.',
        '2026-10-30'),
    'national-amateur': (
        'National amateur championships',
        'Amateurs of the host nation by amateur ranking, then up to a quarter of the field from the rest of its '
        'region. Nationality decides, never residence.',
        None),
    'elite-amateur': (
        'Elite amateur events',
        'Invited by world amateur ranking (unranked amateurs by observed form), within the event\'s regions where '
        'it has them; the Mid-Amateur needs age 25 or over.',
        None),
    'usa-amateur': (
        'USA Amateur',
        'Exempt: the last three champions and last year\'s runner-up (still amateurs), then the top 64 of the '
        'amateur ranking. Then open qualifying for amateurs with three starts this season who play North '
        'American amateur golf (living there or at college there) or are world amateur top 300; places by a fair '
        'draw, split across the sites, then to each site\'s best finishers.',
        None),
    'circuit-championship': (
        'Circuit championships',
        'Each circuit\'s season-ending championship: its champions of recent editions still on the circuit, then '
        'its order of merit as it stood the week before.',
        None),
    'major-qualification': (
        'Major championship qualification',
        'Each major\'s published exemption categories, then its qualifying and alternates (the route code is the '
        'category: M = Tour Masters, P = Premier Tour Championship, U = USA Open, B = Britannia Open).',
        None),
    'premier-finals': (
        'Premier Tour Finals',
        'The leaders of the season\'s Premier points list (Premier money) as it stood the week before.',
        None),
    'q-school': (
        'Q-School',
        'Open to professionals who enter and can pay; later stages from the earlier stages\' leading finishers.',
        None),
    'qualifying': (
        'Qualifying events',
        'Open qualifiers: entrants choose to enter and pay their own way; leading finishers go on to the event.',
        None),
    'college-postseason': (
        'College post-season',
        'Conference and regional championships and the national championship, selected from college golfers by '
        'ranking and results; the school pays.',
        None),
    'club-pro': (
        'Club professionals',
        'Club professionals play their region\'s section events; the national championship is reached through '
        'sectional qualifying.',
        None),
    'late-entry': (
        'Late entries',
        'A place left open after everyone had chosen, taken by a golfer for whom the event was below their first '
        'preference.',
        None),
    'college-eligibility': (
        'College eligibility (Golf Legacy ruleset 1)',
        'A golfer may play college golf in every season from enrolment through the season in which they turn 22 '
        '(age by birth year), so at most five seasons for an 18-year-old entrant. Each season enrolled is '
        'recorded once in the eligibility ledger. No redshirt, waiver or transfer exceptions. A fictional rule: '
        'close to the NCAA\'s age-based five-year window, not its older four-seasons-in-five rule.',
        '2026-10-30'),
}

_PREMIER_RIGHTS = {
    'EXEMPT': 'Premier member, exempt (a recent major or Premier win)',
    'FULL': 'Premier member with full status (top 125 of last season\'s Premier money list)',
    'GRADUATE': 'Premier member who earned the card on a Challenger tour or at Q-School',
    'CONDITIONAL': 'Premier member with conditional status (after better-status members, by this season\'s money)',
    'MEMBER': 'Premier member',
}
_FIXED = {
    'WINNER EXEMPTION (not a member)': ('winner-exemption', 'A winner\'s exemption, held without a Premier card'),
    'PREMIER MEMBER (visitor places)': ('visitor-places', 'A Premier member in one of the places kept for visitors'),
    'AMATEUR INVITATION': ('amateur-invitation', 'An amateur on a sponsor\'s invitation'),
    'COLLEGE LINEUP': ('college-lineup', 'Picked for their college\'s lineup'),
    'OPEN AMATEUR ENTRY': ('open-amateur', 'Open entry to an amateur event of their circuit'),
    'CLUB PROFESSIONAL': ('club-pro', 'A club professional of the circuit\'s region'),
    'MEMBER': ('tour-member', 'A member of the event\'s tour'),
    'MEMBER (draw)': ('tour-member', 'A member of the mini tour (places by a fair draw)'),
    'HOME PLAYER': ('home-player', 'A professional from the host country'),
    'AMATEUR (unranked, by form)': ('elite-amateur', 'Invited on observed form (no amateur ranking)'),
    'PAST CHAMPION': ('circuit-championship', 'A past champion of this championship still on the circuit'),
    'OPEN QUALIFYING ENTRY': ('usa-amateur', 'Entered open qualifying'),
    'ENTRY': ('club-pro', 'Entered sectional qualifying'),
    'COLLEGE POST-SEASON': ('college-postseason', 'Selected for the college post-season'),
    'Q-SCHOOL ENTRY': ('q-school', 'Entered Q-School'),
    'PREMIER POINTS LIST': ('premier-finals', 'Qualified on the Premier points list'),
    'QUALIFYING ENTRY': ('qualifying', 'Entered the qualifier'),
    'SELECTED': ('qualifying', 'Selected by the event'),
    'ALT': ('major-qualification', 'An alternate, replacing a qualified player who withdrew'),
    'INIT': ('major-qualification', 'Inaugural invitation (the world\'s first Tour Masters, by world ranking)'),
}
_PATTERNS = (
    (re.compile(r'^AMATEUR RANKING (\d+)$'), 'elite-amateur', 'Selected by world amateur ranking (No. {0})'),
    (re.compile(r'^HOME AMATEUR \(amateur ranking (\d+)\)$'), 'national-amateur',
     'An amateur of the host nation (amateur ranking {0})'),
    (re.compile(r'^HOME AMATEUR \(unranked\)$'), 'national-amateur', 'An amateur of the host nation (unranked)'),
    (re.compile(r'^REGIONAL AMATEUR \(amateur ranking (\d+)\)$'), 'national-amateur',
     'An amateur from the host nation\'s region (amateur ranking {0})'),
    (re.compile(r'^REGIONAL AMATEUR \(unranked\)$'), 'national-amateur', 'An amateur from the host nation\'s region (unranked)'),
    (re.compile(r'^ORDER OF MERIT (\d+)$'), 'circuit-championship', 'No. {0} on the circuit\'s order of merit'),
    (re.compile(r'^USA AMATEUR CHAMPION (\d+)$'), 'usa-amateur', 'Exempt as the {0} USA Amateur champion'),
    (re.compile(r'^RUNNER-UP (\d+)$'), 'usa-amateur', 'Exempt as the {0} USA Amateur runner-up'),
    (re.compile(r'^QUALIFYING SITE (\d+) \(alternate\)$'), 'usa-amateur', 'Qualified at site {0} (as an alternate)'),
    (re.compile(r'^QUALIFYING SITE (\d+)$'), 'usa-amateur', 'Qualified at site {0}'),
    (re.compile(r'^SECTIONAL (\d+)$'), 'club-pro', 'Qualified at sectional {0}'),
)
_MAJOR_CODE = re.compile(r'^([MPUB]\d+|UQ|UF|BQ|BF|PF|BQ_[A-Z_]+)$')


def _major_labels():
    from .qualification import RULES as MAJOR_RULES
    return {r.code: r.label for routes in MAJOR_RULES.values() for r in routes}


_labels = None


def explain(route):
    """(rule id, readable text) for a recorded entry route; (None, None) if it is not recognised (the code
    is then shown as it is)."""
    global _labels
    if not route:
        return None, None
    late = route.endswith(' — late entry')
    base = route[:-len(' — late entry')] if late else route
    rule, text = _explain(base)
    if late and text:
        text += ' — a late entry'
    return rule, text


def _explain(r):
    global _labels
    if r in _FIXED:
        return _FIXED[r]
    if r.startswith('PREMIER ') and r[8:] in _PREMIER_RIGHTS:
        return 'premier-rights', _PREMIER_RIGHTS[r[8:]]
    for pat, rule, text in _PATTERNS:
        m = pat.match(r)
        if m:
            return rule, text.format(*m.groups())
    if _MAJOR_CODE.match(r):
        if _labels is None:
            _labels = _major_labels()
        if r in _labels:
            return 'major-qualification', _labels[r]
    if r.endswith(' MEMBER'):
        return 'other-member', f'A member of the {r[:-7].title()}'
    return None, None
