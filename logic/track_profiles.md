# TRACK PROFILES & BIAS KNOWLEDGE BASE

## 1. SARATOGA (NY)
**Tier:** Tier 1 (Premier/Elite) - *The "Graveyard of Champions"*
* **Par Adjustment:** **+15 Lengths** vs Tier 3 (Parx). Form here is the industry maximum.
* **Dirt Profile:**
    * **Surface:** Deep, sandy loam. Tires horses out. High energy expenditure.
    * **Bias:** **DEAD RAIL** (1-2 path often deep/slow). Avoid rail runners in sprints.
    * **Run Style:** Favors Stalkers/Closers. Front-runners often decelerate rapidly due to the deep cushion.
    * **6F Sprints:** "Wire-to-Wire" is difficult. Post 1 is a disadvantage.
* **Turf Profile:**
    * **Inner Turf:** Tight turns. **Speed Favoring**. Inside posts (1-4) dominant.
    * **Outer (Mellon) Turf:** Wide turns. Fair / Closer Friendly.
* **Algorithmic Flag:** Downgrade "Need-the-Lead" (E) types with low stamina. Upgrade Stalkers.

## 2. GULFSTREAM PARK (FL)
**Tier:** **DYNAMIC** (Tier 1 Dec-Mar / Tier 2 Apr-Nov)
* **Par Adjustment:** Winter (+10 Lengths), Summer (+3 Lengths).
* **Dirt Profile:** "The Conveyor Belt."
    * **Surface:** Hard, fast, sandy. Kickback is severe.
    * **Bias:** **GOLDEN RAIL**. Speed and the Rail are dominant.
    * **Run Style:** **Wire-to-Wire**. If you miss the break, you lose.
    * **One-Turn Mile:** Plays like a long sprint. Speed carries.
* **Turf Profile:** "The Parking Lot."
    * **Geometry:** Extremely tight turns.
    * **Bias:** Wide trips are death. Inside posts and tactical speed are essential. Deep closers struggle.
* **Tapeta:** Treats as **Surface_Turf_Synthetic**. Fairer than dirt.

## 3. SANTA ANITA (CA)
**Tier:** Tier 1 (Premier West)
* **Par Adjustment:** **+10 Lengths** (Insulated Economy).
* **Dirt Profile:**
    * **Condition:** Fast/Standard = Speed Favoring. **Wet/Sealed = DEAD RAIL** (Bias Inversion).
    * **Bias:** Sprints (5.5/6F) dominated by Front-runners (>60%).
* **Turf Profile:**
    * **Hillside Course (6.5F):** **Closer's Course**. Right-hand turn start disadvantages the rail. Speed often goes too fast.
    * **Flat Oval:** Fair. Speed holds better than the Hillside.
* **Class Note:** "Cal-Bred" vs "Open" is a steep jump (5-7 Beyer points).

## 4. DEL MAR (CA)
**Tier:** Tier 1 (Premier Summer)
* **Par Adjustment:** **+10 Lengths** (Watch for "Ship & Win" bonus chasers inflating fields).
* **Dirt Profile:**
    * **Geometry:** Short Stretch (919 ft).
    * **Bias:** **Speed/Presser Favoring** (2024 Trend). Inside posts (1-3) win 55% of routes.
* **Turf Profile:**
    * **Bias:** Narrow course, but often a "Hot Pace" melts the speed. Favors **Stalkers**.
    * **Surface:** Very Firm. Europeans/East Coasters may find it too hard.

## 5. KEENELAND (KY)
**Tier:** Tier 1 (Boutique)
* **Par Adjustment:** **+12 Lengths** (Huge field sizes inflate difficulty).
* **Dirt Profile:**
    * **Geometry:** Short stretch (Finish at 1/16th pole).
    * **Bias:** "Fair" but 1/16th pole finish helps Pressers/Stalkers hold on. Wire-to-Wire is rare. Inside speed favored in Routes.
* **Turf Profile:**
    * **Geometry:** Wide, sweeping turns.
    * **Bias:** **Closer Friendly**. You can win from last.
    * **Wesley Ward Factor:** In April, Wesley Ward 2YO turf sprinters are a massive statistical bias.

## 6. CHURCHILL DOWNS (KY)
**Tier:** Tier 1 (Major)
* **Par Adjustment:** **+9 Lengths**.
* **Dirt Profile:**
    * **Surface:** **"Cuppy"** (breaks away). Horse-for-Course is critical.
    * **Bias:** One-Turn Mile favors speed (Cutback angle). Rail is dangerous unless track is Sloppy.
* **Turf Profile:**
    * **Trend:** Shifting toward **Speed**. Gulfstream shippers often get loose on the lead here.

## 7. AQUEDUCT (NY)
**Tier:** Tier 2 (Winter) / Tier 1.5 (Spring/Fall)
* **Par Adjustment:** Winter (+6 Lengths), Spring/Fall (+8 Lengths).
* **Dirt Profile:**
    * **Winter:** **DEAD RAIL**. Jockeys ride 3-4 wide. Outside Flow is the bias.
    * **Bias:** Sprints still favor speed, but "Outside Speed" is better than Rail Speed.
* **Turf Profile:**
    * **Inner:** Tight/Inside.
    * **Outer:** Fair.

## 8. BELMONT PARK (NY - "Big Sandy")
**Tier:** Tier 1 (Elite)
* **Par Adjustment:** **+12 Lengths**.
* **Dirt Profile:**
    * **Geometry:** Massive 1.5-mile oval. Sweeping turns.
    * **Bias:** **Closer's Paradise**. Wide turns maintain momentum. One-turn routes favor "Outside Flow."
* **Turf Profile:** Fairest in America. Euro shippers excel.

---

## 9. PAR ADJUSTMENT MATRIX (CLASS EQUALIZATION)
*Use this to normalize Speed Figures to a standard "Parx (Tier 3)" baseline.*

| Source Track | Adj (Lengths) | Adj (Beyer Pts) | Note |
| :--- | :--- | :--- | :--- |
| **Saratoga** | +6.0 | **+15** | Max strength |
| **Del Mar** | +5.0 | **+12** | Summer Elite |
| **Keeneland** | +5.0 | **+12** | Huge Fields |
| **Belmont** | +5.0 | **+12** | Stamina Test |
| **Santa Anita** | +4.5 | **+10** | Insulated |
| **Gulfstream (W)** | +4.5 | **+10** | Jan-Mar Only |
| **Churchill** | +4.0 | **+9** | Cuppy Surface |
| **Aqueduct** | +2.5 | **+6** | Winter Grind |
| **Parx** | 0.0 | **0** | Baseline |

**ALGORITHMIC FORMULA:**
`Normalized_Speed = Raw_Figure + (Source_Adj - Target_Adj)`
*Example: A 75 at Saratoga (+15) = A 90 at Parx (0).*