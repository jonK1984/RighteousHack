You are implementing Jon Kakaley's RighteousHack Knight quest redesign in jonK1984/RighteousHack (a Christian NetHack 5.0 variant). Work ONE STEP AT A TIME. This launch is STEP 1 ONLY. Later steps will arrive as follow-up messages. Do not start any step until told.

HARD RULES
- Create branch `knight-quest` from `righteoushack-0.1`. All steps go on this one branch. Open ONE draft PR into `righteoushack-0.1` after step 1 and keep pushing to it. Never open other PRs. Never touch NetHack/NetHack upstream. Never merge.
- Do exactly the spec; no extra mechanics, no extra text. All player-visible text below is approved VERBATIM; use it exactly (no em dashes, no edits). If you need any player-visible text not listed, STOP and report it instead of inventing it.
- Nothing occult. Never quote the Apocrypha.
- Keep EDITLEVEL at 20. Must build with Windows MSVC nmake (Jon builds in C:\CODE\RighteousHack) and on Linux. Run all `test/*_checks.py` and keep them passing; add a focused test for each step.
- Naming: "Silene", "King Constantine", "Princess Isabel", "Ixoth", "Ixoth's brood", "Captain of the Guards", "Lamp of God's Word", "riding blanket of the heavenly host" (already fully defined artifact; do not change it).
- At the end of each step: commit, push, and report exactly what changed, file list, test results, and anything you could not do.

STEP 1 (do now): Commit this whole spec to `doc/knight-quest-spec.md` (verbatim), then implement the BOG terrain:
- New terrain type "bog", 100% walkable by everyone. Displayed with the SAME symbol as water (`}`) in every symbol set, including DECgraphics/IBMgraphics/curses/enhanced sets and the Windows tiles/GUI where symbol sets apply, colored CLR_BROWN. Farlook / map key / describe calls it "bog".
- When the hero steps onto a bog square while NOT riding: 5% chance to lose exactly one turn, message: "Thy feet sink into the bog."
- While riding (u.usteed): never stuck. The FIRST time ever in a game the hero rides onto bog, message: "Thy steed beareth thee lightly over the bog." (once per game).
- Make it usable from Lua level files (a map character for des.map, plus des.terrain support). Do not place it on any level yet.

======== FULL APPROVED SPEC (for reference; implement only the current step) ========

QUEST OVERVIEW
Home: King Constantine's castle in Silene (Kni-strt). Fillers/locate: three fixed-layout marsh mazes (Marsh's Edge = filler 1, Deep Fen = filler 2, Heart of the Marsh = locate). Goal: vanilla NetHack's Kni-goal Cave of the Dragon layout kept as is, with Ixoth, the riding blanket of the heavenly host (quest artifact), and Princess Isabel.
Completion: Ixoth must be slain AND Isabel brought home. After Ixoth dies, #chat with Isabel; she becomes a tame follower. Isabel is UNKILLABLE. The quest completes when the hero speaks to King Constantine while Isabel is with him (adjacent/on level following). Then the sealed treasury opens; it contains a Lamp of God's Word.

