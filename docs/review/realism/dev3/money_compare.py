import statistics as st, sys
sys.path.insert(0, sys.argv[1])
from golfsim import population as P
from golfsim import finance as F
for seed in map(int, sys.argv[2:]):
    row = [seed]
    for r in ('dev-2', 'dev-3'):
        w = P.generate_world(seed=seed, dev_rules=r)
        pros = sorted((g for g in w.golfers if F.in_money_pool(g)), key=lambda g: -g.overall)
        cash = sorted((g.cash for g in pros), reverse=True)
        row.append(f'{r}: #1 {pros[0].overall:.1f} cash ${pros[0].cash/1e6:.1f}M | richest ${cash[0]/1e6:.1f}M | '
                   f'top-10 rating median cash ${st.median(g.cash for g in pros[:10])/1e6:.1f}M | '
                   f'all pros median ${st.median(cash)/1e3:.0f}k total ${sum(cash)/1e9:.2f}B | backed {sum(1 for g in pros if g.backer)}')
    print(*row, sep='\n  ')
