# AttackBot End-to-End Findings Report

- Generated at: `2026-03-25T03:28:12.980203+00:00`
- Report file: `E2E_Runs/E2E_SYSTEM_FINDINGS#5.md`
- Project root: `C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1`
- Test outcome: `failed`
- Error: `Pinned program selector did not resolve to any program. E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'`

## Requested Mode
- Full end-to-end execution attempted against current M3 stack.
- All feature flags were set to `true` in scan start payload.
- Live-mode policy: no seeded/dummy fallback for primary scan.
- Program selection override active via `E2E_PINNED_PROGRAM_HANDLE` / `E2E_PINNED_PROGRAM_ID`.

## Execution Steps
1. 2026-03-25T03:25:08.211856+00:00 | Starting end-to-end system trace test
1. 2026-03-25T03:25:08.212182+00:00 | .env present (loaded 0 missing keys into process env)
1. 2026-03-25T03:25:09.874020+00:00 | Bringing up stack with docker compose up -d
1. 2026-03-25T03:26:02.859767+00:00 | Health probe scraper: status_code=200
1. 2026-03-25T03:26:03.346722+00:00 | Health probe core-engine: status_code=200
1. 2026-03-25T03:26:36.917759+00:00 | Health probe reporter: status_code=None
1. 2026-03-25T03:27:10.137646+00:00 | Health probe attack-graph-engine: status_code=None
1. 2026-03-25T03:27:10.862946+00:00 | Health probe api-gateway: status_code=200
1. 2026-03-25T03:27:11.739856+00:00 | Connected to database backend=docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
1. 2026-03-25T03:27:11.739877+00:00 | Pinned program selector configured: E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'
1. 2026-03-25T03:27:11.739881+00:00 | HackerOne credentials detected; triggering live scraper sync
1. 2026-03-25T03:28:12.225178+00:00 | Scraper trigger request failed; continuing with current live program inventory. error=ReadTimeout: 
1. 2026-03-25T03:28:12.980095+00:00 | Failure captured: Pinned program selector did not resolve to any program. E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'

## Runtime Context
- DB connection backend: `docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit`
- Live HackerOne mode: `False`
- Program source: `None`
- Program selection policy: `pinned_program_handle`
- Pinned program handle override: `weblate`
- Pinned program ID override: `None`
- Program ID: `None`
- Program handle: `None`
- Scan ID: `None`
- Reconciler pause requested (`E2E_PAUSE_RECONCILER`): `True`
- Queue baseline enforcement (`E2E_ENFORCE_QUEUE_BASELINE`): `True`
- Queue pre-purge enabled (`E2E_QUEUE_PURGE_BEFORE_BASELINE`): `True`
- HackerOne username present in process env: `True`
- HackerOne token present in process env: `True`

### Enabled Feature Flags
```json
{}
```

## HackerOne Scrape Trigger
```json
{
  "error": "ReadTimeout: ",
  "payload": null,
  "status_code": null
}
```

