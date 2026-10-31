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

RULES_VERSION = '2026-11-11'
RANKING_RULE = 'world-ranking-1'     # the world ranking's formula (unchanged since the world began; named now)
VERSIONS = (
    ('2026-10-30', 'Winners\' exemptions count whatever a golfer\'s membership (a non-member champion earns a '
                   'Premier card and exempt entry); open amateur golf follows where an amateur lives as well as '
                   'nationality; the college eligibility ledger; round scores, conditions and each golfer\'s prize '
                   'money recorded for every event; golf statistics (driving, greens, putting...), each start\'s world '
                   'ranking points, weekly ranking averages and match-play results recorded.'),
    ('2026-10-31', 'Calendar versions: new worlds play the reference calendar (v2: majors in weeks 15, 20, 25 and 30, '
                   'qualifying waves with one attempt, cut-offs read from immutable snapshots, amateur titles routed '
                   'to the edition their date allows, the annual amateur award after the USA Amateur, Asian Q-School '
                   'in week 51, day-level travel between events in one week); worlds started earlier keep the '
                   'classic calendar (v1) unchanged. A ledger of every major place (earned, used or lost) and each '
                   'golfer\'s highest Overall are recorded.'),
    ('2026-11-01', 'USA Open champions keep their place for the ten editions after their win, through the tenth '
                   'anniversary (it had ended a year early, after the ninth). An earned major place is never lost '
                   'for money alone: when the golfer cannot pay the trip, the organizer pays its travel and entry, '
                   'in kind (the caddie\'s week stays the golfer\'s). Each major place records the money it was '
                   'decided on.'),
    ('2026-11-02', 'An injury announced as n weeks keeps the golfer out of exactly n weeks of entries (it had kept '
                   'them out one week longer). The world\'s first Tour Masters invitations are covered by the '
                   'major-trip guarantee, as earned places and called-up alternates are. Amateur support: amateurs '
                   'who show success have their golf costs (events, a caddie, a coach) paid in kind up to a season '
                   'cap by band. Coaches\' teaching and scouting and every golfer\'s Prestige are recorded.'),
    ('2026-11-03', 'The other majors\' champions (five) and the Players Championship winners (three) hold the most '
                   'recent editions as of the field, this season\'s included only when it is played before the field '
                   '(it had been one edition more). The work pathway: a full-time adult amateur outside the top 300, '
                   'without support or family money, who cannot afford any eligible event for eight counted weeks '
                   'takes a job at the next monthly plan and keeps playing as a working amateur.'),
    ('2026-11-04', 'Recruitment of coaches and caddies is two-way: a scout\'s assessment of a young player firms up '
                   'with the seasons they have watched them; development coaches and coaches of established players '
                   'look for different players, and coaches of established players and caddies without a bag make '
                   'offers themselves; golfers, coaches and caddies may each turn an approach down; a '
                   'working partnership\'s loyalty (rapport, fit, results together) weighs against a better-known '
                   'offer. Approach, acceptance, refusal and departure reasons are recorded. A caddie\'s reputation '
                   '(and so their fee) follows the season of the bag they carry as the season ends, before the '
                   'winter\'s career decisions (it had moved after them), so a golfer judged able to pay their own '
                   'way is judged on next season\'s caddie fee; every such decision keeps the figures it used.'),
    ('2026-11-05', 'Five-year prestige: event prestige reads the last five calendar years, recency-weighted, with '
                   'a limit on how far it moves in a year (it had been the last four editions); courses have a '
                   'prestige of their own from the events they hosted in completed seasons, and an event that has '
                   'outgrown its venue for three seasons moves to a better course in its city two seasons later; '
                   'nations have a '
                   'prestige from success beyond pre-event expectation, which sets their share of each year\'s new '
                   'juniors and new professionals. The number of new golfers is unchanged by it: only how the '
                   'fixed number is shared between nations.'),
    ('2026-11-06', 'A working amateur can return to full-time amateur golf in the winter when their finances and '
                   'results support it: a full season in work, no debt, savings covering a full-time amateur season '
                   'of golf, and results worth going back for; the chance falls smoothly with age (no cut-off).'),
    ('2026-11-07', 'Death after retirement: in the winter after each season, anyone who is not an active competitive '
                   'golfer -- a golfer retired from competition (including one who coaches or caddies), or a coach '
                   'or caddie -- may die, at an annual risk rising with age (a provisional game calibration). A '
                   'working coach\'s or caddie\'s partnerships end then, with the reason recorded; results, records '
                   'and relationships are kept. Worlds started earlier never process deaths.'),
    ('2026-11-08', 'Course familiarity has a regional baseline: a golfer plays a course in the state or province where '
                   'they were born or live (the country, where the state or province is unknown) as if they had played '
                   'a few rounds there, unless they have played more; it is a floor, never added to experience, and '
                   'counted once. Every golfer has a recorded home club where they live, which counts the same way. '
                   'Local hosting: a low- or entry-level event playing in a city for the first time takes a free '
                   'municipal course no event has used yet, and keeps it; established venues are unchanged. Each '
                   'course records its state or province, and each season the starts where the baseline applied. '
                   'Aggression, an existing personality trait, is shown on profiles (unchanged in play).'),
    ('2026-11-09', 'Seasonal weather: each round\'s wind and wetness come from the course\'s climate and the time of '
                   'year (opposite seasons in the two hemispheres, coastal exposure, course style), with a wind '
                   'direction played against each hole\'s line (head, tail or cross) and gusts varying it shot by '
                   'shot. Wet rounds play differently '
                   'but are never cancelled, shortened or delayed. A playoff is played in the final round\'s '
                   'weather. Each round\'s wind direction and gustiness are recorded with its conditions. Worlds started earlier '
                   'keep the classic weather.'),
    ('2026-11-11', 'College amateurs in open amateur golf at home: in an ordinary open amateur event (the regular '
                   'events of a regional amateur series) a college golfer whose home region -- where they live, their '
                   'college base while at college -- is the series\' region enters at the same class as the series\' '
                   'members, and members and these college golfers rotate by their amateur (tier 6) starts this '
                   'season, not every start, so college events do not push a college golfer back; ranking keeps its '
                   'head start of a few starts. Unchanged: circuit, national and elite amateur championships and '
                   'qualifying, college events, professional events, college golfers from outside the region, '
                   'eligibility, field sizes (up to 1.5 times the usual field) and the calendar; no place is '
                   'reserved or guaranteed, and members can lose places in full fields. Worlds started earlier keep '
                   'the previous order.'),
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
        'when more want to play). Members enter first; college golfers living in the circuit\'s region enter '
        'with them, at the same class, and the two rotate by amateur (tier 6) starts this season, fewest first, '
        'with amateur ranking worth a head start of a few starts (college events do not count). Everyone else '
        'follows by class as before, by starts of every kind. Worlds started before rules 2026-11-11 put college '
        'golfers after the members and rotated by every start.',
        '2026-11-11'),
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
        'category: M = Tour Masters, P = Premier Tour Championship, U = USA Open, B = Britannia Open). Under the '
        'reference calendar (v2) a place is one place however many categories support it; every place is kept in '
        'the rights ledger with its evidence (the edition and result, ranking or award it came from, when it was '
        'earned) and how it ended: entered, withdrawn (injured or retired), declined (could not pay the trip: only '
        'before rules 2026-11-01) or expired (an amateur\'s place after turning professional). Since 2026-11-01 a '
        'golfer with an earned place who cannot pay the trip has its travel and entry paid by the organizer, in '
        'kind; injury, retirement and an expired amateur place still end a place, and qualifying stages and other '
        'events are paid as usual; the same holds for an alternate called up and, in the world\'s first season, '
        'for a Tour Masters invitation from the seeded world ranking (route INIT). Champion and runner-up places '
        'are separate '
        'categories; an amateur title feeds the next edition its date allows (the Britannia Amateur, after the '
        'USA Open, feeds next season\'s USA Open and Masters but this season\'s Britannia Open). USA Open champions '
        'hold their place for the ten editions after their win (U1). Under the reference calendar the other '
        'majors\' champions "last 5 years" (P2, U5, B3) and the Players Championship winners "last 3 years" (M3, P3, '
        'U6, B4) hold the five (three) most recent editions as of the field: this season\'s edition is one of them '
        'only when it is played before the field (before rules 2026-11-03 it was one more, the current edition and '
        'five or three before it).',
        '2026-11-03'),
    'calendar': (
        'The calendar',
        'Each world plays one calendar version, recorded with every season. Classic (v1): majors in weeks 18, 24, '
        '25 and 30. Reference (v2, new worlds): majors in weeks 15, 20, 25 and 30, five weeks apart; Premier '
        'opportunity events in the week after each; 36 Premier events (8 flagship, 20 standard, 8 opportunity) '
        'at their reference weeks; club professionals\' sectionals in week 12 and championship in week 18; USA '
        'Open local waves in weeks 17, 19 and 21 (each applicant chooses one: one attempt), international final '
        'qualifying in week 22 (direct entries only) and domestic final in week 24; Britannia regional waves in '
        'weeks 26 and 27 (one attempt across them), final qualifying week 28, Scotland Open week 29; the season\'s '
        'leading amateur after the USA Amateur (week 33) is named in week 34 and holds places in next season\'s '
        'USA and Britannia Opens while still an amateur; Asian Challenger Q-School in week 51 for next season\'s '
        'cards. Ranking cut-offs are the lists published after their week (Masters 13, Premier Tour Championship '
        '18, USA Open 20 and 24, Britannia Open 21), never a later or earlier one. A golfer can play two events in '
        'one week only if the days do not overlap and there is time to travel: none within a country, a free day '
        'within a region, two between regions.',
        '2026-10-31'),
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
    'world-ranking': (
        'World ranking (world-ranking-1)',
        'Every start in a professional event -- majors, Premier, Challenger, Regional and Mini tour events; not '
        'qualifying stages, amateur, college or club-professional events -- earns points: 100 x ((the event\'s '
        'prestige when played - 20) / 80) ^ 2.2 (nothing below prestige 20), times the finish\'s share: 1 for a '
        'win, 0.6 x (position - 1) ^ -0.73 for second to 60th (tied golfers each take their shared position\'s share), '
        'nothing beyond 60th or for a missed cut. Points count for 104 weeks: in full for 13 weeks, then falling '
        'in a straight line to nothing. The ranking average is the weighted total divided by the number of '
        'starts in those 104 weeks (zero-point starts included), but by at least 40 and at most 52. Recomputed '
        'every week. Amateurs earn world points in these events too. The world\'s first two seasons also carry '
        'points seeded from each golfer\'s standing when the world began. Not today\'s official ranking: no '
        'separate field-strength formula beyond prestige.',
        '2026-10-30'),
    'golf-statistics': (
        'Golf statistics (definitions version 1)',
        'Counted from every simulated shot in completed 18-hole stroke-play rounds (match-play and playoff holes '
        'are not rounds). Driving distance: the first tee shot on each par 4 and 5 hit with a driver, carry and '
        'roll to where it finished, misses included. Fairways hit: first tee shots on par 4s and 5s finishing '
        'on the fairway (a fairway bunker or a driven green is not the fairway). Greens in regulation: on the '
        'putting surface in par - 2 strokes or fewer, penalties included (the fringe is not the green), or holed '
        'from off the green that soon (an ace, a holed approach: no putts). '
        'Scrambling: par or better after missing the green in regulation. Sand saves: up and down from a '
        'greenside bunker. Putts: strokes on the putting surface (not from the fringe). Scoring average: raw '
        'strokes per round, not adjusted. Strokes gained: against the engine\'s own expected-strokes table, '
        'not a validated real-world baseline. Season, career and tour figures add up the counts and the '
        'opportunities (never averages of averages); seasons before this version show "not recorded".',
        '2026-10-30'),
    'amateur-support': (
        'Amateur support',
        'Amateurs who show success have their golf costs paid in kind -- event travel and entry, a caddie\'s weekly '
        'fee and a coach\'s fee -- up to a season cap: Band A $25,000 (amateur ranking 1-10; last season\'s USA '
        'Amateur or Britannia Amateur champion or annual amateur award; a top-25 finish in a major as an amateur), '
        'Band B $12,000 (ranking 11-50; an earned major place this season; a continental amateur title or the USA '
        'Mid-Amateur), Band C $5,000 (ranking 51-150; or among the 150 amateurs with the most ranking points won in '
        'the last 26 weeks). Never cash, living costs or moving; unused support lapses at the season\'s end. The '
        'budget opens in week 1; a new Band A or B achievement raises it from the next week, and it is never cut '
        'during a season. Each winter the band is what the facts give but at most one band below the one held '
        '(A, B, C, none). It ends on turning professional or retiring. A school or club pays its own events first, '
        'then the support, then the golfer; the organizer pays a major trip only when the two cannot. Starting '
        'values to test, not proven amounts.',
        '2026-11-02'),
    'work-pathway': (
        'Work pathway for cash-blocked amateurs',
        'A full-time amateur outside college, aged 21 or over, outside the amateur ranking\'s top 300 (or unranked), '
        'with no amateur support and no family money left, who could not afford any event they were eligible for '
        'in 8 counted weeks takes a job at the next monthly plan and keeps playing as an amateur alongside it (the '
        'salary, living costs and schedule of every working amateur). A week counts when there was an eligible '
        'event and not one was affordable; an injury, a week with no suitable event and a week with nothing they '
        'were eligible for neither count nor reset; any week they could pay for an event starts the count again. '
        'Nobody is given money and no cost is waived; the way back to full-time golf is turning professional, as '
        'for every working amateur.',
        '2026-11-03'),
    'mortality': (
        'Death after retirement',
        'An active competitive golfer never dies. Everyone else -- a golfer retired from competition (whether or '
        'not they went on to coach or caddie), and every coach and caddie, working or retired -- may die in the '
        'winter after a season. Deaths are processed once per season on one date, the winter after season Y, '
        'after the season\'s career decisions, the staff\'s retirements and the ending of the relationships of '
        'those who left, and before outside recruits are hired. A death is recorded as "the winter after season '
        'Y" with the age then (the season\'s year minus the birth year, approximate like every age in the world), '
        'and that age is kept for good. No date inside a completed season is ever drawn, so no death is dated '
        'before anything the person did. The annual risk at age a is 0.0005 + 0.000041 x e^(0.09 a), at most '
        '50 % (about 0.9 % at 60, 2.2 % at 70, 5.5 % at 80, 13.5 % at 90, 33 % at 100), the same for every '
        'nation: a provisional game calibration, not a validated demographic fact. Each person\'s chance is '
        'settled by a draw of their own for that season (from the world\'s seed, the season and the person), so '
        'it moves nothing else in the world and is the same after a save and resume; a season is never processed '
        'twice. A golfer who became a coach or caddie is one person: they die once, and every record of them '
        'says so. A coach\'s or caddie\'s open partnerships end that winter ("coach died" / "caddie died") and '
        'they stop working; outside recruits fill the gap as for any vacancy. Results, records, relationships '
        'and profiles are kept. Worlds started before this rule never process deaths, and no past death is '
        'invented: people already old when a world begins are processed from its first season\'s end.',
        '2026-11-07'),
    'event-prestige': (
        'Event prestige (five calendar years)',
        'An event\'s prestige (0-100) is 35% its tour\'s standing, 30% its field (the best 30 entrants by world '
        'ranking -- amateur ranking for amateur events -- as ranked the week it was played), 20% its purse (log '
        'scale) and 15% its course\'s physical class and layout. Each factor is averaged over this calendar year '
        'and the four before, weighted 1.0, 0.9, 0.8, 0.7 and 0.6 by age; a year without an edition is left out '
        'and the others reweighted. It is updated after each edition and moves at most 6 points in a calendar '
        'year either way. A new world assumes the four years before its first season were played at each '
        'event\'s expected starting factors; one assumed year leaves the window each season. Qualifying stages '
        'keep their starting prestige. Before rules 2026-11-05: the plain average of the last four editions, '
        'with no yearly limit.',
        '2026-11-05'),
    'course-prestige': (
        'Course prestige',
        'A course\'s prestige is separate from its physical class and layout (which alone count in event '
        'prestige, so a venue\'s prestige never feeds back into its events). At each season\'s end it is set '
        'for the next season from the five completed seasons before it: for each season in which the course '
        'hosted an event, the highest prestige (as played) of the events it hosted, averaged with weights 1.0, '
        '0.9, 0.8, 0.7 and 0.6 by age; it moves at most 10 points from one season to the next, and a course '
        'that hosted nothing in those five seasons loses 10% of its prestige a season. A new world assumes the '
        'four seasons before it hosted what its first season\'s schedule gives it. Courses that have hosted '
        'nothing have none.',
        '2026-11-05'),
    'venue-moves': (
        'Better venues for events that outgrow theirs',
        'Every edition is played where the course plan puts it unless the event has moved. At each season\'s end, '
        'a single-site event (not a major, not a qualifying stage) whose prestige has been at least 5 points above '
        'its venue\'s course prestige at three consecutive season ends, and which has not moved in the last ten '
        'seasons, moves to the physically best other course in the same city that its level may use, that is '
        'physically better than its current one and free that week (never an elite course in a major\'s week), '
        'from the season after next; ties by course prestige, then course id. If none qualifies it stays. The move '
        'applies whenever the event is planned on the course it replaced; a year in which the new course is '
        'already booked that week it plays the planned course. Each edition records the venue actually used.',
        '2026-11-05'),
    'nation-shares': (
        'National prestige and shares of new golfers',
        'The number of new juniors (18) and new professionals (21-26) each year is what the existing rule '
        'creates from the nations as the world began, with the same random draws: prestige never adds or removes '
        'a golfer. That number is split between nations by share (largest remainders; ties by the larger quota, '
        'then the name), and each nation draws candidates from its own unchanged talent distribution until '
        'exactly its number has passed the pathway\'s usual filter; nobody\'s nationality ever changes. A '
        'nation\'s share is its starting share (its expected share under the existing rule) times its '
        'participation multiplier, normalised to 100%. The multiplier follows national prestige: in every event '
        'except qualifying stages each starter earns the fame points of their finish, and is expected, before '
        'the event, to take half of an equal share of the fame the event hands out plus half by current Overall '
        '(softmax, 4 points per e-fold). Over the last five completed seasons (weights 1.0 to 0.6 by age), '
        'R = (actual + 150) / (expected + 150), prestige = 50 + 25 x log2 R within 0-100, and the multiplier '
        'moves toward 4 ^ ((prestige - 50) / 50) -- between 0.25 and 4 -- by at most 10% a year. Set at each '
        'season\'s end for the next season\'s entrants.',
        '2026-11-05'),
    'amateur-return': (
        'Returning from work to full-time amateur golf',
        'Each winter a working (part-time) amateur outside college who did not turn professional may return to '
        'full-time amateur golf, if all three hold: at least one full season in work since taking the job (a job '
        'taken during a season counts from the next); no debt, and savings plus family money covering a full-time '
        'amateur season of golf (16 events at their own average trip cost last season, or a regional amateur trip '
        'when they played too few to tell; support and salary do not count); and results in the season just ended '
        '(amateur ranking inside the top 300, a win or top-3 finish, or a rise of 100 places). Then it is a chance, '
        'never certain: higher with stronger results, more savings and more drive, lower with age from 23 with no '
        'age excluded, at most 60 % a year. Provisional calibration (owner decision D5, thresholds D5a).',
        '2026-11-06'),
    'staff-recruitment': (
        'Coaches and caddies: recruitment',
        'Before each season. Scouting: each coach with room for a share deal looks at up to 60 players aged 23 and '
        'under near them -- up to 20 promising players they watched in earlier winters, the rest new -- and judges '
        'what each can become from what can be watched (the level seen with error, the growth typical for the age, '
        'last year\'s improvement) through an error set by their scouting skill that shrinks with the seasons they '
        'have watched that player (x 1/sqrt(1 + 0.5 x (seasons - 1)), at most six seasons); never hidden potential. '
        'Among players they believe can reach their bar, development coaches (youth specialists) prefer the room to '
        'grow and last year\'s rise; the others prefer established results (Prestige and a world or amateur '
        'ranking), a known fit from working together before, and earned major places. They approach at most two. '
        'A golfer without a coach accepts a share deal less often while a college team coaches them or when last '
        'season\'s prize money makes a share costly, more often from a better-known coach; a golfer with a coach '
        'weighs the newcomer\'s extra reputation against the partnership\'s loyalty (rapport, fit, results together), '
        'so a better-known offer alone rarely ends a good partnership. Courting established players: each coach of '
        'established players with reputation 55 or more and room in their book looks at the 30 most accomplished '
        'golfers within reach (their country, or their region from reputation 60), of any age, with achievement '
        'anyone can see (Prestige / 10 plus up to 3 for a world ranking inside 200 or an amateur ranking inside '
        '300, at least 4), and offers a fee to the one they rate highest (achievement, a known fit, earned major '
        'places), one offer a winter. The golfer accepts only if the fee fits what they can commit to a coach (10% '
        'of their means); without a coach, more readily from a better-known coach and the more coachable they are; '
        'with one, against the loyalty above. Hiring: a golfer who wants a paying coach asks those they can afford '
        'and who have room, best-looking first; a coach rarely refuses while their book has room and, as it fills, '
        'keeps places for the players they look for (or refuses a known poor fit). Caddies: first, each caddie '
        'without a bag looks at the 30 golfers wanting a caddie in their region with the best results and offers '
        'to carry the bag of the one they would most readily accept (if at least 85% ready), one offer a winter; '
        'the golfer accepts only if the caddie\'s fees fit their caddie budget (the hiring rule), without a caddie '
        'more readily the better known the caddie against their own results, with one against the loyalty above. '
        'Then a tour professional still without a caddie offers the bag to caddies they worked well with first, '
        'then to the best-looking ones they can afford; a caddie weighs the golfer\'s results (last season\'s prize '
        'money or Prestige, against what the caddie\'s own reputation earns), a known fit and a Premier card, and '
        'grows readier to accept after each bag turned down that winter. One offer per pair per winter, whoever '
        'makes it; a golfer whose partnership began in this market is not courted again until the next; an '
        'existing partnership ends only when the golfer has accepted another (recorded as leaving for that '
        'approach). Every approach records who made it and why, and why it was accepted or refused; a golfer who '
        'stays out of loyalty has that recorded on the partnership they kept. '
        'Departures follow the existing winter odds (progress, rapport, fit, money) and retirement. The weights '
        'are proposed starting values.',
        '2026-11-04'),
    'course-familiarity': (
        'Course familiarity',
        'Familiarity with a course is the competitive rounds a golfer has played on it, any layout (rounds of an '
        'event, and match-play and playoff holes in rounds\' worth). The engine uses 1 - exp(-rounds / 15): small, '
        'bounded help with decisions, approach distance control and reading greens. Regional baseline: on a '
        'course in the same state or province as the golfer\'s birthplace or where they live at the time, the '
        'engine is given at least 3 rounds; where the state or province is unknown for the golfer or the course, '
        'the same country gives at least 1.5. It is a floor: the engine uses the larger of rounds played and the '
        'baseline, never their sum, and birthplace and residence count once even when they differ (the larger '
        'match). Home club: every golfer whose residence is recorded has one, recorded with its date: a municipal '
        'course in the state or province they live in (else another course there that is not an elite venue; '
        'where there is none, the same choice within their country), a stable draw per golfer and place, changed '
        'only when they move. Their home club counts as at least 3 rounds too -- the same floor, which adds nothing '
        'where the club is in their own state or province, never on top of another baseline. No other home '
        'advantage exists. People whose places were never recorded get no baseline and no home club. The rounds a '
        'golfer has actually played are recorded unchanged; profiles show them and, separately, the value the '
        'engine uses. A caddie\'s familiarity is rounds caddied there only.',
        '2026-11-08'),
    'local-hosting': (
        'Venues: home courses and local hosting',
        'An event in a city returns to the course it last used there (its home course) whenever that course is '
        'free; otherwise it takes the free course whose layouts rank highest for its level in that city, or moves '
        'to another city in its pool. Local hosting: when a low-level event (mini events, small-college golf, 54-72 '
        'hole amateur and club-professional events) or an entry-level event (18-36 hole regional amateur events) '
        'plays in a city for the first time, it takes a free municipal course there that no event has used yet, if '
        'there is one, and keeps it as its home. Established home courses never change because of this, no course '
        'hosts two events in a week, and no event is rotated between courses.',
        '2026-11-08'),
    'aggression': (
        'Aggression (playing style)',
        'A personality trait from 0 (cautious) to 100 (attacking), set when a golfer enters the world and never '
        'changed afterwards: not by age, injury, results or anything else. It is a style, not an ability: higher '
        'is not better. Shown as cautious (below 35), balanced (35-65) or attacking (above 65). It tilts four '
        'choices: the club off the tee (an attacking golfer leans to driver), aiming at the flag or the safe part '
        'of the green, going for a par 5 in two, and attempting the recovery shot from the trees rather than '
        'punching out. It tilts only choices that are possible: a shot out of reach (beyond the longest club from '
        'that lie, which follows Power, so age, injury and season fatigue shorten it) is always a lay-up, however '
        'aggressive the golfer, so an aging attacking golfer still attacks, at what they can still reach. Course '
        'Management sets how well each choice is judged; there is no other risk score.',
        '2026-11-08'),
    'weather': (
        'Weather (seasonal-1)',
        'Simulated seasonal climate, bundled with the game (not a forecast or live weather). Each course reads its '
        'city\'s climate group (oceanic, continental, temperate, Mediterranean, subtropical, tropical, desert, '
        'alpine) for the month of the event: a wind factor on the course\'s typical wind (its style, plus 3 mph on '
        'the coast) and a chance that a round is wet. Southern-hemisphere courses read the month six months on. '
        'Coastal courses swing more through the year. Each event draws a weather system for its week and each '
        'round its own wind speed, direction, gustiness and wetness, from the event\'s seed: the same world gives the same '
        'weather, and what is recorded is exactly what was played. Every hole has a fixed compass line from its '
        'course\'s routing. Headwinds shorten drives and lengthen approaches, tailwinds lengthen drives and make '
        'greens harder to hold, crosswinds widen the lateral spread. Gusts: each full shot meets the wind at its '
        'own strength around the round\'s mean (gustier on the coast, in unsettled weeks and windy months; '
        'bounded, and the round\'s average wind damage is the same as a steady wind of that speed), so carry and '
        'spread vary shot to shot. Wet rounds shorten the roll, thicken the '
        'rough, make sand heavier, soften the greens and add grip and concentration errors (less on fast-draining '
        'links, sandbelt and heathland). Ball-Flight Control, accuracy and distance control, Course Management, '
        'Recovery Play, Bunker Play, Focus, the caddie\'s yardage, mental support and course knowledge, and '
        'familiarity with the course all reduce the damage (a low, controlled flight, the caddie\'s yardage and '
        'good management also feel less of the gusts); none removes it. Who is playing never changes the '
        'weather or its effect (no country penalty). No round is ever cancelled, shortened or delayed by weather. '
        'Temperature and seasonal turf firmness are not modelled. Worlds started before rules 2026-11-09 keep the '
        'classic weather: wind speed only and a flat 8% chance of rain that only shortened the roll.',
        '2026-11-09'),
    'injuries': (
        'Injuries',
        'A golfer can be hurt playing an event; the chance rises with tiredness, age and the rounds played and falls '
        'with injury resistance and stamina. An injury at an event in week W announced as n weeks keeps them out '
        'of the entries of weeks W+1 to W+n, counted on across the year end (next season\'s week 1 follows week '
        '52); they can enter again from week W+n+1, and a major place falling in those weeks is withdrawn. An '
        'injury of 10 weeks or more can take some power, stamina and injury resistance, and their ceilings, for '
        'good (the longer, the likelier). Before rules 2026-11-02 a golfer stayed out one week longer than announced.',
        '2026-11-02'),
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
_MAJOR_CODE = re.compile(r'^([MPUB]\d+R?|UQ|UF|UA|BQ|BF|PF|BQ_[A-Z_]+)$')


