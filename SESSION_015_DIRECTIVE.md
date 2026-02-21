# Session 015 Directive

**Initialize Session 015 — Balance and Tier Integration.** 
Two focused fixes:

1. **Battle Balance:** 
   * Increase player squad base stats by +25% across Rex, Brom, and Pip. 
   * SHIELD taunt must actively redirect SWORD targeting — if a SHIELD unit has taunted, enemy SWORD units must target it preferentially over lower-HP units. 
   * STAFF heal amount should scale with missing HP, not a flat value. 
   * Add a difficulty setting to the overworld: Easy/Normal/Hard adjusting enemy stats by -20%/0%/+20%.

2. **Tier Integration:** 
   * When a node is clicked on the overworld, launch `territorial_grid.py` first as the mid-tier battle. 
   * The outcome of the territorial grid battle — Blue win or Red win — determines who won that region, and THEN triggers a 3v3 auto-battle as the 'final skirmish' to confirm the result. 
   * If the player wins the grid, they enter auto-battle with a stat bonus. 
   * If the player loses the grid, they enter auto-battle at a disadvantage. 
   * The overworld node result reflects the auto-battle outcome.

3. **Maintenance:**
   * All 7 slime_clan tests must still pass. 
   * Update `PLAN.md` with the three-tier war system description.