## Program Selection Audit
| program_id | handle | name | platform | is_active | valid_in_scope_count | selected | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 70a23677-501b-49ad-8973-53adc554307e | gitlab | GitLab | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 4762a4ab-3e3e-4ae3-af31-0f44f8ad2c05 | formassembly | FormAssembly | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 734881ac-1444-4aaf-955b-219f1e8f60eb | urbandictionary | Urban Dictionary | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 4d7dc2a1-d8a4-4b76-be02-508518751a7a | glassdoor | Glassdoor | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 5e218150-4e91-4bd4-a0c8-051a8445dd60 | stopthehacker | StopTheHacker | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 449b1805-1544-4a0d-8344-5f465ae591a1 | iandunn-projects | Ian Dunn | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 8ea676f5-8147-4474-a1c4-6e305672bbb8 | irccloud | IRCCloud | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| b7896e56-914b-48e1-b3d9-b4ca63dd95bd | khanacademy | Khan Academy | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| bdeffc4f-3420-4ba7-a59b-1c2fcdd2f1df | att | AT&T | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| d827dc8a-55f6-4978-b455-02052cb05940 | automattic | Automattic | hackerone | True | 29 | False | not selected: run pinned to explicit program selector(s) |
| d1493d3a-5cbb-455b-916a-d5dd0099bc23 | coinbase | Coinbase | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| ee0e4c9a-be48-4224-85c1-883094afc97f | publitas | Publitas | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| a5f0b451-5a93-45d5-ac7c-cfeaae141a67 | tinder | Tinder | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 0e7e60ef-f025-462f-bfc2-a910a542aa80 | slack | Slack | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| b1cd5fc1-82c0-46b2-b7e0-720d9d186264 | basecamp | Basecamp | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 758e92e5-cf77-4f28-aecd-a65bb3acbcc6 | x | X / xAI | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| d02d8d9d-6710-4541-bf15-d879ad576d57 | concretecms | Concrete CMS | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 6d92bab8-17ed-4ec2-8c2a-c03568902be0 | priceline | Priceline | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 5be1220b-10c0-493b-9d5c-71074b2293f1 | linkedin | LinkedIn | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 00a723ee-9344-4cc9-b4e8-11cf6399561b | vimeo | Vimeo | hackerone | True | 36 | False | not selected: run pinned to explicit program selector(s) |
| 312a3f8d-e1cf-41cb-aeee-675394c382f9 | wordpress | WordPress | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| 674be257-de51-4e18-9fb1-0cc22d452be3 | mavenlink | Mavenlink | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 0d4b6dd8-e549-49c6-9e96-9998a1ead185 | cloudflare | Cloudflare Public Bug Bounty | hackerone | True | 53 | False | not selected: run pinned to explicit program selector(s) |
| 90bb2cf8-611e-4402-9b95-0fd48da13cd3 | django | Django | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d2b21e99-28bb-42e7-83dd-fd037591912e | rails | Ruby on Rails | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 74f5a1d2-4f91-4456-8a27-624630b4e2ff | phabricator | Phabricator | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 6976c79f-23d5-4d8a-a098-402e9ce565ad | security | HackerOne | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| 20a3f8b9-725b-46dc-8047-3ebf448d7ca0 | getyourguide_vdp | GetYourGuide VDP | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 9491bcff-8ebc-4ff3-b80f-9837ec65b5c1 | tines_automation_vdp | Tines (VDP) | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| ca6af4e6-e99a-4597-90df-03b33fd08be1 | mod_supply_chain_vdp | MOD Supply Chain VDP | hackerone | True | 181 | False | not selected: run pinned to explicit program selector(s) |
| 71eef50f-6fd0-4187-b44f-d09aa0250690 | vercel_platform_protection | Vercel Platform Protection | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| dd215241-281e-4ac0-bdbc-15f9bb02a6af | anduril_industries | Anduril Industries | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 81835478-3086-4404-92c5-27f9804a2ce7 | bose_vdp | Bose (VDP) | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| db03a241-1e8e-488a-8bd1-aec902998195 | twilio | Twilio | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| 7074d761-490b-4a77-a304-f546007271f2 | doordash | DoorDash | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| b71d924c-c4bd-4a49-82f4-f8a2556b8caa | mueller_water_products_vdp | Mueller Water Products (VDP) | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| eb40acd0-f779-475d-80ea-c9fdb0a1a379 | henkel_vdp | Henkel | hackerone | True | 238 | False | not selected: run pinned to explicit program selector(s) |
| 61230f7b-3e94-47d9-a8cd-e1c0ce7cec50 | vueling_vdp | Vueling | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| a6a37658-6a42-4d09-b9b4-4ba126f96cbe | mufg-vdp | MUFG VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| c0befe94-1936-4836-a946-de19a2ce1252 | docusign | DocuSign | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2d3a7473-f4f8-456d-885d-f9e424cdd59b | bankunited | BankUnited | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 05017cf3-58ea-4e1d-a395-fcb7070dc85a | robinhood | Robinhood Markets Bounty | hackerone | True | 25 | False | not selected: run pinned to explicit program selector(s) |
| 566e804b-3b3f-4a4f-9792-5b281b4fe452 | robinhood_markets | Robinhood Markets | hackerone | True | 30 | False | not selected: run pinned to explicit program selector(s) |
| 269ae4bc-7288-430b-ba25-b2e3d27f7ce5 | british_airways_vdp | British Airways VDP | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| b38da6f5-2520-4f81-8d51-06070b5506e7 | regions_financial | Regions Financial | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 898ecc5e-ebb5-4184-a91b-4265bc268287 | vercel-open-source | Vercel Open Source | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| be6e6a40-e4a2-4e2c-941e-423623e07213 | netscaler_public_program | NetScaler Public Program | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 219153aa-9f2c-494f-b732-9ae6f19f8c40 | lovable-vdp | Lovable VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 8ee0cbcf-d004-49ea-b4ea-0daf7ba4a875 | hack_the_box | Hack The Box | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| e3b68177-7ca2-4e06-aa91-e659fa16ab55 | banco_plata | Banco Plata | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| c89c44b3-effd-420d-85d5-eaca86b16f70 | braze_inc | Braze, Inc. | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 8e039c2b-5818-427d-842e-fe41296439fd | meesho_bbp | Meesho | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| ed003630-9af7-4fe8-9b86-85d8b01310d7 | tucows_vdp | Tucows (VDP) | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| 72f31304-df63-4111-a782-adb5265d893d | tbs-sct | Treasury Board of Canada Secretariat/Secrétariat du Conseil du Trésor du Canada | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| ede248e5-c509-4303-9c15-ab92e2f99726 | citi_group | Citi Group | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| d593f81d-5dcc-4468-9414-7bff84945854 | kong | Kong | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| abb7a82c-e1a3-4027-9c66-cd54bbb88a2b | worldpay | Worldpay | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| a84a19cd-a660-4c27-8d99-61ddcb8c1706 | hertz | Hertz VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| d4f4c704-eb42-484f-a64d-e014309a803b | experian | Experian | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 3a98f922-9f3b-4452-9935-86dc848fd697 | hexagon_vdp | Hexagon-VDP | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| feac897b-3b3b-447d-b294-4927de2c5439 | eightfold | Eightfold | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 86690668-6516-4cd6-8a4e-5cbc36537d18 | centene_vdp | Centene_vdp | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 295207d7-35d1-4dc4-921d-143042ce2e16 | msci | MSCI | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 194506a4-1aa2-4b9d-85e3-e2c9bb4960ff | ferrero | Ferrero | hackerone | True | 274 | False | not selected: run pinned to explicit program selector(s) |
| e0089518-eccf-4d5d-9c25-6209c6931ba9 | dust | Dust | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 5e3b7b5e-d2f4-41dc-9840-e6a9f01fb64c | hotmartvdp | Hotmart (VDP) | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 0155f17e-a3e0-4691-86b0-3ff294ba1ba7 | hex | Hex | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 77474b31-fdaa-4f8d-82cf-408ff1761ed9 | hyland_software | Hyland Software | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| b02fad84-ad38-4039-a5b3-663e00f2b849 | whoop_bug_bounty | Whoop Bug Bounty | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| d00106d6-6b1f-447a-becc-6624997fae4a | baird_vdp | Baird | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 44f09866-6c9c-49e4-afb2-68a8772d1e36 | northerntechhq | Northern.tech | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 93cfbe68-2372-4a98-bf8b-28917770f5c3 | alibaba_vdp | Alibaba VDP | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 25cd9689-e9d6-40b0-b2dc-ec53ecf366bf | hemi_labs_vdp | Hemi VDP | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 17acf38e-c8f9-4ece-bbb7-1551315cc024 | kraken-tech | Kraken Tech | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 1f4ab341-bdc0-47f6-850d-82a304dd8281 | bcny | The Browser Company of NYC | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| c53b3bf6-9c11-41d1-a837-16f7f3b1f1c3 | 1password | 1Password - Enterprise Password Manager | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| fbedff71-6ef9-42e4-b980-d0e059d58f74 | 1password_ctf | 1Password - CTF | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| ca2c44a7-8391-470c-995e-c16319875b9f | neon_bbp | Neon | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 47cc4f05-a660-4464-a811-e4bfa846dcf9 | penn_entertainment | Penn Entertainment | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| f2a39ae3-df0c-4b08-b9e3-59c35790a881 | kaseya | Kaseya | hackerone | True | 38 | False | not selected: run pinned to explicit program selector(s) |
| 345cbe5c-deb1-425d-802a-d0a49fd26d10 | oppo_bbp | OPPO | hackerone | True | 124 | False | not selected: run pinned to explicit program selector(s) |
| a65c2ec5-b55e-4ed8-b333-51b0743cf2f1 | hubspot | HubSpot | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| 87f36d6d-3ac2-4e07-a941-a18659fc4092 | adevinta_vdp | Adevinta | hackerone | True | 23 | False | not selected: run pinned to explicit program selector(s) |
| 97059d16-476d-420a-a247-281e46748065 | verily_life_sciences | Verily Life Sciences | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 2ba089c1-dc4a-41b8-b5a6-b38214bbe2ed | syfe_bbp | Syfe | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 153534f3-3ca3-4589-9a1f-ad560c850c0a | qinetiq | QinetiQ Response | hackerone | True | 30 | False | not selected: run pinned to explicit program selector(s) |
| 940b3874-0869-43ca-9058-183e18025d08 | recreation_gov_vdp | Recreation.gov | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 0135b291-f664-4c95-bbb1-770faae5473a | pepsico_vdp | PepsiCo VDP | hackerone | True | 216 | False | not selected: run pinned to explicit program selector(s) |
| 7db9b4a6-0cb9-422a-b6fe-d032efa8ad83 | nba-public | NBA Public Bug Bounty | hackerone | True | 142 | False | not selected: run pinned to explicit program selector(s) |
| ddb18e11-e0df-4f28-b6c3-eef73f4e4260 | supabase | Supabase | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 1ece87a4-84b2-4b14-9b52-2daeacd45730 | bill_vdp | BILL VDP | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 082d061e-2d21-416e-9109-a8362f7a7155 | starbucks_japan | Starbucks Japan | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| fd0f95f7-9c11-4e93-9878-56900755bd96 | starbucks_china | Starbucks China | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 7993a349-3d37-4fe0-b421-441f34987838 | liverpool_victoria | Liverpool Victoria | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 4d89518c-b2a5-4e19-b65f-01cc8c645282 | itau_unibanco | Itaú Unibanco | hackerone | True | 138 | False | not selected: run pinned to explicit program selector(s) |
| 3a3806f2-ea4b-4a12-978e-a7628b004636 | aws_vdp | AWS VDP | hackerone | True | 558 | False | not selected: run pinned to explicit program selector(s) |
| 7324e25d-f886-4654-9bbe-153b28431a9b | varonis | Varonis | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 72341e61-ee4b-4e10-b309-223dde7a4539 | circle-bbp | Circle BBP | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| acebf9fc-c445-4f21-bb3d-2d5636ad65d9 | bumba_bbp | Bumba | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| f527b616-af4b-46a1-92bc-a7511f7120f1 | lpl_financial-vdp | LPL Financial VDP | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 921a2feb-229e-4f0c-9594-88e527cf887f | peloton | Peloton | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| a38e650f-9210-4111-9c1b-7d8bb41866d4 | 6sense-vdp | 6sense VDP | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 746b9168-fd60-47ca-9f0a-c8b896129a90 | anthropic-vdp | Anthropic (VDP) | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 9ac7e39f-7c69-4157-a36c-ce1d6ab4472b | finnair_vdp | Finnair Vulnerability Disclosure | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2f192a03-2a2d-4c6d-a01e-fdd5957a616e | hpe_vdp | HPE VDP | hackerone | True | 207 | False | not selected: run pinned to explicit program selector(s) |
| 849c1c99-a6c0-461e-895b-045f21e7f7bc | mintel | Mintel | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| dce88433-4d00-4943-b88b-a42fbb4528b3 | klarna | Klarna | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 175166a4-f757-416b-ab13-102e7abe1c0b | wallet_on_telegram | Wallet on Telegram | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 3f14582d-fce7-4faf-adda-722a4b798715 | ion | ION Group | hackerone | True | 1352 | False | not selected: run pinned to explicit program selector(s) |
| 28fcf7e4-2c63-4b88-b696-926505681efb | tomtom | TomTom | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 4ea4dd8c-dd5a-41ee-b690-9899b6fc9bbe | nimiq | Nimiq | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| bcf2078a-aff7-4d04-a65f-4a0c02d2741e | singlestore | SingleStore | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 8390996b-e090-46fd-8900-383f45af3ecc | lowes | Lowe's Companies VDP | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 16505944-1743-46d2-83fa-0ea52a93ec51 | porsche | Porsche | hackerone | True | 111 | False | not selected: run pinned to explicit program selector(s) |
| 6c4ea566-26eb-4ca9-a6fb-ab38cb9c58e2 | chia_network | Chia Network | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 5e14c7c5-07a8-4e6c-9cd8-c7e71e10b8ed | interco_vdp | Inter & Co. VDP | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| 7a6cd785-d593-4fe6-8be7-2be081928cfc | unico_idtech | Unico IDtech | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| e6fffff4-80a9-41c6-b62e-e2555ffa3015 | corebridge_financial | Corebridge Financial | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| 5a8d1d93-5da6-4157-91e0-a73e0a92c983 | wellhive | WellHive | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 2e7e3f5d-8ada-400f-9014-23eb70822861 | netflix | Netflix | hackerone | True | 30 | False | not selected: run pinned to explicit program selector(s) |
| bafe79e1-1f81-4d42-9483-68b03c05d0b6 | banco_bmg | Banco BMG VDP | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| ee23e009-2cc0-4725-9026-e58e0bf6ffa4 | dailypay_vdp | DailyPay VDP | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| f7fddd77-c199-4e78-83bd-10ee375e1216 | temu | Temu | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| c1f6492b-87f2-418c-ad79-d95ea9fc2476 | 23andme_bbp | 23andMe Bug Bounty | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 197acc8b-6050-49a0-9980-eb024c618651 | privy-bbp | Privy (Bounty) | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| f27237a5-1ba9-4ad8-b5bb-a0442edab0ed | audible | Audible | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 9401c467-e244-448a-9d7b-f75e210f1c70 | aeromexico_vdp | Aeromexico VDP | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 0f2faa42-8692-4df0-adbb-97a1b4f880aa | 3cx | 3CX | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 1c0232d6-538c-421a-b8a3-6a3cfb29e96c | vectra_ai_vdp | Vectra AI, Inc. (Response) | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| ee6bab54-b009-4131-8230-5dd43cdaa4de | bybit_fintech | Bybit Fintech Ltd | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 0ba9fcc8-d483-4836-93bc-b0891f6d88f7 | transunion | TransUnion LLC | hackerone | True | 135 | False | not selected: run pinned to explicit program selector(s) |
| 341e7a8c-ab28-40b9-ac4c-5246511b7108 | trip_com | Trip.com | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 09f3fdec-3981-4d5a-b9c3-cc61f261a945 | inditex | Inditex | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| b9cb60a6-a627-4fb4-ad3b-a715875db188 | leather_wallet | Leather Wallet | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| bb3562cb-1a91-4c5c-a84f-e034371ccec1 | fireblocks_mpc | Fireblocks MPC | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 23619d41-3791-45cf-aea9-c28b78bfc447 | lightspark_bbp | Lightspark BBP | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 2137586b-b008-415d-85f2-23ff587d6800 | aon | Aon | hackerone | True | 264 | False | not selected: run pinned to explicit program selector(s) |
| b98dee25-9890-4ca8-a061-70496ce904d3 | bykea | Bykea | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 3f8347c3-225c-4302-bfeb-0c2747932e9c | aven_response | Aven (Response) | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| dd2c2e91-74e3-4bb2-9223-b86f7cc519ef | oaknorth_bank | OakNorth Bank | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| e602eef3-5357-4745-87fe-05add1e3e6b5 | roke_vdp | Roke | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| eff772b5-1531-49d6-a30a-c33089f5b855 | aboitizpower_corporation | AboitizPower | hackerone | True | 71 | False | not selected: run pinned to explicit program selector(s) |
| 7cc8dbc1-2c0c-4278-aa4d-2c965844b39a | visa | Visa | hackerone | True | 111 | False | not selected: run pinned to explicit program selector(s) |
| 54126f82-aad1-4308-a294-a1c4c68e6895 | alshaya | Alshaya | hackerone | True | 166 | False | not selected: run pinned to explicit program selector(s) |
| dd2d06f9-ccf7-46d0-96c1-0c59ff761cff | toolsforhumanity | Tools for Humanity | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 3be932b8-fdd9-4ff6-a19e-f013d12056f1 | ring | Ring | hackerone | True | 30 | False | not selected: run pinned to explicit program selector(s) |
| ba0e7c1f-17b9-45e8-b1aa-fe6883dc1923 | eurofins | Eurofins | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| d9f269a7-ab0e-4858-a959-d2a14f6d0405 | six-group | SIX Group | hackerone | True | 56 | False | not selected: run pinned to explicit program selector(s) |
| 0b7b00bc-6299-4014-a878-140ceb7834b6 | brightspeed | Brightspeed | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| b947214a-7683-4b57-9885-b4096831fb9c | eufy_security | eufy Security | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 14e786e0-4005-4c25-b6c0-138cc19e4ef7 | eero | eero | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 55429276-a7e3-4b1c-b750-f7effd7acd6c | truist_financial | Truist Financial | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| f3b52586-ed0e-4d31-a491-ff79ea0012c8 | fertitta_entertainment | Fertitta Entertainment | hackerone | True | 22 | False | not selected: run pinned to explicit program selector(s) |
| 85c30330-4939-4ce3-87d2-5f887acd1dd4 | mozilla | Mozilla | hackerone | True | 29 | False | not selected: run pinned to explicit program selector(s) |
| ddf08ab8-ad77-4f47-9325-6524b89ea264 | stripchat | Stripchat | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 613dbb33-88e2-48de-9a34-1c45ea7def6e | tron_dao | TRON DAO | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 8ec6d75a-2e1f-40f6-921d-d93f2e17431b | redox_bbp | Redox | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 39e4b656-407a-4b54-bc2d-fe3b1c7f0bbc | okg | OKG | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| f3ea0780-d119-4d6f-9caf-ac511dd3d248 | superbet | Superbet | hackerone | True | 25 | False | not selected: run pinned to explicit program selector(s) |
| a543452f-a58d-4a0a-b904-1d455e9eda3a | abn_amro_vdp | ABN AMRO Bank VDP | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 3681e0c6-db18-4d17-ab03-2303e8742818 | pornbox | PornBox | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 1f5189f2-1c90-4a11-a3ba-381f3b88f483 | greenfly | Greenfly | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 4657ef79-95ca-41f6-a710-1c681b563963 | magic-eden | Magic Eden | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| a0a83ed8-f012-47d7-86ca-ee8a354a0d41 | boozt | Boozt Fashion AB | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 7ff54905-9efd-45ae-bc2e-45b3fe5fd0a7 | one_zero_vdp | ONE ZERO VDP | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| c8eb9c55-6fed-4e7a-a933-b5b7130a9648 | vodafone_oman | Vodafone Oman | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| a179fc27-2641-48ed-bd3b-a256922da341 | intuit_rdp | Intuit | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| cdee39cf-7247-43bd-a30c-9a6bad52f3c5 | indrive | inDrive | hackerone | True | 118 | False | not selected: run pinned to explicit program selector(s) |
| 9fbb52a6-2e45-47b7-a762-c892f6019ae9 | alsco | ALSCO | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 9a9515b5-fd35-4ac3-9f7e-ed8c98287130 | frontegg | Frontegg | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| ed22ae29-09a0-4fbd-b8d3-72c880b2e4e1 | zerobounce | ZeroBounce | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 139f07e0-0f81-4514-9972-a9983847f865 | sheer_bbp | Sheer | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| d5189175-a9d7-4404-96dd-15ec0f55c18b | rei_vdp | REI VDP | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 370d7ec0-4514-46d9-ba00-c4bae14e5e21 | rei_bbp | REI BBP | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 5e1f5580-475e-45aa-b8a5-5fe3e2c91292 | coinhako | Coinhako | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 3261f791-5f60-4706-bd8d-4c2b9a11abce | mergify | Mergify | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| bc40b716-7731-4eb2-81a8-ce106bb9e705 | arkose_labs | Arkose Labs | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 97e36415-3126-4c5f-bf87-1d3de61102a6 | fifth_third_bank_vdp | Fifth Third Bank VDP | hackerone | True | 69 | False | not selected: run pinned to explicit program selector(s) |
| 48c56560-ab0c-4f09-bf03-1d4f234dd239 | zabbix | Zabbix | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 22ecdf2a-f75a-4f03-8ba9-249e7359656f | abb | ABB Information Systems Ltd | hackerone | True | 1038 | False | not selected: run pinned to explicit program selector(s) |
| a0b8d31c-60b1-4931-8d84-cfd55c40c5ac | abercrombie_fitch | Abercrombie & Fitch Management Co. | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| e274e190-ac90-45b1-95d8-901d3dea9c44 | kkr_vdp | KKR-VDP | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 94228443-d84f-4069-9362-e5f0ea8d1c87 | yuga_labs | Yuga Labs | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 8ef6916d-92c8-4c51-afde-28b6ab685cad | productboard | ProductBoard, Inc. | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 90dbfcd9-7ba3-4aa1-9186-2bad77a50404 | wisdomtree | WisdomTree, Inc. | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 9b66a2ac-dac7-4b83-8ffa-a6f76baa6e90 | notion | Notion Labs, Inc. | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| c131678d-4379-4a72-a8a1-a0b612e5e6a2 | dynamic_labs | Dynamic Labs | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 14231582-9ec5-4bb3-a1f4-1a4455cb30ac | modern_treasury | Modern Treasury | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| de9f5ff5-7595-42c4-9afa-06f8dd775acf | fireblocks | Fireblocks | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| f83bb6b7-7be4-462d-9b54-dcd0a3af4569 | city_of_los_angeles_vdp | City of Los Angeles | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 1ea9410c-c4d9-4d99-bca0-89f6c25f90ea | canada_goose_inc | Canada Goose Inc. | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 553d08c3-e702-42ac-a129-53cb015a4c5e | resmed | ResMed | hackerone | True | 63 | False | not selected: run pinned to explicit program selector(s) |
| 31455b6e-1c31-465c-b911-561356fdf9a6 | daimler_truck | Daimler Truck | hackerone | True | 272 | False | not selected: run pinned to explicit program selector(s) |
| d22348a2-5489-4dea-ae05-68cc40070a47 | avalara | Avalara | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| badaf7b3-f397-4348-8c11-521993b7705a | mpesa | M-Pesa Africa Limited | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 1ab4c569-a10c-476b-9b70-0d965f035a33 | monarch_money | Monarch Money | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 5f124795-52ca-47b3-af5e-b85383b25dc0 | render | Render | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 2e732b0f-df2c-49e4-8e2a-23cbe2da1e9a | floqast | FloQast | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 402d28a4-00a2-46b0-962d-04977b468a28 | metamask | MetaMask | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 384627f0-a5f6-488e-aa0e-d9ff74854e20 | prudential-financial | Prudential Financial | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |

