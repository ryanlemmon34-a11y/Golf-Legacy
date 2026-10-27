"""Golf Legacy v0.8 capacity experiment, NOT a full gameplay version.

Extends v0.7 with geographically distributed regional and local pro circuits.
Does not alter original scoring, mental pressure, cut, grouping, payout, career
progression, rookie generation, or financial eligibility rules.

This is deliberately *not* an amateur/college system. Amateur eligibility and
semi-professional work schedules require their own explicit design and tests.
"""
from engine_v07 import World as FrozenV07
from engine_v03 import Tour

REGIONS=('Americas','Europe','Asia','Africa','Oceania')

class World(FrozenV07):
    def __init__(self,*args,extra_circuits_per_region=3,**kwargs):
        self.extra_circuits_per_region=extra_circuits_per_region
        super().__init__(*args,**kwargs)

    def _setup_tours(self):
        super()._setup_tours()
        for region in REGIONS:
            for i in range(self.extra_circuits_per_region):
                # One regional feeder and two local professional circuits.
                # All retain their home region but share the same global
                # pool of professional entrants and the v0.7 funding rules.
                tier=3 if i==0 else 4
                tour=Tour(id=len(self.tours),
                          name=f'{region} {"Secondary Regional" if tier==3 else "Local Pro " + str(i)}',
                          region=region,tier=tier,
                          prestige=(35 if tier==3 else 19),
                          events=10,slots=(88 if tier==3 else 72),
                          purse=(135000 if tier==3 else 38000))
                self.tours.append(tour)
