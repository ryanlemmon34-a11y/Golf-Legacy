# Golf Legacy v0.6 — changes and open questions

This is a separate working revision of the preserved v0.3 archive. It does not modify the original conversation. No paid services, purchases or real financial transactions were used. Simulation money is fictional.

## Main changes

**Skill and competition.** Persistent elite execution matters more without rank bonuses or forced winners. Per-hole residual variance is reduced while preserving expected strokes, with week/round variation and consistency retained. The final candidate smoothly compresses the extreme tail above execution rating 90, preserving the ordinary curve and its slope at the transition. There is no hard score ceiling or named-player adjustment.

**Development and starting players.** Established veterans are initialized along approximate individual development trajectories rather than receiving disproportionate mature skill. Different growth rates, peaks and decline remain. Replacements debut at 18 rather than arriving at 19 with age-18 attributes. Latent caps, developed ability, temporary form and ranking remain distinct.

**Funded careers.** Players must fund entry and their season's professional overhead. Outside-work contributions arrive with elapsed time, not as advance credit; work and fewer funded starts reduce training exposure. Affordable downshifts, hiatus, re-entry and permanent exits are separate states. A soft mid-20s reassessment is not an age-26 retirement rule. Three consecutive seasons of observable progress can earn patience, never waive a cash constraint. Moving to weaker fields cannot manufacture apparent improvement. Sponsorship is optional and OFF by default.

**Real opportunities.** Five regional mini circuits replace a single under-capacity global circuit. They use distinct 100-player events, open cross-region entry and a geographic preference, not guaranteed starts. A major victory grants premier eligibility for the following five seasons under a declared fictional rule, avoiding a proven major winner being trapped on a slow promotion ladder. Entry is still cash-gated.

**Correctness.** Fixed missing/spurious course familiarity, major experience reset before development, permanent residual penalties from temporary slumps, non-conserved purses and duplicate tied-place payouts, phantom charges for cancelled undersubscribed events, stale retirement state and double-booked course/week venues. Chronological hole order, pairings, cuts, playoff handling and live pressure remain intact.

**A living record.** Annual histories, entry-opportunity diagnostics, economic ledgers and reasoned transitions support evidence-based recaps. Year-end injuries/slumps cannot explain earlier results. Stories do not invent motives or attribute outcomes to hidden potential.

## What changed because testing found problems

The original five v0.3 worlds produced 85–96 distinct major champions per 120 majors. An initial v0.4 elite-skill experiment overcorrected: its two worlds produced 51 and 47, with the retrospective ten most successful champions winning 56.7% and 55.0%. Those results are retained, not marketed as balanced.

The apparent aging problem was largely initialization: in v0.4, established players won majors at mean ages 36.8 and 37.5; new entrants' means were 30.5 and 30.8. Established starters accounted for 41 of 42 wins at age 40+. This supported correcting veteran initialization rather than forcing all players to decline earlier.

The next two v0.5 worlds looked reasonable in aggregate (68/73 distinct major champions; 42.5%/35.8% retrospective top-ten share), but exposed two serious issues:

- One player, Kai Taylor, won 18 majors in 36 starts by age 26. His debut attributes were already near their ceilings. Actual-profile replay and controlled scoring tests found a 4.43-stroke expected round advantage over the contemporaneous 100th ability-ranked golfer. The smooth v0.6 tail reduces that matched-control gap to 3.62 while leaving ordinary profiles essentially unchanged. This is a model calibration correction, not a penalty for that player. His early rare-readiness profile remains an important uncertainty.
- The lone mini circuit supplied just 1,200 slots for roughly 800 players. Median participation was two starts per year, and no mini-tier season ever qualified for sustained-progress credit. Financial failure was partly a calendar bottleneck. More plausible opportunities were needed before interpreting career exits.

## Access is not guaranteed financial success

The regional circuits supply 6,000 annual slots and explicitly add tournament purse funding: 60 × 45,000 raises annual mini prizes from 540,000 to 2.7 million. Improved finances cannot be attributed solely to access.

A separate three-year purse-neutral sensitivity kept the annual pool at 540,000 by paying 9,000 per event. Mini participants still reached a median 12 starts and 46 observable-progress cases in the third year; the standard-purse scenario produced 11 starts and 68 cases. Only 1 of 504 versus 29 of 529 active mini players had nonnegative golf net. More opportunity creates costs as well as chances; it does not guarantee a viable career.

An opening-bankroll sensitivity compared zero, four and eight event reserves above overhead for the same established cohort. Zero reserves caused 375 immediate downshifts; four and eight caused none. The four-event default is a declared initial-world assumption representing fictional prior careers, not earned income or a later bailout. New entrants do not receive this floor.

## Evidence and limitations

- Current top-125 career histories are survivor-conditioned. Rankings are not ability, tour participation is not a tour card, and a current successful cohort cannot establish every aspirant's failure probability.
- Economic costs, savings, work capacity, progress thresholds and exit probabilities are prototype assumptions, not empirically fitted forecasts. Retirement can reflect opportunity cost and progress, not only bankruptcy; there is no evidence-backed universal quitting age.
- Tier membership, qualifying and exemptions remain simplified. Major selection is still too directly ability-based. There is no full amateur pathway, Q-school or real exemption system.
- Broad near-ceiling skill at debut can still occur in the inherited rare generator. Smooth scoring compression addresses extrapolation, not the full realism of component readiness. Exceptional young players should retain room and varied paths to develop.
- Equal regional calendars and flat travel costs may encourage implausible cross-region participation. Final late-world opportunity distributions, not just the initial pilot, matter.
- Active careers and late entrants are right-censored; starting veterans have unobserved prehistory. Replenishing 1,700 active slots is not an estimated worldwide professional funnel. All-tour wins must not be called premier-tour wins.
- Two final worlds test a configuration, not generational frequencies or proof of balance. The historical 1990–2019 major benchmark is an era-dependent reference, not a quota. Retrospective top-ten winner share is not pre-event top-ten ranking win probability.

See the source-linked research, frozen configuration, diagnostics, final audits and `CONTINUE_PROJECT.md` for reproducible details and next priorities.

## Bounded extreme-profile check

An explicit fixture repeated 200 complete major-style tournaments per version against the same strong 144-player field across 12 courses. The captured extreme profile won 105 under v0.5 and 52 under v0.6; top-five finishes fell from 162 to 110. Full cuts, pressure, pairings and playoffs were retained. This supports the direction of the taper, not the rarity or full career of a naturally generated prodigy. Neither final v0.6 world generated a flagged rare candidate. See `diagnostics/EXTREME_TOURNAMENT_STRESS.md`.