### Program Scope Used
_None_

## Service Health
| service | http_status | health_status | error |
| --- | --- | --- | --- |
| scraper | 200 | healthy |  |
| core-engine | 200 | healthy |  |
| reporter |  |  | All connection attempts failed |
| attack-graph-engine |  |  | All connection attempts failed |
| api-gateway | 200 | healthy |  |

## Scan Summary
### Start Response
```json
{}
```

### Final Scan Row
```json
{}
```

### Scan Wait Result
```json
{}
```

### Pipeline Stage Timeline
_None_

### Artifact Counts
```json
{}
```

### Findings by Severity
_None_

### Findings by Source
_None_

### Detailed Findings
_None_

## Queue and Worker Evidence
### Core DLQ Inspect API
```json
{}
```

### Queue Baseline Purge
```json
{}
```

### Queue Baseline Wait
```json
{}
```

### RabbitMQ Queue States
_None_

## API Snapshots
### /scans/{scan_id}
```json
{}
```

### /scans/{scan_id}/findings
```json
{}
```

## Forced Deep Trace (Downstream Replay)
_Not executed._

## Process Evidence
### Command: docker compose up -d
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env up -d`

```text
STDOUT:
<empty>

STDERR:
 Container attackbot-postgres-1 Running 
 Container attackbot-neo4j-1 Running 
 Container attackbot-redis-1 Running 
 Container attackbot-loki-1 Running 
 Container attackbot-prometheus-1 Running 
 Container attackbot-minio-1 Running 
 Container attackbot-vault-1 Running 
 Container attackbot-rabbitmq-1 Running 
 Container attackbot-attack-graph-engine-1 Running 
 Container attackbot-grafana-1 Running 
 Container attackbot-reporter-1 Running 
 Container attackbot-scraper-1 Running 
 Container attackbot-core-engine-1 Recreate 
 Container attackbot-reporter-worker-1 Running 
 Container attackbot-core-engine-1 Recreated 
 Container attackbot-api-fuzzer-worker-1 Running 
 Container attackbot-ai-analysis-worker-1 Running 
 Container attackbot-api-gateway-1 Running 
 Container attackbot-js-analysis-worker-1 Running 
 Container attackbot-core-worker-1 Recreate 
 Container attackbot-exploit-verifier-1 Running 
 Container attackbot-browser-worker-1 Running 
 Container attackbot-scenario-runner-1 Running 
 Container attackbot-core-worker-1 Recreated 
 Container attackbot-tempo-1 Starting 
 Container attackbot-minio-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-vault-1 Waiting 
 Container attackbot-tempo-1 Started 
 Container attackbot-minio-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-minio-init-1 Starting 
 Container attackbot-migrate-1 Starting 
 Container attackbot-vault-1 Healthy 
 Container attackbot-vault-init-1 Starting 
 Container attackbot-minio-init-1 Started 
 Container attackbot-migrate-1 Started 
 Container attackbot-redis-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-neo4j-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-vault-init-1 Started 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-neo4j-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-redis-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-migrate-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-migrate-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-core-engine-1 Starting 
 Container attackbot-core-engine-1 Started 
 Container attackbot-attack-graph-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-scraper-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-reporter-1 Healthy 
 Container attackbot-scraper-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-attack-graph-engine-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-reporter-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-worker-1 Starting 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-worker-1 Started 

