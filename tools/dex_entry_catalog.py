#!/usr/bin/env python3
"""Catalog of Toepfer pokedex flavor text for dex_entry sync."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEX_CSV = ROOT / "docs" / "toepfer-dex-entries.csv"
MATRIX_CSV = ROOT / "docs" / "toepfer-matrix.csv"
APPLY_SCRIPT = ROOT / "tools" / "apply_dex_csv.py"

MIN_LEN = 80
MAX_LEN = 120

ENTRIES: dict[int, str] = {
    1: "Fresh from onboarding, TOEPFER keeps desk ferns alive and morale wilting. HR calls it growth.",
    2: "TOEPFERJR schedules fertilizer like quarterly reviews. Every leaf gets a performance plan.",
    3: "TOEPFERSR photosynthesizes profits from the corner office. Sunlight is a taxable benefit.",
    4: "LILTOEPF dials until the headset melts daily. Voicemail is just a warm lead waiting.",
    5: "BIGTOEPF turns maybe into signed contracts before coffee cools. The pen never rests.",
    6: "MEGATOEPF closes deals hot enough to void the NDA. Legal keeps a fire extinguisher.",
    7: "DRTOEPFER resets passwords and dampens panic. Have you tried turning it off and on?",
    8: "SIRTOEPF guards the server room like a prized shell collection. Root needs three approvals.",
    9: "LORDTOEPF cannons through legacy systems at budget reviews. Uptime is nonnegotiable policy.",
    10: "KINGTOEPF files paperwork faster than anyone can shred it. The inbox never stops inching.",
    11: "QUEENTOEPF cocoons in meetings until promoted. Hard shell outside, soft deadlines within.",
    12: "PRINCEOEPF floats above org charts spreading memos. Every department gets a gentle directive.",
    13: "CYBEROEPF needles through footnotes at two AM. Discovery never sleeps, and neither does he.",
    14: "ROBOTOEPF stays rigid until the partner says go. Motion filed, body still not moving.",
    15: "LASERTOEP stings anyone who reads the fine print wrong. Three partners, zero mercy shown.",
    16: "PLASMATOEP sorts interoffice mail by wing flap. Certified delivery means certified exhaustion.",
    17: "QUANTOEPF beats rush hour with a beak full of contracts. Same-day delivery, same-day overtime.",
    18: "ATOMTOEPF flies executives above traffic and accountability. Clear skies, unclear expense reports.",
    19: "NANOTOEPF clocks in at dawn and out whenever payroll blinks. Benefits are a future milestone.",
    20: "GIANTOEPF finally made perm after three years of maybe. The break room now knows their name.",
    21: "MICROTOEP scans barcodes and patience at equal speed. Every beep is another minute of life.",
    22: "MUTANTOEP patrols aisles like a hawk with a clipboard. Shrinkage drops when fear goes up.",
    23: "GAMMAOEPF pitches wellness plans that cure nothing but budget. Slither into the demo today.",
    24: "RADIOTOEP owns the pipeline and the pipeline owns you. Barrels of synergy, drops of truth.",
    25: "GLOWTOEPF lives on caffeine, cables, and unresolved tickets. The glow of monitors is home.",
    26: "TOXICTOEP approves pull requests and punishes scope creep. One merge away from burnout.",
    27: "ACIDTOEPF digs into client sites and sand traps alike. Territory maps fit in one claw.",
    28: "FROSTOEPF rolls up quarterly numbers like a burrow. No account escapes the final audit.",
    29: "BLAZETOEPF runs the hive floor with poison diplomacy. Cross her and feel the sting memo.",
    30: "SHOCKOEPF demands spotlight, budget, and a better chair. Drama is just unpaid emotional labor.",
    31: "PSYCHOTOEP armors the boardroom against nonsense. Soft skills, hard spikes, zero tolerance.",
    32: "TELETOEPF still has the orientation lanyard on. Enthusiasm high, parking pass still pending.",
    33: "CLONETOEPF micromanages with horns and a smile. Your timesheet is always slightly wrong.",
    34: "COPYTOEPF rules the floor from a corner cubicle. Loyalty rewarded, dissent reorganized quietly.",
    35: "FAKETOEPF floats shift to shift hoping for hours. Dreaming of full-time and dental coverage.",
    36: "GLITCHOEPF finally earned PTO and a nameplate. Weekends exist on paper, not in practice.",
    37: "BETATOEPF spins every scandal into a teachable moment. Nine tails, nine talking points ready.",
    38: "ALPHATOEPF crafts narratives smoother than silk. Bad news ships Friday at five sharp.",
    39: "OMEGATOEPF lulls the all-hands until everyone naps. Applause mandatory, consciousness optional.",
    40: "ZETATOEPF holds the stage until Q and A dies. Inspiration billed at consultant rates.",
    41: "NULLTOEPF flutters through graveyard shifts unseen. Fluorescents hum, productivity does not.",
    42: "VOIDTOEPF shift lead drinks cold coffee like blood. Dawn is just another deadline missed.",
    43: "CHAOSTOEP mops floors and executive egos nightly. The trash reveals more than audits do.",
    44: "ORDEROEPF cultivates lobby plants and rumors alike. Nothing wilts faster than open secrets.",
    45: "LAWTOEPF pollenates projects until walls bloom. Allergy season is just sprint planning.",
    46: "CRIMETOEP fries morale alongside the lunch rush. One ticket, one tantrum, repeat forever.",
    47: "DETTOEPF runs the kitchen like a hostile takeover. Plates out, feelings optional, tips split.",
    48: "SPYTOEPF clicks every button until something breaks. Bug reports are love letters to dev teams.",
    49: "AGENTOEPF mothballs releases until standards met. Ship date is a suggestion, not a promise.",
    50: "NINJATOEPF tunnels under deadlines without daylight. Hard hats required, optimism buried deeper.",
    51: "PIRATEOEPF coordinates three diggers and one budget. Underground politics run deeper than pipes.",
    52: "COWBOYOEP swipes from the fund and your trust. Expense reports always miss a few coins.",
    53: "KNIGHTOEP audits every penny with velvet claws. The company card has a very short leash.",
    54: "WIZARDOEP migrates between desks solving problems badly. Headaches migrate straight to WITCHTOEP.",
    55: "WITCHTOEP listens until the billable hour ends. Insight costs extra, silence costs more.",
    56: "VAMPTOEPF punches above rank and below standards. Orientation video still playing in their head.",
    57: "WERETOEPF ejects trouble from the club and the Slack. No ID, no entry, no refund on dignity.",
    58: "ZOMBIETOEP greets VIPs and growls at vendors. Tail wags for executives, snarls for interns.",
    59: "GHOSTOEPF patrols the perimeter and the parking lot. Unauthorized access ends at the lobby.",
    60: "ANGELTOEPF skims leaves and gossip from the fountain. Depth is shallow, secrets run deep.",
    61: "DEMONTOEPF whistles at running near the cubicles. No diving into spreadsheets without floaties.",
    62: "ALIENOEPF flexes policy until compliance submits. Muscle is the final approval workflow.",
    63: "UFOTOEPFER teleports away from feedback mid-sentence. Potential unlimited, attention span limited.",
    64: "SPACEOEPF bends spreadsheets until they confess. Numbers never lie, but they do get coached.",
    65: "MOONTOEPF reads minds and quarterly projections. IQ high, empathy outsourced to HR.",
    66: "STARTOEPF reps the company wellness plan daily. Corporate discount on pain and gain.",
    67: "SUNTOEPF spots interns until they drop the bar. Form matters, feelings do not count here.",
    68: "EARTHTOEPF runs three departments with six arms. Multitasking is just unpaid overtime.",
    69: "SPROUTOEP vines toward promotion one rung at a time. Sunlight is middle management above.",
    70: "JEDITOEPF hangs between floors waiting for a lift. Elevator broken, ambition still ringing.",
    71: "SITHTOEPF digests rivals and lunch meetings whole. Corner office view, carnivorous calendar.",
    72: "BORGTOEPF worker never leaves the home pod. Slack green dot is the only proof of life.",
    73: "DROIDOEPF tentacles reach every screen share silently. Mic off does not mean unseen.",
    74: "CYBORGTOEP blocks every initiative with rocky skepticism. Progress halted, meeting extended again.",
    75: "MECHTOEPF rolls over fresh ideas at the door. Innovation requires three forms and a bribe.",
    76: "TANKTOEPF stops traffic, projects, and small talk. Immovable object, immovable deadline.",
    77: "SNIPERTOEP gallops interoffice mail before the elevator. Hoofbeats echo through empty halls.",
    78: "MEDICTOEPF routes couriers faster than approval chains. Flame trail optional, overtime mandatory.",
    79: "CHEFTOEPF responds to emails next fiscal quarter. Urgent flagged, still unread, somehow fine.",
    80: "NURSETOEPF shelled out for silence and a corner desk. Productivity naps behind a closed door.",
    81: "NERDTOEPF attaches to every desk needing staples. Magnetic personality, paperclip budget.",
    82: "JOCKTOEPF pulls departments together or apart. Alignment achieved, casualties acceptable.",
    83: "GOTHTOEPF brings leek soup to every board lunch. Side dish of guilt included, no substitutions.",
    84: "KARENOEPF splits focus between two bosses daily. Two heads, half the credit, double blame.",
    85: "CHADTOEPF adds a third opinion nobody requested. Consensus means agreeing with the loudest beak.",
    86: "BOOMERTOEP seals crates and excuses before departure. Cold chain, cold hearts, on-time delivery.",
    87: "ZOOMERTOEP hauls freight and gossip cross-country. CB radio runs on diesel and drama.",
    88: "GRANDTOEPF sticks to every surface in the break room. Sanitize the rumor before it hardens.",
    89: "UNCLETOEPF dissolves messes organic and political. Nothing toxic survives the mop bucket.",
    90: "DADTOEPF opens doors and closed-door meetings. Shell tight, secrets tighter, key under mat.",
    91: "MOMTOEPF guards assets behind a pearl-white firewall. Breach attempts bounce off politely.",
    92: "BROTOEPF drifts desk to desk with no badge scan. HR forgot to onboard the ghost again.",
    93: "SISTOEPF haunts the break room after clock-out. Free snacks vanish whenever it appears.",
    94: "TWINTOEPF makes problems disappear from the ledger. Smile wide, shadow long, questions shorter.",
    95: "TRIPTOEPF coils through cable trays like policy. One break and the whole network shudders.",
    96: "SOLOTOEPF dreams invoices into existence at three AM. Sleepwalking through the close books.",
    97: "DUOTOEPF hypnotizes staff into overtime compliance. Watch the pocket watch, sign the waiver.",
    98: "TRIOTOEPF pinches accounts until they squeak. Every line item clawed from reluctant clients.",
    99: "LEGIONOEPF grabs overdue payments with both claws. Interest compounds, patience does not.",
    100: "ARMYTOEPF spins up systems until something sparks. Self-destruct is a feature, not a bug.",
    101: "NAVYTOEPF detonates legacy code on schedule. Boom means deployment succeeded this quarter.",
    102: "MARINEOEPF huddles in orientation clutching handbooks. Crack one shell, ten policies spill out.",
    103: "CAPTOEPF headhunts talent from rival break rooms. Three heads, one offer letter, no mercy.",
    104: "MAJORTOEPF constructs facades and floor plans nightly. Hard hat on, past buried, blueprint ready.",
    105: "GENRLTOEP carries the project bone through winter. Morale buried, deadline very much alive.",
    106: "SERGTOEP kicks memos down the hall at speed. Urgent stamped, recipient still not ready.",
    107: "BABYTOEPF punches clocks and faces with equal force. Late again, documented, noted, filed.",
    108: "TEENTOEPF licks every plate before the executive suite. Speed over sanitation, always.",
    109: "WOKETOEPF spews fumes in every stand-up meeting. Ventilation insufficient, attitude abundant.",
    110: "BASEDTOEPF obscures metrics behind a haze of spin. Two heads, one narrative, zero clarity.",
    111: "CRINGETOEP charges through trades like a rampage. Horns down, market up, ethics negotiable.",
    112: "RIZZTOEPF rhymes bull with billable hours daily. Commissions horned in before the bell rings.",
    113: "SIGMATOEPF heals bruised egos with policy pamphlets. Eggs in one basket, grievances in another.",
    114: "NPCTOEPF tangles every receipt until truth emerges. Compliance is a knot, not a suggestion.",
    115: "BOSSTOEPF pouches interns through crisis and snacks. Maternal leave policy written in practice.",
    116: "FINALTOEPF fetches coffee for the loading dock. Small fins, big hustle, zero recognition.",
    117: "SECRETOEPF directs shipments with a stern fin daily. Tide waits for no purchase order.",
    118: "LEGENDTOEP swims in the talent pool bottom tier. Big dreams, tiny budget, large appetite.",
    119: "MYTHTOEPF dominates the pond and the bonus pool. Scale tips toward whoever swallows rivals.",
    120: "RARETOEPF twinkles in the company talent show. Five points of potential, one spotlight.",
    121: "SHINYTOEPF commands the stage and the org chart. All eyes up, all budgets down now.",
    122: "GOLDTOEPF mimes deadlines behind invisible walls. Silent suffering, loud applause required.",
    123: "SILVRTOEP cuts costs with precision and no anesthesia. Scalpels sharp, feelings numb.",
    124: "BRONZTOEPF kisses cheeks and freezes small talk cold. Hospitality with a chilling subtext.",
    125: "DIAMTOEPF buzzes through outages and live wires. Sparks fly, tickets close, hair singes.",
    126: "RUSTTOEPF heats up safety drills until everyone sweats. Exit signs glow, excuses burn off.",
    127: "ELITETOEPF pins inventory until nothing moves. Shelves orderly, soul slightly crushed.",
    128: "NOOBTOEPF stampedes the floor when the bell rings. Horns locked with bears, coffee spilled.",
    129: "PROTOTOEPF flops in the pond while executives laugh. Promotion feels like a myth told upstream.",
    130: "GODTOEPF finally made VP after years of splashing. Teeth out, title up, respect mandatory.",
    131: "DEMIGDTOEP ferries brass across town in comfort. Back seat meetings, front seat discretion.",
    132: "MIMETOEPF mirrors every deck until originality blurs. Performance review says highly adaptable.",
    133: "INFINITOEP evolves role based on whoever speaks loudest. Potential unlimited, desk still temporary.",
    134: "CHAOTTOEPF flows into any client conversation smoothly. Commissions ripple, quotas still rise.",
    135: "GLTCHTOEPF jolts stale meetings back to life briefly. Energy spikes, then the bill arrives.",
    136: "MOONMOOEP burns through leads faster than forecasts. Flashy close, smoky aftermath, charred quota.",
    137: "POTATOEPF processes forms at digital clock speed. Pixel perfect, soul slightly corrupted.",
    138: "TOMATOEPF fossilizes in the archive basement politely. Ancient resume, modern pay grade.",
    139: "CARROTOEPF spirals up the ladder with tentacle grip. Tenure coiled tight around the org chart.",
    140: "ONIONTOEPF stands fossil-still at the server room door. Threats bounce off the carapace.",
    141: "GARLICTOEP slices through policy violations cleanly. Blades out, compliance in, appeals closed.",
    142: "PICKLEOEPF commutes by air to skip stand-ups. Prehistoric perks, modern expense fraud.",
    143: "WAFFLEOEPF sleeps through pager duty and all-hands. PTO balance infinite, responsiveness zero.",
    144: "PANCAKTOEP freezes budgets until Q4 thaws. Cold logic, colder emails, ice in veins.",
    145: "TACOTOEPF electrifies infrastructure until it screams. Sparks mean innovation, burns mean KPIs.",
    146: "PIZZATOEPF rose from the layoff list phoenix-style. Same desk, new title, old trauma included.",
    147: "BURGEROEPF coils around the org chart learning ropes. Small scale now, boardroom appetite growing.",
    148: "SUSHITOEPF stretches between teams until thin. Long neck, longer meetings, short patience.",
    149: "RAMENTOEPF lands deals from the penthouse nest. Wings wide, dividends wider, objections smaller.",
    150: "COFFEEOEPF duplicated from the perfect employee template. Free will sold separately, NDA eternal.",
    151: "TOEPFERX appears in meetings uninvited, unchanged. No job title fits, neither does any box.",
}


def validate_entry(dex_num: int, ingame_name: str, entry: str) -> list[str]:
    errors: list[str] = []
    length = len(entry)
    if length < MIN_LEN:
        errors.append(f"#{dex_num} {ingame_name}: too short ({length} < {MIN_LEN})")
    elif length > MAX_LEN:
        errors.append(f"#{dex_num} {ingame_name}: too long ({length} > {MAX_LEN})")
    if ingame_name not in entry:
        errors.append(f"#{dex_num} {ingame_name}: missing ingame_name substring")
    return errors


def main() -> int:
    failures: list[str] = []
    rows: list[dict[str, str]] = []

    with DEX_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            sys.exit("missing CSV header")
        for row in reader:
            dex_num = int(row["dex_num"])
            ingame_name = row["ingame_name"].strip()
            if dex_num not in ENTRIES:
                failures.append(f"#{dex_num}: no catalog entry for {ingame_name}")
                entry = row["dex_entry"].strip()
            else:
                entry = ENTRIES[dex_num]
                row["dex_entry"] = entry
            failures.extend(validate_entry(dex_num, ingame_name, entry))
            row["char_count"] = str(len(entry))
            rows.append(row)

    if failures:
        for msg in failures:
            print(f"VALIDATION FAILED: {msg}", file=sys.stderr)
        return 1

    with DEX_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    dex_by_slug = {row["slug"].strip(): row for row in rows}
    matrix_rows: list[dict[str, str]] = []
    with MATRIX_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        matrix_fieldnames = reader.fieldnames
        if matrix_fieldnames is None:
            sys.exit("missing matrix CSV header")
        for row in reader:
            slug = row["slug"].strip()
            if slug in dex_by_slug:
                src = dex_by_slug[slug]
                row["dex_entry"] = src["dex_entry"]
                row["char_count"] = src["char_count"]
            matrix_rows.append(row)

    with MATRIX_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=matrix_fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(matrix_rows)

    result = subprocess.run([sys.executable, str(APPLY_SCRIPT)], cwd=ROOT)
    if result.returncode != 0:
        return result.returncode

    print(f"Catalog applied {len(rows)} dex entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
