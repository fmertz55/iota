"""Build numbers.tex and figures for the shadow paper from committed result files only."""
import json, sys, statistics as st
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'src'))
O = ROOT / 'output/minimal_realization'; G = ROOT / 'shadow_paper/generated'; F = ROOT / 'shadow_paper/figures'
J = lambda p: json.load(open(O / p))
core = J('MIR-REVERSIBLE-CORE-001/results.json')['summary']
aut = J('MIR-REVERSIBLE-AUTONOMY-001/results.json')['summary']
vc = J('MIR-REVERSIBLE-VACUUM-COLLIDE-001/results.json')
c2 = J('MIR-REVERSIBLE-COLLIDE-002/results.json')['summary']
s2 = J('MIR-REVERSIBLE-SHADOW-002/results.json')
s3 = J('MIR-REVERSIBLE-SHADOW-003/results.json')
S3 = s3['summary']; pairs = s3['pairs']
sh = [x for x in pairs if x['shadow_runs'] > 0 and x['only_shadow'] > 1e-12]
N = dict(
 coreSingle=core['primary_pass'], coreRules=core['secondary_pass_rules'], corePairs=core['secondary_pairs'],
 autSub=aut['sub-light']['same_object'], autSubN=aut['sub-light']['n'], autLight=aut['light']['autonomous'], autLightN=aut['light']['n'],
 autRules=len({c[0] for c in aut['candidates']}),
 silentSub=vc['V']['silent']['sub-light'], activeSub=vc['V']['active']['sub-light'],
 ctwoRules=c2['rules'], ctwoN=c2['collisions'], ctwoElastic=c2['outcomes']['elastic'], ctwoTrans=c2['outcomes']['transmuted'],
 ctwoSup=c2['outcomes']['superposition'], ctwoBubble=c2['outcomes']['bubble'], ctwoUnres=c2['outcomes']['unresolved'],
 stwoClean=s2['summary']['clean'], stwoShadow=s2['summary']['shadow_rules'],
 sthreePairs=S3['pairs'], sthreeClean=S3['clean_pairs'], sthreeShadow=S3['shadow_pairs'], sthreeShadowRules=S3['shadow_rules'],
 sthreeFoot=S3['footprint_ratio_1'], sthreeStatePos=S3['probe_state_positive'], sthreeStateOne=S3['probe_state_ratio_1'],
 sthreeStateMed=f"{S3['probe_state_ratio_median']:.2f}",
 onlyMin=f"{min(x['only_shadow'] for x in sh):.2f}", onlyMax=f"{max(x['only_shadow'] for x in sh):.2f}",
 survMed=int(st.median(x['probe_R_species_survives'] for x in sh)))
G.mkdir(exist_ok=True, parents=True)
(G / 'numbers.tex').write_text(''.join(f"\\newcommand{{\\n{k}}}{{{v}}}\n" for k, v in N.items()))
# Figure 3: per-pair ledger
plt.rcParams.update({'font.size': 8})
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.8))
xs = np.arange(len(sh)); order = sorted(range(len(sh)), key=lambda i: (sh[i]['only_shadow'], sh[i]['probe_state_ratio']))
ax[0].bar(xs, [sh[i]['only_shadow'] for i in order], color='0.75', label='held only by the background')
ax[0].scatter(xs, [sh[i]['footprint_beyond'] for i in order], s=8, color='k', zorder=3, label="recovered from the probe's footprint")
ax[0].set_xlabel(f'shadow pairs (n = {len(sh)})'); ax[0].set_ylabel('bits (of 6)'); ax[0].set_xticks([])
ax[0].set_title('The probe recovers all of it', loc='left'); ax[0].legend(frameon=False, loc='upper left')
r = [x['probe_state_ratio'] for x in sh]
ax[1].hist(r, bins=np.linspace(0, 1, 11), color='0.35', edgecolor='white')
ax[1].set_xlabel('fraction carried out by the probe coherence itself'); ax[1].set_ylabel('shadow pairs')
ax[1].set_title('Often the probe carries it away', loc='left')
for a in ax: a.spines[['top', 'right']].set_visible(False)
fig.tight_layout(); fig.savefig(F / 'fig3_ledger.pdf'); fig.savefig(F / 'fig3_ledger.png', dpi=200)
print(json.dumps(N))