```

### Command: docker compose ps
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env ps`

```text
STDOUT:
NAME                              IMAGE                           COMMAND                  SERVICE               CREATED          STATUS                          PORTS
attackbot-ai-analysis-worker-1    attackbot-ai-analysis-worker    "celery -A backend.sâ€¦"   ai-analysis-worker    4 minutes ago    Up 3 minutes                    
attackbot-api-fuzzer-worker-1     attackbot-api-fuzzer-worker     "celery -A backend.sâ€¦"   api-fuzzer-worker     4 minutes ago    Up 3 minutes                    
attackbot-api-gateway-1           attackbot-api-gateway           "uvicorn backend.serâ€¦"   api-gateway           40 minutes ago   Up 39 minutes (unhealthy)       0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
attackbot-attack-graph-engine-1   attackbot-attack-graph-engine   "uvicorn backend.serâ€¦"   attack-graph-engine   41 minutes ago   Up 40 minutes (healthy)         8006/tcp
attackbot-browser-worker-1        attackbot-browser-worker        "celery -A backend.sâ€¦"   browser-worker        4 minutes ago    Up 3 minutes                    
attackbot-core-engine-1           attackbot-core-engine           "uvicorn backend.serâ€¦"   core-engine           52 seconds ago   Up 44 seconds (healthy)         0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
attackbot-core-worker-1           attackbot-core-worker           "celery -A backend.sâ€¦"   core-worker           50 seconds ago   Up Less than a second           8002/tcp
attackbot-exploit-verifier-1      attackbot-exploit-verifier      "celery -A backend.sâ€¦"   exploit-verifier      4 minutes ago    Up 3 minutes                    
attackbot-grafana-1               grafana/grafana:latest          "/run.sh"                grafana               41 minutes ago   Up 40 minutes                   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
attackbot-js-analysis-worker-1    attackbot-js-analysis-worker    "celery -A backend.sâ€¦"   js-analysis-worker    4 minutes ago    Up 3 minutes                    
attackbot-loki-1                  grafana/loki:latest             "/usr/bin/loki -confâ€¦"   loki                  41 minutes ago   Up 40 minutes                   3100/tcp
attackbot-minio-1                 minio/minio                     "/usr/bin/docker-entâ€¦"   minio                 41 minutes ago   Up 40 minutes (healthy)         9000/tcp
attackbot-neo4j-1                 neo4j:5-community               "tini -g -- /startupâ€¦"   neo4j                 41 minutes ago   Up 40 minutes (healthy)         7473-7474/tcp, 7687/tcp
attackbot-postgres-1              postgres:16                     "docker-entrypoint.sâ€¦"   postgres              41 minutes ago   Up 40 minutes (healthy)         0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
attackbot-prometheus-1            prom/prometheus:latest          "/bin/prometheus --câ€¦"   prometheus            41 minutes ago   Up 40 minutes                   9090/tcp
attackbot-rabbitmq-1              rabbitmq:3-management           "docker-entrypoint.sâ€¦"   rabbitmq              41 minutes ago   Up 40 minutes (healthy)         0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
attackbot-redis-1                 redis:7-alpine                  "docker-entrypoint.sâ€¦"   redis                 41 minutes ago   Up 40 minutes (healthy)         6379/tcp
attackbot-reporter-1              attackbot-reporter              "uvicorn backend.serâ€¦"   reporter              4 minutes ago    Up 4 minutes (healthy)          8003/tcp
attackbot-reporter-worker-1       attackbot-reporter-worker       "celery -A backend.sâ€¦"   reporter-worker       4 minutes ago    Up 4 minutes                    8003/tcp
attackbot-scenario-runner-1       attackbot-scenario-runner       "celery -A backend.sâ€¦"   scenario-runner       4 minutes ago    Up 3 minutes                    
attackbot-scraper-1               attackbot-scraper               "uvicorn backend.serâ€¦"   scraper               41 minutes ago   Up 40 minutes (healthy)         0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
attackbot-tempo-1                 grafana/tempo:latest            "/tempo"                 tempo                 41 minutes ago   Restarting (1) 52 seconds ago   
attackbot-vault-1                 hashicorp/vault:1.15            "docker-entrypoint.sâ€¦"   vault                 41 minutes ago   Up 40 minutes (healthy)         8200/tcp


STDERR:
<empty>
```

## Observed Gaps in Current Implementation
- Reporter worker currently validates `report.jobs` envelopes only.
- Specialist workers are queue listeners; deeper stages land in later milestones.
- This report reflects what ran in this test session, not aspirational docs.