HOME LEVEL MAP (Kni-strt), 76x21. Legend: `}` water/moat, `-|` walls, `+` door, `S` secret door, `T` tree, `.` floor/grass, `=` bridge (walkable, over the brook), `^` portal (in the tiny portal house), `@` stablemaster, `#` hay (decor), `\` throne, `_` altar (to the Lord, lawful), `*` treasury contents spot, `{` fountain, `!` apothecary, `E` engraving, `G` guard, `C` Captain of the Guards, `>` down stairs.
The western `}` curving brook (2 wide, north to south) is a flowing brook of water in the pastures, crossed only by the `==` bridge by the stable. The outer `}` ring is the castle moat; the castle gate/causeway is the `+` at the west wall of the courtyard.
T...................}}......................................................
.-----------------..}}.........T...}-----}}}}}}}}}}}}}}}}}}}}}}}}}}}}}-----}
.|...|...|...|...|...}}............}|...|}}}}}}}}}}}}}}}}}}}}}}}}}}}}}|...|}
.|...|...|...|...|...}}............}|...|-----------------------------|...|}
.--+---+---+---+--....}}...........}|...S.....|........|........|....||...|}
.|...............|....}}.........T.}-----.....|........|........|....|-S---}
.|.......@.......+....}}...........}}}|.......|...\....+...._...|.*..|..|}}}
.|.............##E...==............}}}|.......|........|........|.E..|..|}}}
.-----------------...}}............}}}|.......|........|........|.G..|..|}}}
....................}}.............}G}|.......-----+-------+-------+--..|}}}
..T................}}...------.......E+............G.......G.......G....|}}}
..................T}}...|....|.....}G}|.................................|}}}
....------------..}}....|.^..|.....}}}|.........G.......................|}}}
....|..........|..}}....|....|.T...}}}|.................{....---------..|}}}
....|..........+E.}}....|....|.....}}}|...............G......|....E..|..|}}}
....|..........|...}}...--+---.....}-----....................+...!...|-S---}
....|..........|...}}......E.......}|...S....................|.......||...|}
....------------....}}.............}|...|-----------------------------|...|}
.....................}}...T........}|...|}}}}}}}}}}}}}}}}}}}}}}}}}}}}}|...|}
.T.......T...........}}............}-----}}}}}}}}}}}}}}}}}}}}}}}}}}}}}--.--}
T.................T...}}......T.........................................C>..
Features:
- Stable (northwest): 4 stalls behind locked stall gates. Stall contents: pony, horse, horse, warhorse. All horses tame (to the hero) but unreachable until paid. Prices: pony 500, horse 2500 each, warhorse 7500 gold. Paying the stablemaster opens that stall's gate. Stablemaster lines (verbatim):
  Greeting: "Welcome, good knight, to the King's Stable. Every beast here is gentle and ready for the saddle."
  Offer at a stall: "This %s is thine for %d pieces of gold. Wilt thou buy?"  (%s = pony/horse/warhorse, %d = price)
  Purchase: "Well chosen. The gate is open; take thy steed and ride in the Lord's service."
  Not enough gold: "Thou hast not gold enough for this beast. Return when thy purse is fuller."
  Declined: "As thou wilt. The stall shall wait for thee."
- Knight's shop "The Armoury of Silene" (southwest building). Stock: saddles, lances, long swords, plate mail, ring mail, helmets, large shields, gauntlets, high boots, carrots, apples. Guaranteed minimum: 2 stacks of 10 carrots, 2 stacks of 10 apples, 1 blessed +2 lance, 1 saddle. ALL items in this shop at 2x normal price.
- Apothecary (inside castle, southeast room `!`): sells a couple of anointing oils of healing (existing RighteousHack item). Greeting: "Welcome to the King's apothecary. Here be anointing oils for the healing of wounds."
- Treasury (room with `*`, east of chapel in keep): sealed/unopenable until the quest is complete; contains a Lamp of God's Word.
- Portal back is in the tiny portal house (`^`).
- Spires: 4 corner spires, each with a secret door (S) as drawn. The SE spire has a gap in its bottom wall (the Captain's notch) at the spot directly north of C.
- Engravings (verbatim, on the ground just outside each door, at the E spots):
  Castle gate/causeway: "The Castle of King Constantine of Silene"
  Stable: "The King's Stable. Horses for the Lord's knights."
  Knight's shop: "The Armoury of Silene. Saddles, lances, and the furniture of war."
  Apothecary: "The Apothecary. Anointing oils for the healing of wounds."
  Treasury door: "The King's Treasury. Sealed until the dragon be slain."
  Portal house: "The Wayfarer's House"
- Guards: 8 peaceful castle watchmen at the G spots (2 gate, 2 courtyard, 3 keep doors, 1 treasury). Hostile only if attacked or if the treasury is broken into. On #chat: one gate guard and one courtyard guard say the marsh hint; the other six each say one lore line.
  Hint: "Beware the marshes beyond the stair, good knight. The mire will hold fast a man on foot, but a steed beareth his rider over it lightly."
  Lore 1: "The princess Isabel is fair beyond any maid in Silene. Her beauty is renowned in every land."
  Lore 2: "The King hath fasted and prayed many days that the Lord would send a deliverer."
  Lore 3: "Ixoth came up out of the marshes and poisoned the waters. No herd will drink of them now."
  Lore 4: "The King's treasury is sealed. It shall not be opened until the dragon be slain."
  Lore 5: "The Captain of the Guards letteth no untried knight pass to the marshes."
  Lore 6: "The princess was taken at the brook as she went out to draw water. We heard her cry, but the beast was swift."
- Captain of the Guards (C), peaceful, guards the only path to the down stairs. While on duty he blocks BOTH the stairs path and the SE spire notch. Hero below XL 14: he will not move; says: "Halt, %p. None pass to the marshes but knights proven in battle. Return when thou art stronger." Hero XL 14+: says "Thou art proven, %p. Pass, and God speed thee." then steps aside to a spot that opens both the stair path and the spire notch (the spire becomes a back way in/out of the castle).
- Spawning on home level: occasional weak spawns ONLY in the outer pastures (never inside the castle walls/courtyard/keep or inside any building): newt, gecko, iguana only.

MARSH MAZES (fixed layouts below; `}` here = BOG terrain, walkable). `<` up stairs, `>` down stairs. Each maze has 6 bog-free rest pockets; place one anointing oil of healing in 2 of the pockets on each maze. Maze 3 (locate) has the walled center room with the way down (`>`) entered by its west door `+`.
MAZE 1
---------------------------------------------------------------------------
-<-..}...}..-..}...}....-...}.-...}.}....}}.-.}.-}}}.}..}.}.}}-.....}}....-
-.---.-----}-.-------.---.-}---}---------.---}-.-.-----}-----}-.--....-----
-}-...-}..}}-....}..-..}}}-}-...-}}}...}-}..-.-}-...-.}.-.}.-.-.-}....}...-
-.-.---.-----.....-.-------.-.---------}---.-.-.---.-.---.---.-.-.....---.-
-}-}.}-...}.......-.-....}......}.}}..-.-...-.-.}..}-.-}.}-..}-.......-}..-
-}---.-------....--}-}-----.....-----}-}-.---.-------.-.---}-----.-.-}-.---
-...}.-.....-....}}.-}..-.}........}}.-.-..}-.-....}-}-...-}}}-.-.-}-.-}}.-
-------.-.---.---------.---.....-------}---.-.-}-----}-.-.---.-}-.-}-.---.-
-.-.}.-.-...}.-}}...}.-}}.}.....}.-..}........}}-...}.-.-.-..}-...-..}..-}-
-}-.-.-.-----.....-.-.---.---}---.---.-....---.....------}-.---.---------}-
-.}.-.-}-}..-.......-...-.-.-.....-...-.....}......}.}.}-}-}..-}}.-..}}}}}-
-----.-.-}-}-.....-----}-.-}-------.-.-.....-......--.-.-.---}-----}-----.-
-....}-..}-}......}}}}..-..}.}.}..-.-}-}-.}.-.........-}.}..-}.}}}-}-....}-
-.-------------.-----------------.-.---.-----------}-------------.-.-}-----
-..}..}.}..}}.-.}}.}-...}.}}}..}-...-}}}-}.}.......}-.}.-.....}}-}.}-.-...-
-.---}-------.-----.-.-.-------.---}-.---.-----.-----.-.-}-----.-----.-}-}-
-}-..}-...}.-}..-..}-.-.-.-.}.}.-}..-}.}-}}...-}-.....-}}.-}..-}.}.}-.}.-}-
-.-.---.---.-----.-----.-.-.-----------.-.---.---.---------.-.-.---------.-
-.-...}}..-...}.}}...}..-}}.}}......}...-}.}-..}}}}}.....}}.-}-....}}..}.>-
---------------------------------------------------------------------------

MAZE 2
---------------------------------------------------------------------------
-<}}.}..-..}-}.}}}-....}..-}..}}-.-}......}...-.}.-..}..-}}.}.}.-.}}}}-...-
-------}-.-.-----.-}---.....---.-}-.-----}---.-.-}---.---.---.-.---.-}---}-
-}..}}-}}.-.}.}.-...-}}.......-.}}-}-.-.}}-}}..}-}..-}..}.-...-..}-.-}-}}}-
-}---.---------}-----.-.....-}-----}-.-....--------.-----.-.-----}-}-.-.---
-}-..}}...-}.}-}..-.}}-.....-.}}..-.-.-.....-.}.}...-..}-.-...-.....-.-...-
-.-.-----.---.---.-.---.---.-.---.-}-.-.....---.-----.-}-----.-}....-.---.-
-.-.......}}}...-.-}-.-}}..}-.}.-.-.-.......}.-}}....}-..}}}}.-.....}.-...-
-}-......--------.-.-.-}-------}-.-.---....--.-.---------------.....---}---
-}-}........-}}.-...-}..-.-..}..-.}......}.}-.-}-...}.-}..}..........}....-
-.--.....}-.-.-.-----}---}-.---------------}-.---.---.-.-------.-.-------.-
-.}.-...-.-.}.-.-}....-}}.-}-..}..-.-.}.-...-.....-.-}-.-.}}..-.-.}..}..}.-
-----.-.-----}-.-}-----.---.---.-.-.-}-.---------.-}-}---}---.-.---------}-
-}.}..-.......-.-.-...}.-.}}-..}-}.}-.-.-.}.}..}-}-.....}.-}-.-.}......}-.-
-}------.....--}-}---.-}-}---.-------}-}-}-----}-.-.....---.-}-----.-----.-
-.-............}-}..-}-.}....}-.}...-}-.}.-...-}-.}......}.}-}.}..-.}.-..}-
-}------.....------.-----------}---.-.-----.---.---.....---------}-.-}-.---
-}-...}}.....}..-...-.}.}.....-.}.-.}}-...}..}-...}...-.-..}-...}}-.-}-.-}-
-.-}---.-.-.-}-.-.---.-------.---.-----.-----}-------.---.-.-.-----.-}-.-.-
-...}}-}}.-...-.}.....-}.}........-.}}..}.}}-.}}.....}}}..-...-.....-}}..>-
---------------------------------------------------------------------------

MAZE 3
---------------------------------------------------------------------------
-<...}-..}.}...}}.-.}}}}-}..}.}}....-.-}.}.}}}}..}....}.-}}.-..}-}}.-.}.}}-
-----.-}---------.-}-}---.-----}---}-.-}-----.---------}-.-.-.-}-.-}---.-.-
-}...}-.}}....-..}-.-.-}..-...-}-.}.-}.}-}}}..-...-...-}..-...-.-.-}-.}.-.-
-.-----.-------}---.-.-.---}---.-.-------.-----.-.-.-.---------.-.-}-.---.-
-.-}.}-......}-...-.-..}-.}.-...-.-}}}.}-}-}.}-}-.-}-}..}}-...-...-.-.}.-}-
-.-.-.--......-.-.-.-----.-}-.---}-.---}-.-.-}-}-.-}---.-.---.-----}-.-}-}-
-.-.-..}......-}-.-...-}..-.-}..-}}.-}..-..}-.-.-.-}.}-.-.}......}-.-.-.-}-
-.-.----......-}-}---.-}---.---}-------------.-}-}-----.----......-.---.-.-
-.-...-......}-}-.-...-}..-.}}-.}|.......|.}-.}}-}}}}.-}}.}.......-..}-.-.-
-.---.-----}-}---.-.-----.---}--.+...>...|-}-----.---.-.----.....----}-.-.-
-}}.-.....-}-.-.......}}.}-..}}.-|.......|-..}..-.-.-.-.}.........}...-}-.-
---}-.---.-.-.-.-.....---.---------------------.-.-.-}---------.-}-----.---
-}}.-}-.....-}-.}.......}.-}}}.}..-...-.}..}.}-}-...-}-....}}.-}-}}.-}-.}.-
-.-----.....-.---.....---.-......--.-}-.-----.-.--....-}-----.-}---.-.-.-}-
-}-}.}-.....}}}.......}}-.-......}}}-...-}}...-}......-.-.-...-..}.}-...-}-
-.-.-}-....------------.----.....}----------------....-}-.-.---}---------.-
-}}}-.-.....-.}.-}.}.}-}}........}-}.........}..}......}.}-.-.-.-}}}}.-..}-
-----.-----.-.-}-.-.-------.-.-}-.-}-------------.-.-------.-.-.-.---}-}-}-
-.}.}.}.}.}}-.-}.}-.}.}}}.....-.-}}.}}}}..}.....-...}.}..}..-}}.}.-}}}..-.-
---------------------------------------------------------------------------

Enemies (existing monsters; random generation on these levels drawn from these lists):
  Marsh's Edge: newt, gecko, iguana, baby crocodile, giant beetle.
  Deep Fen: lizard, baby crocodile, water moccasin, snake, Ixoth's brood.
  Heart of the Marsh: crocodile, cobra, pit viper, Ixoth's brood.
"Ixoth's brood" = baby red dragons, displayed/named "Ixoth's brood".

QUEST TEXT (verbatim; %p = player name)
King Constantine first greeting (blackout quest text window):
"Hear me, %p. In the days of my youth the land of Silene was green and fair, and her brooks ran clear.

But there came up out of the marshes a great red dragon, whose name is Ixoth. His breath poisoned the waters, and the pastures withered, and the flocks and herds died in the fields. My people fled from the villages, and the land was laid waste.

Then, upon a day of mourning, the beast came even unto my castle and carried away my daughter, the princess Isabel, fairest of all the maidens of Silene. He bore her into his cave beyond the poisoned marshes, and no knight who went after her hath returned.

Many days have I fasted and prayed that the Lord would send a deliverer. And now thou art come. Blessed be the Lord, for I believe He hath sent thee."
Immediately after, level-dependent:
  Below XL 14: "Yet thou art young in battle, %p, and the marshes would swallow thee. Go forth and gain experience, and grow in strength. When thou art proven, return to me, and I will send thee to deliver my daughter."
  XL 14+: "Thou art proven in battle, %p. Go down by the path at the south of my lands, where the Captain of my Guards keepeth the way. Pass through the poisoned marshes, slay the dragon Ixoth, and bring my daughter home. The Lord go with thee."
Return without victory: "Isabel is yet in the dragon's keeping. Delay not, %p; the Lord go with thee."
King, Ixoth dead but Isabel not with hero: "Where is my daughter, %p? I see her not. Bring her home to me."
Victory (Isabel with hero): "My daughter is restored to me! The Lord hath heard my prayer and sent thee, %p. In my prayers I have sensed a great destiny for thee. Go into the treasury and take the great Lamp of God's Word; let it guide thee in the way thou must go."
Ixoth, blackout text on first entering the goal level:
"So, %p, the old king hath sent another of his tin-clad knights to die. I have feasted upon better men than thee, and their bones lie scattered in my cave.

The princess is mine, and thou shalt never take her from me. Come then, little knight. I shall burn the flesh from thee, and gnaw upon thy bones, and lay thy skull among the rest!"
Isabel #chat after Ixoth dies (she then becomes a tame follower): "Thou hast slain the beast! Blessed be the Lord who sent thee. Wilt thou bring me home to my father?"

EASTER EGG (after quest complete, Isabel at home with the King; #chat with Isabel):
- Male hero: she asks "I loveth thee, %p. Wilt thou marry me?" (yes/no prompt). If no: no reply line; she asks again every later #chat until yes. If yes: "Then I am thine, and thou art mine! Let us tell my father." Afterward (married): Isabel #chat: "My husband, %p! Come home safely to me." King #chat: "Welcome, my son, husband of my daughter. Silene is ever thy home."
- Female hero: never proposes; Isabel says: "Thou art as a sister to me, %p. God keep thee."

PLANNED STEPS (only do the one you are told):
1 bog terrain; 2 home level map (geometry, features placement, engravings, pasture-only spawns); 3 stable purchase mechanic; 4 Knight's shop + apothecary stock/pricing; 5 guards + chat lines + Captain XL14 gate/notch; 6 three marsh mazes (pockets, oils, enemies, Ixoth's brood); 7 goal level (vanilla cave + Isabel + Ixoth taunt); 8 Isabel follower/unkillable/return/completion/treasury/marriage; 9 King quest text + full test pass.