def _major_labels(version=None):
    from .qualification import rules_for
    return {r.code: r.label for routes in rules_for(version).values() for r in routes}


_labels = {}


def explain(route, version=None):
    """(rule id, readable text) for a recorded entry route; (None, None) if it is not recognised (the code
    is then shown as it is). version: the calendar the season was played under (a major route's wording
    follows its own version; classic when not given)."""
    if not route:
        return None, None
    late = route.endswith(' — late entry')
    base = route[:-len(' — late entry')] if late else route
    rule, text = _explain(base, version)
    if late and text:
        text += ' — a late entry'
    return rule, text


def _explain(r, version=None):
    if r in _FIXED:
        return _FIXED[r]
    if r.startswith('PREMIER ') and r[8:] in _PREMIER_RIGHTS:
        return 'premier-rights', _PREMIER_RIGHTS[r[8:]]
    for pat, rule, text in _PATTERNS:
        m = pat.match(r)
        if m:
            return rule, text.format(*m.groups())
    if _MAJOR_CODE.match(r):
        labels = _labels.get(version)
        if labels is None:
            labels = _labels[version] = _major_labels(version)
        if r in labels:
            return 'major-qualification', labels[r]
    if r.endswith(' MEMBER'):
        return 'other-member', f'A member of the {r[:-7].title()}'
    return None, None
