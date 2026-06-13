@ In-game GBA test for Toepfer wizard front sprites (species 1-151).
@ Hooked from the bedroom sign in Pallet Town. VAR_TOEPFER_FRONT_SPRITE_TEST_INDEX
@ holds 0-based progress; talk again after each battle to advance.

.equ TOEPFER_FRONT_SPRITE_TEST_COUNT, 151

EventScript_WizardFrontSpriteTest::
	lockall
	specialvar VAR_RESULT, CountPartyNonEggMons
	goto_if_eq VAR_RESULT, 0, EventScript_WizardFrontSpriteTest_NoParty
	call EventScript_WizardFrontSpriteTest_PrepareBattle
	compare VAR_RESULT, NO
	goto_if_eq EventScript_WizardFrontSpriteTest_Cancel
	dowildbattle
	addvar VAR_TOEPFER_FRONT_SPRITE_TEST_INDEX, 1
	compare VAR_TOEPFER_FRONT_SPRITE_TEST_INDEX, TOEPFER_FRONT_SPRITE_TEST_COUNT
	goto_if_ge EventScript_WizardFrontSpriteTest_WrapIndex
EventScript_WizardFrontSpriteTest_Cancel::
	releaseall
	end

EventScript_WizardFrontSpriteTest_PrepareBattle::
	copyvar VAR_0x8004, VAR_TOEPFER_FRONT_SPRITE_TEST_INDEX
	addvar VAR_0x8004, SPECIES_BULBASAUR
	copyvar VAR_0x8008, VAR_TOEPFER_FRONT_SPRITE_TEST_INDEX
	addvar VAR_0x8008, 1
	buffernumberstring STR_VAR_1, VAR_0x8008
	bufferspeciesname STR_VAR_2, VAR_0x8004
	setvar VAR_0x8005, 5
	setvar VAR_0x8006, ITEM_NONE
	special CreateEnemyEventMon
	msgbox Text_WizardFrontSpriteTest_Prompt, MSGBOX_YESNO
	return

EventScript_WizardFrontSpriteTest_WrapIndex::
	setvar VAR_TOEPFER_FRONT_SPRITE_TEST_INDEX, 0
	msgbox Text_WizardFrontSpriteTest_Wrapped, MSGBOX_DEFAULT
	releaseall
	end

EventScript_WizardFrontSpriteTest_NoParty::
	msgbox Text_WizardFrontSpriteTest_NoParty, MSGBOX_DEFAULT
	releaseall
	end

Text_WizardFrontSpriteTest_Prompt::
	.string "TOEPFER front sprite test.\p"
	.string "Species {STR_VAR_1}/151:\n"
	.string "{STR_VAR_2}\p"
	.string "Battle to view the front sprite?$"

Text_WizardFrontSpriteTest_Wrapped::
	.string "All 151 species viewed!\p"
	.string "Counter reset to #1.\n"
	.string "Talk again to restart.$"

Text_WizardFrontSpriteTest_NoParty::
	.string "You need a Pokémon in your party.\p"
	.string "Get your starter from PROF. OAK,\n"
	.string "then come back here.$"
