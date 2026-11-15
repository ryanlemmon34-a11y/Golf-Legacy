"""Career semantic accents. Green remains primary; labels/signs carry every meaning without color."""
PALETTES = {
    'light': {'green':('#17643d','#edf7ef'), 'gold':('#78520b','#fff4d6'),
              'blue':('#175d91','#edf5ff'), 'amber':('#824600','#fff3df'),
              'red':('#a22c36','#fff0f1'), 'violet':('#66429a','#f4effb')},
    'dark': {'green':('#8bdcb0','#20372a'), 'gold':('#f3cf75','#392f19'),
             'blue':('#9dccff','#203247'), 'amber':('#ffc77c','#3d2d18'),
             'red':('#ffadb5','#40252b'), 'violet':('#d2b9ff','#332943')},
}

def variables(mode):
    return ''.join(f'--career-{name}:{fg};--career-{name}-bg:{bg};' for name,(fg,bg) in PALETTES[mode].items())

STYLE = '<style>.career-hub{' + variables('light') + '}@media(prefers-color-scheme:dark){.career-hub{' + variables('dark') + '''}}
.career-hub {--career-frame:#b8c9bd;--career-shadow:0 3px 10px #18362610,0 1px 2px #1836260a}
@media(prefers-color-scheme:dark){.career-hub {--career-frame:#435b4b;--career-shadow:0 4px 14px #00000038,0 1px 2px #00000028}}
.career-hub .career-panel,.career-hub .planner-week,.career-hub .attribute-card,.career-hub .newcomer-card {border-color:var(--career-frame);box-shadow:var(--career-shadow)}
.career-hub .career-panel > h2,.career-hub .career-panel > .section-heading {padding-bottom:12px;border-bottom:1px solid var(--career-frame)}
.career-hub #period-review {border-top:4px solid var(--career-gold)}
.career-hub #career-plan {border-top:4px solid var(--career-green)}
.career-hub #career-inbox {border-top:4px solid var(--career-blue)}
.career-hub .planner-week legend {border:1px solid var(--career-green);border-radius:6px;padding:4px 10px;background:var(--career-green-bg);color:var(--career-green)}
.career-hub .planner-week:focus-within,.career-hub .newcomer-card:focus-within {outline:2px solid var(--career-blue);outline-offset:3px}
.career-hub .career-details {border-color:var(--career-frame);border-left:3px solid var(--career-green)}
.career-hub .career-hero {border-top:5px solid var(--career-green);background:linear-gradient(110deg,var(--career-green-bg),var(--panel));box-shadow:0 8px 24px #00000008}
.career-hub .career-overall {color:var(--career-green);background:var(--career-green-bg);padding:18px;border:1px solid var(--career-green);border-radius:10px}
.career-hub .career-overall strong {color:var(--career-green)}
.career-hub .career-summary {gap:10px}
.career-hub .career-summary > div {border-radius:7px;padding:8px 12px;border-left:3px solid var(--career-green);background:var(--career-green-bg);color:var(--career-green)}
.career-hub .career-summary > div:nth-child(2),.career-hub .career-summary > div:nth-child(3) {border-color:var(--career-gold);background:var(--career-gold-bg);color:var(--career-gold)}
.career-hub #career-calendar {border-top:4px solid var(--career-blue)}
.career-hub #career-calendar .status-pill {color:var(--career-blue);background:var(--career-blue-bg);border-color:var(--career-blue)}
.career-hub .career-nav a[href="#career-calendar"] {color:var(--career-blue);background:var(--career-blue-bg)}
.career-hub .career-nav a[href="#period-review"] {color:var(--career-gold);background:var(--career-gold-bg)}
.career-hub .career-nav a[href="#career-attributes"] {color:var(--career-violet);background:var(--career-violet-bg)}
.career-hub .coach-advice {border-left:4px solid var(--career-blue);background:var(--career-blue-bg)}
.career-hub .coach-advice h3 {color:var(--career-blue)}
.career-hub .result-win .result-place {color:var(--career-gold);background:var(--career-gold-bg);border:1px solid var(--career-gold)}
.career-hub .result-top10 .result-place {color:var(--career-green);background:var(--career-green-bg);border:1px solid var(--career-green)}
.career-hub .readiness {border-top:4px solid var(--career-green)}
.career-hub .readiness-caution {border-color:var(--career-amber)}
.career-hub .readiness-caution .fatigue-number {color:var(--career-amber)}
.career-hub .readiness-caution meter {accent-color:var(--career-amber)}
.career-hub .entry-evidence {border-left:3px solid var(--career-blue);background:var(--career-blue-bg);padding:10px 14px;margin:12px 0;border-radius:0 6px 6px 0}
.career-hub .entry-evidence > strong {color:var(--career-blue)}
.career-hub .attribute-card {border-top:3px solid var(--career-violet)}
.career-hub .attribute-track i {background:var(--career-green);opacity:1}
.career-hub .up {color:var(--career-green)} .career-hub .down {color:var(--career-red)}
.career-hub .banner.warn {color:var(--career-amber);background:var(--career-amber-bg);border-left:4px solid var(--career-amber)}
.career-hub .planner-week {border-top:3px solid var(--career-green)}
.career-hub .plan-option:has(input:checked) {border:2px solid var(--career-green);background:var(--career-green-bg);padding:10px}
.career-hub button.primary {background:var(--career-green);color:var(--career-green-bg);font-weight:700;border-color:var(--career-green)}
.career-hub .newcomer-card {border-top:3px solid var(--career-blue)}
.career-hub a:focus-visible,.career-hub button:focus-visible,.career-hub input:focus-visible,.career-hub select:focus-visible {outline:3px solid var(--career-blue);outline-offset:3px}
@media(forced-colors:active){.career-hub .plan-option:has(input:checked) {outline:2px solid Highlight}.career-hub button.primary {forced-color-adjust:auto}}
</style>'''
