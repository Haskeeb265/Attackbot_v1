# AttackBot End-to-End Findings Report

- Generated at: `2026-03-25T03:02:35.765175+00:00`
- Report file: `E2E_SYSTEM_FINDINGS.md`
- Project root: `C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1`
- Test outcome: `completed`

## Requested Mode
- Full end-to-end execution attempted against current M3 stack.
- All feature flags were set to `true` in scan start payload.
- Live-mode policy: no seeded/dummy fallback for primary scan.
- Program selection override active via `E2E_PINNED_PROGRAM_HANDLE` / `E2E_PINNED_PROGRAM_ID`.

## Execution Steps
1. 2026-03-25T02:58:32.558709+00:00 | Starting end-to-end system trace test
1. 2026-03-25T02:58:32.559121+00:00 | .env present (loaded 0 missing keys into process env)
1. 2026-03-25T02:58:35.354155+00:00 | Bringing up stack with docker compose up -d
1. 2026-03-25T02:59:44.199562+00:00 | Health probe scraper: status_code=200
1. 2026-03-25T02:59:44.712397+00:00 | Health probe core-engine: status_code=200
1. 2026-03-25T03:00:18.135169+00:00 | Health probe reporter: status_code=None
1. 2026-03-25T03:00:52.010067+00:00 | Health probe attack-graph-engine: status_code=None
1. 2026-03-25T03:00:52.681038+00:00 | Health probe api-gateway: status_code=200
1. 2026-03-25T03:00:53.635008+00:00 | Connected to database backend=docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
1. 2026-03-25T03:00:53.635030+00:00 | Pinned program selector configured: E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'
1. 2026-03-25T03:00:53.635033+00:00 | HackerOne credentials detected; triggering live scraper sync
1. 2026-03-25T03:00:54.123442+00:00 | Scraper trigger responded with status_code=200
1. 2026-03-25T03:00:54.853123+00:00 | Selected existing real program with scope: 2715b22b-3506-4fb1-bece-95cad2eec341 (weblate) via policy=pinned_program_handle
1. 2026-03-25T03:00:56.105749+00:00 | Queue purge pre-check scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-25T03:00:57.430323+00:00 | Queue purge attempt #1 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-25T03:00:57.864954+00:00 | Queue purge settle window scan.jobs: settled_unacked=True ready=0 unacked=0
1. 2026-03-25T03:00:59.322393+00:00 | Queue purge attempt #2 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-25T03:00:59.322421+00:00 | Waiting for queue baseline before triggering scan: queue=scan.jobs ready=0 unacked=0 timeout=60s
1. 2026-03-25T03:00:59.826014+00:00 | Queue baseline poll scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-25T03:00:59.826062+00:00 | Queue baseline reached: scan.jobs ready=0 unacked=0
1. 2026-03-25T03:00:59.826070+00:00 | Triggering core scan with all feature flags enabled
1. 2026-03-25T03:01:12.647380+00:00 | Scan start response included scan_id=bf26cf78-e601-4768-a0e0-7e040e80d703
1. 2026-03-25T03:01:13.502727+00:00 | Scan status transition observed: running
1. 2026-03-25T03:02:27.210816+00:00 | Scan status transition observed: partial
1. 2026-03-25T03:02:27.210839+00:00 | Terminal scan status reached: partial

## Runtime Context
- DB connection backend: `docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit`
- Live HackerOne mode: `False`
- Program source: `existing_real_pinned`
- Program selection policy: `pinned_program_handle`
- Pinned program handle override: `weblate`
- Pinned program ID override: `None`
- Program ID: `2715b22b-3506-4fb1-bece-95cad2eec341`
- Program handle: `weblate`
- Scan ID: `bf26cf78-e601-4768-a0e0-7e040e80d703`
- Reconciler pause requested (`E2E_PAUSE_RECONCILER`): `True`
- Queue baseline enforcement (`E2E_ENFORCE_QUEUE_BASELINE`): `True`
- Queue pre-purge enabled (`E2E_QUEUE_PURGE_BEFORE_BASELINE`): `True`
- HackerOne username present in process env: `True`
- HackerOne token present in process env: `True`

### Enabled Feature Flags
```json
{
  "ai_hypothesis": true,
  "api_fuzzing": true,
  "asset_discovery": true,
  "browser_session": true,
  "cors": true,
  "crlf": true,
  "enumeration": true,
  "fingerprinting": true,
  "idor_verification": true,
  "nuclei": true,
  "scenario_runner": true,
  "secret_js": true,
  "secret_repo": true,
  "sqli": true,
  "ssrf": true,
  "takeover": true,
  "xss": true
}
```

## HackerOne Scrape Trigger
```json
{
  "payload": {
    "platform": "hackerone",
    "reason": "lock_held",
    "status": "skipped"
  },
  "status_code": 200
}
```

## Program Selection Audit
| program_id | handle | name | platform | is_active | valid_in_scope_count | selected | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8a4e7a2b-9b18-45e7-8a63-80ef486146a2 | dropcontact | Dropcontact | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 7d77b5a8-f1df-4205-ada0-3e8cea8a349d | aig | AIG | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| abf7e35e-612d-448b-a3af-80b0c19e34e4 | rebellion-defense | Rebellion Defense | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 81bf1012-925f-4c16-bfdd-a6a2aafa4a5a | estee-lauder |  Esteé  Lauder | hackerone | True | 471 | False | not selected: run pinned to explicit program selector(s) |
| 56928c11-0574-4bf3-b709-943eab4dbb9d | callsign | Callsign | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 823c713b-ed83-4dbc-a4c4-38f905541603 | polygon-technology | Polygon Technology | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| d6fc363e-2a3a-445c-a284-4454983f1ce2 | finra | FINRA Response | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 2853b185-5764-4b82-91e4-282fa8837a8d | blackrock | BlackRock | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| f08ae733-4a63-497a-b03e-0c399d13a762 | zebra_vdp | Zebra VDP | hackerone | True | 57 | False | not selected: run pinned to explicit program selector(s) |
| fa66cf1c-79ff-4bf3-867b-641011177ee5 | launchdarkly | LaunchDarkly | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 134167ee-27d4-4c68-b4ec-4e7a6a139f38 | figma | Figma | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| e1179298-6950-40f2-bca2-149228f4750e | vendasta | Vendasta | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| 65d9ee4e-f06e-416b-a5ca-85c54e637d0d | cs_money | CS Money | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 770680d8-c12b-4e94-9788-51f2c62bc5a9 | mendix | Mendix | hackerone | True | 23 | False | not selected: run pinned to explicit program selector(s) |
| a63332e3-7ebf-4337-991d-ffab553fa070 | lichess | Lichess | hackerone | True | 48 | False | not selected: run pinned to explicit program selector(s) |
| 1b363b6c-d32f-4775-9103-48b3ac6382a8 | insightly | Insightly | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 14b8424f-dc3f-43d7-8566-e928d9dc5310 | trycourier | Courier | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| b4a3d823-1b53-4fe7-8c72-7bf55f13166e | shutterfly_vdp | Shutterfly VDP | hackerone | True | 35 | False | not selected: run pinned to explicit program selector(s) |
| 383c8166-7bcb-4557-891b-d6a2c6e0a63a | n45ht | N45HT | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 77a8cd6c-0610-4a66-a808-5f786dcf05a0 | h1-ctf | h1-ctf | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| c49fed09-70cb-401c-a330-5cc555cfad95 | cognizant | Cognizant | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| a342a04e-992a-4736-83c9-8eb5ece39c8c | ups | UPS VDP | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 3c9c0e69-57af-479e-82d1-8f921632e62a | alibaba | Alibaba BBP | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 993f5928-68c5-4543-bd9f-7c5e868347a2 | openmage | OpenMage | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| e44c0270-63d1-4ab9-b1e1-31afd9d16d6a | shein | SHEIN | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 95a549e6-dfff-4bb2-8399-3b42dad5bd2f | logsnitch | LogSnitch | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 007dc1e5-214d-45a5-8eb0-3b6a97b3d4a8 | cedars-sinai | Cedars-Sinai | hackerone | True | 39 | False | not selected: run pinned to explicit program selector(s) |
| 9d3a7477-ab66-4fc3-9a09-dae0bf982ab9 | flexport_vdp | Flexport VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| c16627e4-afc5-45ea-a436-d8d90573690b | gener8 | Gener8 | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 22c3e1c6-9c22-4ef3-89f6-a5b1b7ab9700 | cirrusinsight | Cirrus Insight | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 3f2d86ac-b425-4c94-83c5-5e9eafee5479 | stagingdoteverydotorg | Staging.every.org | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 10905f2c-3d41-4e00-a4bb-5d56ab545e8f | navient_solutions | Navient Solutions LLC | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| f723c3bb-3de8-44a7-800e-c9bc3f7137a1 | btfs | BTFS | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 4cf8a2e4-bd8d-4cd3-b356-5d5b6fbe835a | r3 | R3 | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 48a9dcf8-e728-475e-a087-02f01e93bbd0 | faraday_inc | Faraday, Inc. | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 9fb39550-85f4-4945-b706-cd9c22f8c4b6 | td-bank | TD Bank Group | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 9f455947-751d-40e2-bfb0-c47f6de4ad39 | aiven_ltd | Aiven Ltd | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 4e0b0281-3339-4841-96a4-f6f235ff9577 | hostinger | hostinger  | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 889011c4-69fd-4f36-9e08-d0d7131fb633 | standard_notes | Standard Notes | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 3b9041d6-f91d-49f8-879b-ddfb9b2e5750 | simple_poll | Simple Poll | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| a44800ee-f8e6-4de9-9c17-44dc4224c7a9 | skale_network | SKALE Network | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| b5964204-9322-408d-9c46-2aa1dae9d4f1 | rghost | RGhost | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| cc6a2dab-888e-42da-99c5-d813744594b8 | playstation | PlayStation | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 3286aba6-2fec-4442-89a7-5e53f76235f4 | myndr | Myndr | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 99a92da6-91e7-4202-b388-5f70184fb789 | pubg | PUBG | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 133e661c-c1bd-4bed-aab9-db2983d6d5a5 | chorus_jg4l2 | Chorus | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 8368c1d8-739e-425e-a1a0-b7718260fb37 | evernote | Evernote | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 55117e82-013d-4c5a-a987-c8178ff56f9a | earny | Earny | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| a3f7bb37-c510-4b50-a7b5-3e2ee9a6734a | usps | USPS - United States Postal Service | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| ddda22d3-94a4-42f7-b2db-027c58e0bd0d | truecaller | Truecaller  | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| ba67a3a4-f961-49f2-806e-9c6130da458c | picsart | Picsart | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 6d0821ee-3e08-42bc-8f48-097f49577639 | lemlist | lemlist | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| d237cba2-4f4e-4d5e-8ec1-d2e138b2f585 | amazonvrp | Amazon Vulnerability Research Program | hackerone | True | 100 | False | not selected: run pinned to explicit program selector(s) |
| 970c28e9-9414-4bab-a053-ff5cd9a31ee2 | hcl_software | HCL Software Inc. | hackerone | True | 48 | False | not selected: run pinned to explicit program selector(s) |
| b890d5cf-b88d-47a8-bacd-ff7e20227f7a | thomsonreuters-public | Thomson Reuters | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| ff3bc095-fcbc-49c1-ac5b-3f6a2ff767bd | exodus | Exodus | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| 5f10fb8c-75a7-488c-9f4b-6815e710d4b0 | companyhub | CompanyHub | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 26f48c39-db93-4362-8f44-8acb231aa0bb | gmelius | Gmelius | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| e53c4004-4630-437b-80d9-b0202422557e | mobisystems_ltd | MobiSystems Ltd. | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 0307b70e-d477-41c8-8f5a-d35f5e6be6a4 | thnks | Thnks | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 30a150d7-d9e0-457e-a5c1-91362251af3c | oasisprotocol | Oasis Protocol Foundation | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| e958f2d7-15d0-4055-9279-8e82303b2de6 | copper | Copper | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| faf2a510-adbd-49c5-97cf-84223ba6c274 | jnj_mobile | JNJ Mobile | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| dab4f5e9-6282-4714-a074-0b3652b0194a | overloop | Overloop | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 1c80094f-563b-41af-900a-4f4f8d9929b4 | stripo | Stripo Inc | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| a79f49d8-c877-459e-b781-9c5aed58101a | palo_alto_software | Palo Alto Software | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 83ba93df-3deb-4a83-a33e-e2f4798ef6dc | uphabit | UpHabit | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 484da2d1-ba00-42ca-a516-5862c773e51c | investnext | InvestNext | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 47fe876f-0172-4e07-bb59-06bd6af1f689 | mtn_group | MTN Group | hackerone | True | 494 | False | not selected: run pinned to explicit program selector(s) |
| 6e6f6e85-c816-43f9-a94c-4eb3b5cc5c03 | panther_labs | Panther Labs | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 6a9e21ba-4b28-40d4-beb1-5a4f4e36bc47 | coinspot | CoinSpot | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| da801ab2-4c21-4da1-abba-b16cf3495e1e | nuri | Nuri | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 80ee9c32-9632-4ac8-bc99-a135890118bf | people_interactive | People Interactive | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| d968689f-ee9c-4fff-aad2-57ec4f68e392 | top_echelon_software | Top Echelon Software | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| a83d201a-a6e3-43de-9140-b2f585f1dc90 | keybank | KeyBank | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| d24a4553-baad-4028-aaee-07fa71c59e68 | aodocs | AODocs | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| dcea063e-6a68-426d-839c-8825d9ed481d | solidus | Solidus | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 7aba5588-8db5-48ea-9689-c9bc7ae2a647 | lark_technologies | Lark Technologies | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| c77e7a4d-0734-4592-bea5-a42a27c89fd1 | amitree_inc | Amitree Inc | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 77d95793-43f3-4edf-8ca5-5e18b99d01a7 | worklytics | Worklytics | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 8b6ab3bd-5dff-4aef-9498-f2af0919ffc2 | mailtime_technology_inc | Mailtime Technology Inc. | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 4e0110ea-5b13-4499-abe1-e8faabfd9bd0 | replyify | Replyify | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 966f8b89-39bb-4f6e-9220-18165eda230b | raivo | Raivo | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| fe49797d-86fd-444e-882e-3582aae3ad2b | consensys | Consensys | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 76a9fac0-3295-4fd2-8f8a-3754c64b3127 | gocardless_bbp | GoCardless Bug Bounty Program | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 5b3c24eb-f663-4253-bece-4cc4472bafc5 | dynatrace | Dynatrace | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| 6a6476d2-db9c-4845-b7a8-5ef8b623f90b | forescout_technologies | ForeScout Technologies | hackerone | True | 63 | False | not selected: run pinned to explicit program selector(s) |
| c472d536-1c25-4e44-a287-ee6b60a64469 | kubernetes | Kubernetes | hackerone | True | 83 | False | not selected: run pinned to explicit program selector(s) |
| 1a14fb34-3edc-4a8e-b54b-2fabda5e4c87 | midpoint_h1c | Midpoint (European Commission - DIGIT) | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 04aee174-267f-4ce3-951f-d6ded7244368 | impresscms | ImpressCMS | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 6c224332-a9fa-416b-97e6-0590d8055fef | starling_bank | Starling Bank VDP | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 96ce168e-0868-4549-8109-ba6791207dfd | spell | Spell | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 45d16673-adaa-46b7-967b-80c613cff454 | endless_group | Endless Group | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| a3c5e4b4-2f77-43aa-baa4-af6c52732976 | early_warning | Early Warning | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| f3541886-7c29-4535-a2d1-19b01fb061bd | ridewithvia | Via | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 9efbf5c7-d415-4993-806b-cbecc5ed7382 | apache_kafka_h1c | Apache Kafka (European Commission - DIGIT) | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| aefff70c-cdac-481f-968f-96e1f4086dc9 | filezilla_h1c | FileZilla (European Commission - DIGIT) | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 9fd9fee6-f680-4f92-8e08-d64c919c7697 | putty_h1c | PuTTY (European Commission - DIGIT) | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 873a4936-5a2e-4259-9f34-c44d9d93cdf2 | vlc_h1c | VLC (European Commission - DIGIT) | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 7e3897d0-b5b1-497f-be60-51daa04f4fba | filezilla | FileZilla | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| c3791beb-5f84-4ff3-8b7e-b605c418f67b | capital-one | Capital One | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| f88e4350-e954-44b1-b8b3-3cadafcbd308 | ford | Ford | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| 4924e84e-7949-4086-83f9-a1be378822ad | reddit | Reddit | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 00f98ccc-b54a-49fe-b7c8-d9d7f8d8d76c | curl | curl | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 0f98cb87-47a1-45c3-89d3-dc27b633d154 | remitano | Remitano | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 22ab360c-8843-4912-b3c1-21b85917e614 | instacart | Instacart | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 12574476-7fe5-4dd4-8b7a-69ab3bb2f247 | central-security-project | Central Security Project | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 100beb09-2010-4936-90ac-079bd95bbdf7 | fronthq | Front | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| b7501300-37ff-4aea-98e7-c2d3ab08e779 | etoro_bbp | eToro BBP | hackerone | True | 42 | False | not selected: run pinned to explicit program selector(s) |
| 364192e3-8beb-4e36-b735-bda69d12ab5d | insulet_corporation | Insulet Corporation | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| 93d19079-52c1-4810-8aca-ad4d9975b067 | fanduel | FanDuel | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 9d7e0a04-9e12-4b30-9242-d8f0e70e5007 | sweatco_ltd | Sweatco Ltd | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 1cd11123-36eb-4590-bde1-4feb337ce1c3 | expediagroup_bbp | Expedia Group Bug Bounty | hackerone | True | 53 | False | not selected: run pinned to explicit program selector(s) |
| e59b63d2-8813-4f4d-bd7b-f68944118e20 | urbancompany | Urban Company | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 87e4c202-136b-4f7e-bd29-0bb2fd87f323 | creditkarma | Credit Karma | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| b2cfa804-cdfb-468c-a052-5bb570cf5e6a | mercadolibre | MercadoLibre | hackerone | True | 67 | False | not selected: run pinned to explicit program selector(s) |
| 4ea10ca2-2b37-49f2-8557-57558609bb2c | expediagroup | Expedia Group VDP | hackerone | True | 35 | False | not selected: run pinned to explicit program selector(s) |
| 37011ec0-428c-4e68-864b-76a0aa9aa48f | defectdojo | DefectDojo | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 812d9b91-a505-449b-a16f-3a841910eda5 | flickr | Flickr | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 020b581d-523d-4127-9152-b0d075127626 | logitech | Logitech | hackerone | True | 86 | False | not selected: run pinned to explicit program selector(s) |
| f4112240-7707-4c5f-ba4e-250cbf2375b5 | remitly | Remitly | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| b9ffcfa4-38ae-4fc4-8f47-d2d790cf2150 | eslint | ESLint | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 6060ad2d-89ae-4a6b-bcd6-aca0023ad5e9 | chainlink | Chainlink | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 542c84b3-45f1-47da-9d16-d2df465afc59 | nisc | NISC-VDP | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| 844d2936-547e-44fd-92d7-efd82557ad5b | marriott | Marriott Bug Bounty Program | hackerone | True | 80 | False | not selected: run pinned to explicit program selector(s) |
| e648519e-ea02-4b28-b27f-fe0109f03f4b | cfptime | CFP Time | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| bfec31eb-2bab-4da8-bdec-25e63b8334f8 | chaturbate | Chaturbate | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 2706bda2-b193-4221-8eb7-84c24e02ebc0 | hannob | Hanno's projects | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d0110b57-0c64-4e1f-895a-a2b4ac670646 | s-pankki | S-Pankki | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| de21d0c4-3f44-4221-820e-944dece653e3 | arkadiyt-projects | arkadiyt-projects | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| b56553b9-aeb5-4c4a-84f2-adeafedf752a | pixiv | pixiv | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| c638b22f-1628-4ef9-ae59-5b0ca6095294 | liberapay | Liberapay | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 25350a62-076d-4c10-997b-320e56a20985 | crypto | Crypto.com | hackerone | True | 23 | False | not selected: run pinned to explicit program selector(s) |
| 5416cfb5-f515-4942-b462-86bc3793a29a | ratelimited | RATELIMITED | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 1167bea8-d2cd-4871-80ca-1214fd5642d7 | ycombinator | Y Combinator | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 2d226257-e92a-49f9-8c61-eb8c6d4f5822 | passhash | passhash | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| a7a0c645-708d-404a-8590-613ca77a7b83 | pingidentity | Ping Identity | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 9d100afb-a52e-469e-851c-09f2f5ac4f8e | crowdstrike | Crowdstrike | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| fea3b05f-4661-4526-b96a-af85aa292079 | affirm | Affirm | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 2be2da2e-9195-4ba0-9f3d-b40cb3f43fd2 | coalition | Coalition, Inc. | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| acf12102-204a-49dd-9049-43eadf8d0b1e | cosmos | Cosmos | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 5ce15f4b-c524-4294-bd03-13ce89a39e07 | databricks | Databricks | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 3b5d0d6c-e569-48b0-bda4-06b210723f13 | flutteruki | Flutter UK&I | hackerone | True | 42 | False | not selected: run pinned to explicit program selector(s) |
| 037357c4-8fa2-4be1-ab2a-da0fbe6efc97 | jamieweb | JamieWeb | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| fc367bed-7427-484f-ade9-0890a4600de7 | ed | Ed | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 753a8c4b-fb2d-4ab6-8a46-015ea03ce88b | bitmex | BitMEX | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| badbf9e1-50b3-4c59-be6a-367c9349997a | smule | Smule | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 277308ca-9abb-4906-bbaa-0b498d38deb4 | fig | Fig | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 10e76933-dd6b-4114-854e-8b0b395324e6 | elastic | Elastic | hackerone | True | 60 | False | not selected: run pinned to explicit program selector(s) |
| bfa87224-c620-460a-a07c-94e3cf3f33fa | valve | Valve | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| 255a402e-6016-4212-b307-c398bfeb17f5 | epicgames | Epic Games | hackerone | True | 85 | False | not selected: run pinned to explicit program selector(s) |
| ed83250d-2e93-42d8-8f94-596482f33b21 | deconf_com | Deconf | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| ba21f266-0ba2-4f60-a068-760f68d8e508 | nodejs | Node.js | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 22a25565-81f2-4a37-ad8f-fb045a3c73de | netlify | Netlify | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 66413d4b-7261-4f5c-9f64-a371bc21cb88 | kartpay | Kartpay | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 36184858-826c-452c-8aa0-f9dbb1620e65 | streak_com | Streak | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| ce9528a2-2da8-4e62-acf0-c0e5868e9437 | usertesting | UserTesting | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 52d72dcf-cb60-4d5b-84fd-be662db2c966 | superhuman | Superhuman (formerly Grammarly) | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| af01906f-0bf5-4836-91ed-12ed51434d93 | hyperledger | Linux Foundation Decentralized Trust | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| 7fbad3cb-02b1-4000-bef4-d066040f9017 | upserve | Upserve  | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 2578e56e-f426-428c-a50b-573e1adf8c2c | malwarebytes | Malwarebytes | hackerone | True | 36 | False | not selected: run pinned to explicit program selector(s) |
| 70e2da39-c246-407f-a60d-050f6ae3e38a | delight_im | delight.im | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 6509bd60-1659-432e-be5e-66c5e5b5fcc0 | wakatime | WakaTime | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 82d5613c-c6cd-4cc8-9efd-31cae0cafa9f | yoti | Yoti | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 11806c2d-2ff2-4179-953c-e4e08653ef75 | infogram | Infogram | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| ac00be94-53e5-4095-83db-7535cd0915ea | bumble | Bumble | hackerone | True | 50 | False | not selected: run pinned to explicit program selector(s) |
| 66ec6da6-49b9-4e21-8055-a61fba102feb | wink_jq3al | WINK | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 282a5447-56ca-4f85-8303-a8839c2bd342 | omise | Omise | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 847c022b-eedb-4514-8487-577af5896c94 | bitwarden | Bitwarden | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| f8aae6d2-d7c6-4bdf-8159-a6fdfc30c654 | parrot_sec | Parrot Sec | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 4fa088f1-d644-4e0a-b293-d37ccba494f1 | stellar | Stellar.org | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 7b5b72d1-e72d-4dd8-9237-491ee610ef23 | teradici | Teradici | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| edd64fa2-72fe-437f-9372-770e4ee1d5e8 | autodesk | Autodesk | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| f62490cd-5196-40ec-bb0a-f3b2fcf22c79 | rocket_chat | Rocket.Chat | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 9ff4160d-eedc-4b20-a7d6-e010d1004243 | roblox | Roblox | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 2715b22b-3506-4fb1-bece-95cad2eec341 | weblate | Weblate | hackerone | True | 6 | True | selected: matched E2E_PINNED_PROGRAM_HANDLE=weblate |
| 93b10688-7d1b-4320-b8ee-bfe72117d9e9 | homebrew | Homebrew | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| df789f05-ba39-4505-bf61-7828ab63ca8b | oportun_vdp | Oportun | hackerone | True | 44 | False | not selected: run pinned to explicit program selector(s) |
| 47b1d47c-e255-4e84-8aee-8a11f8b6b04d | rbkmoney | RBKmoney | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 83dba83c-7800-46fb-8803-93e836527861 | nordsecurity | Nord Security | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| a794297f-bcb8-4d68-acb7-d839438ba9a9 | discourse | Discourse | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| d2bab8bd-e481-4066-9910-3de1e9504a91 | nutanix | Nutanix | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 7f006c6f-f484-4671-b7e0-d69326d93335 | mapsmarker_com_e_u | MapsMarker.com e.U. | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 0a82b80b-ab8e-4a41-9a60-6b7a9be82da7 | nintendo | Nintendo | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 3b6a1bf0-1686-4e6c-88eb-804503540272 | sony | Sony | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| a47ce257-6f5e-48a1-b772-35a9df9031e3 | alvosec | Alvosec | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 12242d30-5139-476d-9d14-a217708f1445 | enjin | Enjin | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| cf594ce9-247b-4f44-8156-e5929d4ed499 | lyst | Lyst | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| cb445c02-3d4b-478f-8e68-a609a4f14581 | disclosure-assistance | Disclosure Assistance | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 4fc994f0-06c5-4f05-967b-3c2931acb801 | xiaomi | Xiaomi | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| bc7e9678-0c92-4334-86ec-07e8806eabdf | deptofdefense | U.S. Dept Of Defense | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 900fb79e-04ae-45b7-ab33-cd838129d61b | semrush | Semrush | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 57fe104b-a269-4ad2-938b-7c354af561f0 | brave | Brave Software | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 57f39ae7-c3f7-4a87-855a-1cbd6b31804d | shopify-scripts | shopify-scripts | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 96816aaa-5349-4aba-963d-71618729f38b | cornershop | Cornershop | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| b35f32f3-9609-4a42-a649-01615da02085 | plaid | Plaid | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 280b9aad-1cea-4351-8e02-a0d79a4998c9 | portswigger | PortSwigger Web Security | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| a40a5a61-8166-4d62-b876-5c07694cd275 | toyota | Toyota | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 90bde9b8-c989-4632-bf5a-d293b6b796bd | localizejs | Localize | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 5ea0ad2c-cde6-43e6-abfb-a9cc1b26a159 | hiro | Hiro | hackerone | True | 0 | False | no non-empty in_scope scope entries |

### Program Scope Used
| scope_type | asset_type | value | notes |
| --- | --- | --- | --- |
| in_scope | domain | hosted.weblate.org | Please use the [Sandbox translation project](https://hosted.weblate.org/projects/sandbox/) for testing. |
| in_scope | url | https://github.com/WeblateOrg/docker |  |
| in_scope | url | https://github.com/WeblateOrg/translation-finder |  |
| in_scope | url | https://github.com/WeblateOrg/weblate |  |
| in_scope | url | https://github.com/WeblateOrg/website |  |
| in_scope | url | https://github.com/WeblateOrg/wlc |  |
| out_of_scope | domain | github.com | The GitHub wiki is intentionally open to public. |
| out_of_scope | domain | hg.weblate.org | This site has intentional setup this way to allow mercurial client to clone the repository. |

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
{
  "payload": {
    "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341",
    "scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703",
    "status": "queued"
  },
  "status_code": 200
}
```

### Final Scan Row
```json
{
  "completed_at": "2026-03-25T03:02:25.056397+00:00",
  "created_at": "2026-03-23T07:59:25.019598+00:00",
  "error_detail": null,
  "finding_count": 0,
  "partial_detail": "{\"errors\": {\"nuclei_scan\": \"nuclei exited with code 2. stderr: \"}, \"failed_stages\": [\"nuclei_scan\"]}",
  "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341",
  "retry_count": 0,
  "scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703",
  "severity_breakdown": "{\"low\": 0, \"high\": 0, \"info\": 0, \"medium\": 0, \"critical\": 0}",
  "started_at": "2026-03-25T03:01:00.319289+00:00",
  "status": "partial"
}
```

### Scan Wait Result
```json
{
  "status_at_snapshot": "partial",
  "terminal_reached": true,
  "timeout_seconds": 3600
}
```

### Pipeline Stage Timeline
| stage_number | stage_name | status | started_at | completed_at | error_detail |
| --- | --- | --- | --- | --- | --- |
| 1.0 | asset_discovery | completed | 2026-03-23T07:59:25.074396+00:00 | 2026-03-23T08:09:27.202233+00:00 |  |
| 1.0 | asset_discovery | completed | 2026-03-25T03:01:12.834447+00:00 | 2026-03-25T03:02:02.008299+00:00 |  |
| 2.0 | fingerprinting | completed | 2026-03-23T08:09:27.204206+00:00 | 2026-03-23T08:09:28.571864+00:00 |  |
| 2.0 | fingerprinting | completed | 2026-03-25T03:02:02.013431+00:00 | 2026-03-25T03:02:03.713028+00:00 |  |
| 3.0 | enumeration | completed | 2026-03-25T03:02:03.715117+00:00 | 2026-03-25T03:02:23.835918+00:00 |  |
| 4.0 | nuclei_scan | failed | 2026-03-25T03:02:03.715130+00:00 | 2026-03-25T03:02:25.044322+00:00 | nuclei exited with code 2. stderr:  |
| 5.0 | web_vuln_tests | completed | 2026-03-25T03:02:23.838224+00:00 | 2026-03-25T03:02:25.049615+00:00 |  |
| 6.0 | js_secrets | completed | 2026-03-25T03:02:23.838331+00:00 | 2026-03-25T03:02:25.052927+00:00 |  |
| 10.1 | report_handoff | completed | 2026-03-25T03:02:25.059073+00:00 | 2026-03-25T03:02:25.069163+00:00 |  |

### Artifact Counts
```json
{
  "assets_count": 4,
  "endpoints_count": 5,
  "evidence_count": 0,
  "findings_count": 0,
  "js_assets_count": 0
}
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
{
  "payload": {
    "queues": [
      {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "queue": "scan.jobs"
      },
      {
        "consumers": 0,
        "exists": true,
        "messages": 0,
        "queue": "scan.jobs.dlq"
      },
      {
        "consumers": 0,
        "exists": true,
        "messages": 1,
        "queue": "report.jobs"
      },
      {
        "consumers": 0,
        "exists": true,
        "messages": 0,
        "queue": "report.jobs.dlq"
      }
    ]
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/queue/dlq/inspect"
}
```

### Queue Baseline Purge
```json
{
  "attempts": [
    {
      "ok": true,
      "purge_error": null,
      "purge_status_code": 204,
      "queue": "scan.jobs",
      "ready_after": 0,
      "ready_before": 0,
      "state_after": {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "state_before": {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "unacked_after": 0,
      "unacked_before": 0
    },
    {
      "ok": true,
      "purge_error": null,
      "purge_status_code": 204,
      "queue": "scan.jobs",
      "ready_after": 0,
      "ready_before": 0,
      "state_after": {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "state_before": {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "unacked_after": 0,
      "unacked_before": 0
    }
  ],
  "enabled": true,
  "final_state": {
    "consumers": 1,
    "exists": true,
    "messages": 0,
    "messages_ready": 0,
    "messages_unacknowledged": 0,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "initial_state": {
    "consumers": 1,
    "exists": true,
    "messages": 0,
    "messages_ready": 0,
    "messages_unacknowledged": 0,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "ok": true,
  "queue": "scan.jobs",
  "settle_poll_seconds": 5.0,
  "settle_state": {
    "consumers": 1,
    "exists": true,
    "messages": 0,
    "messages_ready": 0,
    "messages_unacknowledged": 0,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "settle_timeout_seconds": 60,
  "settled_unacked": true
}
```

### Queue Baseline Wait
```json
{
  "reached": true,
  "seconds_waited": 0.0,
  "state": {
    "consumers": 1,
    "exists": true,
    "messages": 0,
    "messages_ready": 0,
    "messages_unacknowledged": 0,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "timeout_seconds": 60
}
```

### RabbitMQ Queue States
| queue | exists | messages | ready | unacked | consumers | http_status | error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| scan.jobs | True | 0 | 0 | 0 | 1 |  |  |
| scan.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| browser.jobs | True | 0 | 0 | 0 | 0 |  |  |
| browser.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| api.fuzz.jobs | True | 0 | 0 | 0 | 0 |  |  |
| api.fuzz.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| js.analysis.jobs | True | 0 | 0 | 0 | 0 |  |  |
| js.analysis.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| scenario.jobs | True | 0 | 0 | 0 | 0 |  |  |
| scenario.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| verify.jobs | True | 0 | 0 | 0 | 0 |  |  |
| verify.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| ai.analysis.jobs | True | 0 | 0 | 0 | 0 |  |  |
| ai.analysis.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| report.jobs | True | 1 | 1 | 0 | 0 |  |  |
| report.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| reports.completed | True | 0 | 0 | 0 | 0 |  |  |

## API Snapshots
### /scans/{scan_id}
```json
{
  "payload": {
    "completed_at": "2026-03-25T03:02:25.056397+00:00",
    "error_detail": null,
    "finding_count": 0,
    "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341",
    "scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703",
    "severity_breakdown": {
      "critical": 0,
      "high": 0,
      "info": 0,
      "low": 0,
      "medium": 0
    },
    "started_at": "2026-03-25T03:01:00.319289+00:00",
    "status": "partial"
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/scans/bf26cf78-e601-4768-a0e0-7e040e80d703"
}
```

### /scans/{scan_id}/findings
```json
{
  "payload": {
    "count": 0,
    "findings": []
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/scans/bf26cf78-e601-4768-a0e0-7e040e80d703/findings"
}
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
 Container attackbot-prometheus-1 Running 
 Container attackbot-loki-1 Running 
 Container attackbot-grafana-1 Running 
 Container attackbot-vault-1 Running 
 Container attackbot-redis-1 Running 
 Container attackbot-minio-1 Running 
 Container attackbot-rabbitmq-1 Running 
 Container attackbot-neo4j-1 Running 
 Container attackbot-postgres-1 Running 
 Container attackbot-reporter-1 Running 
 Container attackbot-attack-graph-engine-1 Running 
 Container attackbot-core-engine-1 Recreate 
 Container attackbot-reporter-worker-1 Running 
 Container attackbot-scraper-1 Running 
 Container attackbot-core-engine-1 Recreated 
 Container attackbot-api-gateway-1 Running 
 Container attackbot-exploit-verifier-1 Running 
 Container attackbot-browser-worker-1 Running 
 Container attackbot-core-worker-1 Recreate 
 Container attackbot-core-worker-1 Recreated 
 Container attackbot-tempo-1 Starting 
 Container attackbot-minio-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-vault-1 Waiting 
 Container attackbot-tempo-1 Started 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-migrate-1 Starting 
 Container attackbot-vault-1 Healthy 
 Container attackbot-vault-init-1 Starting 
 Container attackbot-minio-1 Healthy 
 Container attackbot-minio-init-1 Starting 
 Container attackbot-migrate-1 Started 
 Container attackbot-neo4j-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Started 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-vault-init-1 Started 
 Container attackbot-neo4j-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-migrate-1 Exited 
 Container attackbot-core-engine-1 Starting 
 Container attackbot-core-engine-1 Started 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-attack-graph-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-scraper-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-reporter-1 Healthy 
 Container attackbot-reporter-worker-1 Starting 
 Container attackbot-reporter-worker-1 Started 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-reporter-1 Healthy 
 Container attackbot-attack-graph-engine-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-scraper-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-api-fuzzer-worker-1 Starting 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-scenario-runner-1 Starting 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-worker-1 Starting 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-ai-analysis-worker-1 Starting 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-exploit-verifier-1 Starting 
 Container attackbot-api-fuzzer-worker-1 Started 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-browser-worker-1 Starting 
 Container attackbot-ai-analysis-worker-1 Started 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-js-analysis-worker-1 Starting 
 Container attackbot-scenario-runner-1 Started 
 Container attackbot-exploit-verifier-1 Started 
 Container attackbot-browser-worker-1 Started 
 Container attackbot-js-analysis-worker-1 Started 
 Container attackbot-core-worker-1 Started 

```

### Command: docker compose ps
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env ps`

```text
STDOUT:
NAME                              IMAGE                           COMMAND                  SERVICE               CREATED              STATUS                          PORTS
attackbot-ai-analysis-worker-1    attackbot-ai-analysis-worker    "celery -A backend.sâ€¦"   ai-analysis-worker    14 minutes ago       Restarting (1) 10 seconds ago   
attackbot-api-fuzzer-worker-1     attackbot-api-fuzzer-worker     "celery -A backend.sâ€¦"   api-fuzzer-worker     14 minutes ago       Restarting (1) 7 seconds ago    
attackbot-api-gateway-1           attackbot-api-gateway           "uvicorn backend.serâ€¦"   api-gateway           14 minutes ago       Up 13 minutes (unhealthy)       0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
attackbot-attack-graph-engine-1   attackbot-attack-graph-engine   "uvicorn backend.serâ€¦"   attack-graph-engine   14 minutes ago       Up 14 minutes (healthy)         8006/tcp
attackbot-browser-worker-1        attackbot-browser-worker        "celery -A backend.sâ€¦"   browser-worker        14 minutes ago       Restarting (1) 3 seconds ago    
attackbot-core-engine-1           attackbot-core-engine           "uvicorn backend.serâ€¦"   core-engine           About a minute ago   Up 57 seconds (healthy)         0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
attackbot-core-worker-1           attackbot-core-worker           "celery -A backend.sâ€¦"   core-worker           About a minute ago   Up Less than a second           8002/tcp
attackbot-exploit-verifier-1      attackbot-exploit-verifier      "celery -A backend.sâ€¦"   exploit-verifier      14 minutes ago       Restarting (1) 1 second ago     
attackbot-grafana-1               grafana/grafana:latest          "/run.sh"                grafana               14 minutes ago       Up 14 minutes                   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
attackbot-js-analysis-worker-1    attackbot-js-analysis-worker    "celery -A backend.sâ€¦"   js-analysis-worker    14 minutes ago       Restarting (1) 8 seconds ago    
attackbot-loki-1                  grafana/loki:latest             "/usr/bin/loki -confâ€¦"   loki                  14 minutes ago       Up 14 minutes                   3100/tcp
attackbot-minio-1                 minio/minio                     "/usr/bin/docker-entâ€¦"   minio                 14 minutes ago       Up 14 minutes (healthy)         9000/tcp
attackbot-neo4j-1                 neo4j:5-community               "tini -g -- /startupâ€¦"   neo4j                 14 minutes ago       Up 14 minutes (healthy)         7473-7474/tcp, 7687/tcp
attackbot-postgres-1              postgres:16                     "docker-entrypoint.sâ€¦"   postgres              14 minutes ago       Up 14 minutes (healthy)         0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
attackbot-prometheus-1            prom/prometheus:latest          "/bin/prometheus --câ€¦"   prometheus            14 minutes ago       Up 14 minutes                   9090/tcp
attackbot-rabbitmq-1              rabbitmq:3-management           "docker-entrypoint.sâ€¦"   rabbitmq              14 minutes ago       Up 14 minutes (healthy)         0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
attackbot-redis-1                 redis:7-alpine                  "docker-entrypoint.sâ€¦"   redis                 14 minutes ago       Up 14 minutes (healthy)         6379/tcp
attackbot-reporter-1              attackbot-reporter              "uvicorn backend.serâ€¦"   reporter              14 minutes ago       Up 14 minutes (healthy)         8003/tcp
attackbot-reporter-worker-1       attackbot-reporter-worker       "celery -A backend.sâ€¦"   reporter-worker       14 minutes ago       Restarting (1) 3 seconds ago    
attackbot-scenario-runner-1       attackbot-scenario-runner       "celery -A backend.sâ€¦"   scenario-runner       14 minutes ago       Restarting (1) 9 seconds ago    
attackbot-scraper-1               attackbot-scraper               "uvicorn backend.serâ€¦"   scraper               14 minutes ago       Up 14 minutes (healthy)         0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
attackbot-tempo-1                 grafana/tempo:latest            "/tempo"                 tempo                 14 minutes ago       Restarting (1) 44 seconds ago   
attackbot-vault-1                 hashicorp/vault:1.15            "docker-entrypoint.sâ€¦"   vault                 14 minutes ago       Up 14 minutes (healthy)         8200/tcp


STDERR:
<empty>
```

### Command: docker compose logs (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env logs --no-color --since 2026-03-25T03:00:59Z --tail 300 scraper core-engine core-worker reporter reporter-worker`

```text
STDOUT:
reporter-1  | INFO:     172.18.0.8:56166 - "GET /metrics HTTP/1.1" 200 OK
reporter-1  | INFO:     127.0.0.1:55286 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1  | INFO:     127.0.0.1:34628 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1  | INFO:     172.18.0.8:46488 - "GET /metrics HTTP/1.1" 200 OK
reporter-1  | INFO:     127.0.0.1:46594 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1  | INFO:     172.18.0.8:55400 - "GET /metrics HTTP/1.1" 200 OK
reporter-1  | INFO:     127.0.0.1:42598 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1  | INFO:     127.0.0.1:39522 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1  | INFO:     172.18.0.8:41990 - "GET /metrics HTTP/1.1" 200 OK
reporter-1  | INFO:     127.0.0.1:46458 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1  | INFO:     172.18.0.8:35200 - "GET /metrics HTTP/1.1" 200 OK
reporter-1  | INFO:     127.0.0.1:44464 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1  | INFO:     172.18.0.8:45168 - "GET /metrics HTTP/1.1" 200 OK
reporter-1  | INFO:     127.0.0.1:43810 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1  | INFO:     127.0.0.1:36744 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1  | INFO:     172.18.0.8:39652 - "GET /metrics HTTP/1.1" 200 OK
core-worker-1  | [2026-03-25 03:01:12,646: INFO/MainProcess] Task core_engine.scan_task[ff4752a5-0bf9-41e1-9936-457963551d41] received
core-worker-1  | [2026-03-25 03:01:12,649: WARNING/ForkPoolWorker-2] {"program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "event_type": "program.scraped", "event": "Scan task received", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:12.649484Z"}
core-worker-1  | [2026-03-25 03:01:12,751: WARNING/ForkPoolWorker-2] {"pool_size": 10, "max_overflow": 20, "event": "db_initialized", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:12.750953Z"}
core-worker-1  | [2026-03-25 03:01:12,751: WARNING/ForkPoolWorker-2] {"endpoint": "minio:9000", "secure": false, "event": "minio_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:12.751784Z"}
core-worker-1  | [2026-03-25 03:01:12,804: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "event": "Resuming existing scan", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:12.804057Z"}
core-worker-1  | [2026-03-25 03:01:12,825: INFO/ForkPoolWorker-2] HTTP Request: GET http://scraper:8001/api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope "HTTP/1.1 200 OK"
core-worker-1  | [2026-03-25 03:01:12,834: WARNING/ForkPoolWorker-2] {"url": "amqp://attackbot:attackbot@rabbitmq:5672/", "event": "queue_publisher_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:12.833954Z"}
core-worker-1  | [2026-03-25 03:01:12,834: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "event": "Stage 0: Scope filter", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:12.834151Z"}
core-worker-1  | [2026-03-25 03:01:12,834: WARNING/ForkPoolWorker-2] {"in_scope_count": 6, "out_of_scope_count": 2, "event": "ScopeFilter built", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:12.834380Z"}
core-worker-1  | [2026-03-25 03:01:12,834: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "skipped_counts": {"url_host_not_domain_led": 5, "explicit_target_out_of_scope": 5}, "event": "asset_discovery_seed_scope_skipped", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:12.834963Z"}
core-worker-1  | [2026-03-25 03:01:12,835: WARNING/ForkPoolWorker-2] {"args": "subfinder", "timeout": 180, "event": "Running subfinder[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:12.835602Z"}
core-worker-1  | [2026-03-25 03:01:38,004: INFO/MainProcess] sync with celery@36a7b7aa45a0
core-worker-1  | [2026-03-25 03:01:38,505: INFO/MainProcess] sync with celery@9f8d7e207cee
core-worker-1  | [2026-03-25 03:01:39,429: INFO/MainProcess] sync with celery@5e7106ce1239
core-worker-1  | [2026-03-25 03:01:40,270: INFO/MainProcess] sync with celery@c46173883b3d
core-worker-1  | [2026-03-25 03:01:44,678: INFO/MainProcess] sync with celery@d10c20a853ae
core-worker-1  | [2026-03-25 03:01:45,943: INFO/MainProcess] sync with celery@9375291ff791
core-worker-1  | [2026-03-25 03:01:57,575: WARNING/ForkPoolWorker-2] {"domain": "hosted.weblate.org", "event": "alterx_skipped_no_subfinder_results", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:57.575476Z"}
core-worker-1  | [2026-03-25 03:01:57,576: WARNING/ForkPoolWorker-2] {"args": "dnsx", "timeout": 270, "event": "Running dnsx[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:57.575978Z"}
core-worker-1  | [2026-03-25 03:01:58,426: WARNING/ForkPoolWorker-2] {"args": "httpx", "timeout": 180, "event": "Running httpx[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:01:58.426285Z"}
core-worker-1  | [2026-03-25 03:02:00,057: WARNING/ForkPoolWorker-2] {"args": "httpx", "timeout": 180, "event": "Running httpx[explicit_scope]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:00.057605Z"}
core-worker-1  | [2026-03-25 03:02:01,993: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "seed_domains": 1, "explicit_targets": 1, "assets_found": 1, "errors": 0, "event": "Stage 1 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:01.993848Z"}
core-worker-1  | [2026-03-25 03:02:02,013: WARNING/ForkPoolWorker-2] {"args": "httpx", "timeout": 180, "event": "Running httpx_fingerprint", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:02.013842Z"}
core-worker-1  | [2026-03-25 03:02:03,707: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "assets_enriched": 1, "event": "Stage 2 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:03.706978Z"}
core-worker-1  | [2026-03-25 03:02:03,715: WARNING/ForkPoolWorker-2] {"args": "nuclei", "timeout": 1080, "event": "Running nuclei", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:03.715708Z"}
core-worker-1  | [2026-03-25 03:02:03,716: WARNING/ForkPoolWorker-2] {"args": "ffuf", "timeout": 540, "event": "Running ffuf[https://hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:03.716776Z"}
core-worker-1  | [2026-03-25 03:02:03,718: WARNING/ForkPoolWorker-2] {"domain": "hosted.weblate.org", "event": "waybackurls skipped via E2E flag", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:03.718140Z"}
core-worker-1  | [2026-03-25 03:02:03,826: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "return_code": 2, "reason_bucket": "nuclei_startup_initialization_failure", "target_count": 1, "sample_targets": ["https://hosted.weblate.org"], "error": "nuclei exited with code 2. stderr: ", "event": "nuclei_startup_failure_detected", "service": "core-worker", "level": "error", "timestamp": "2026-03-25T03:02:03.825993Z"}
core-worker-1  | [2026-03-25 03:02:23,815: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "endpoints": 5, "js_assets": 0, "event": "Stage 3 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:23.815502Z"}
core-worker-1  | [2026-03-25 03:02:23,839: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "js_files_scanned": 0, "secrets_found": 0, "event": "Stage 6 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:23.839706Z"}
core-worker-1  | [2026-03-25 03:02:24,216: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/favicon.ico "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,226: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/user "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,247: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/robots.txt "HTTP/1.1 200 OK"
core-worker-1  | [2026-03-25 03:02:24,263: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/admin "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,264: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/search "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,340: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/favicon.ico "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,406: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/admin "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,435: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/robots.txt "HTTP/1.1 200 OK"
core-worker-1  | [2026-03-25 03:02:24,464: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/favicon.ico "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,590: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/robots.txt "HTTP/1.1 200 OK"
core-worker-1  | [2026-03-25 03:02:24,608: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/user "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,610: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/favicon.ico%0d%0aSet-Cookie:crlf=injected "HTTP/1.1 404 Not Found"
core-worker-1  | [2026-03-25 03:02:24,631: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/search "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,637: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/admin "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,772: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/search "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,776: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/user "HTTP/1.1 301 Moved Permanently"
core-worker-1  | [2026-03-25 03:02:24,779: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/robots.txt%0d%0aSet-Cookie:crlf=injected "HTTP/1.1 404 Not Found"
core-worker-1  | [2026-03-25 03:02:24,859: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/admin%0d%0aSet-Cookie:crlf=injected "HTTP/1.1 404 Not Found"
core-worker-1  | [2026-03-25 03:02:24,904: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/search%0d%0aSet-Cookie:crlf=injected "HTTP/1.1 404 Not Found"
core-worker-1  | [2026-03-25 03:02:25,041: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/user%0d%0aSet-Cookie:crlf=injected "HTTP/1.1 404 Not Found"
core-worker-1  | [2026-03-25 03:02:25,042: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "findings": 0, "event": "Stage 5 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:25.042662Z"}
core-worker-1  | [2026-03-25 03:02:25,067: WARNING/ForkPoolWorker-2] {"queue": "report.jobs", "event_type": "scan.completed", "event_id": "15c45b00-2abd-4734-9854-9cdd376b91d7", "event": "message_published", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:25.067169Z"}
core-worker-1  | [2026-03-25 03:02:25,073: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "event": "Published scan.completed to report.jobs", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:25.073052Z"}
core-worker-1  | [2026-03-25 03:02:25,073: WARNING/ForkPoolWorker-2] {"scan_id": "bf26cf78-e601-4768-a0e0-7e040e80d703", "findings_saved": 0, "status": "partial", "breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}, "event": "Stage 10 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:25.073279Z"}
core-worker-1  | [2026-03-25 03:02:25,074: WARNING/ForkPoolWorker-2] {"event": "queue_publisher_closed", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:02:25.074767Z"}
core-worker-1  | [2026-03-25 03:02:25,085: INFO/ForkPoolWorker-2] Task core_engine.scan_task[ff4752a5-0bf9-41e1-9936-457963551d41] succeeded in 72.443067552s: None
scraper-1      | INFO:     172.18.0.14:45926 - "GET /api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341 HTTP/1.1" 200 OK
scraper-1      | INFO:     172.18.0.14:45926 - "GET /api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:59466 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.18.0.8:60678 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.18.0.14:33208 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.18.0.15:47874 - "GET /api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope HTTP/1.1" 200 OK
scraper-1      | {"handle": "john-deere", "program_id": "232a2594-a4ac-4dcd-9905-17fd371a828d", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:01:13.450036Z"}
scraper-1      | {"handle": "8x8-bounty", "program_id": "d122ea9c-aa96-4df6-97da-fbb8a2435a99", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:01:15.883630Z"}
scraper-1          | {"handle": "hudapp", "program_id": "b6bf2821-79af-4480-b051-81ecf81e5411", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:01:17.553088Z"}
scraper-1          | INFO:     127.0.0.1:55260 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.14:33746 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.8:40896 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     127.0.0.1:33176 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.14:59938 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.8:41726 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     127.0.0.1:50106 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.14:33156 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:55030 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.14:48486 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.8:47252 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     127.0.0.1:46800 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.14:49174 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.8:58832 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     127.0.0.1:41438 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.14:56012 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:35464 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.14:60580 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.8:40230 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     127.0.0.1:38024 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.18.0.14:36982 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-worker-1  | /usr/local/lib/python3.12/site-packages/celery/platforms.py:829: SecurityWarning: You're running the worker with superuser privileges: this is
reporter-worker-1  | absolutely not recommended!
reporter-worker-1  | 
reporter-worker-1  | Please specify a different user using the --uid option.
reporter-worker-1  | 
reporter-worker-1  | User information: uid=0 euid=0 gid=0 egid=0
reporter-worker-1  | 
reporter-worker-1  |   warnings.warn(SecurityWarning(ROOT_DISCOURAGED.format(
reporter-worker-1  |  
reporter-worker-1  |  -------------- celery@8043ccb65221 v5.4.0 (opalescent)
reporter-worker-1  | --- ***** ----- 
reporter-worker-1  | -- ******* ---- Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.41 2026-03-25 03:01:43
reporter-worker-1  | - *** --- * --- 
reporter-worker-1  | - ** ---------- [config]
reporter-worker-1  | - ** ---------- .> app:         reporter-worker:0x75f672e91490
reporter-worker-1  | - ** ---------- .> transport:   amqp://attackbot:**@rabbitmq:5672//
reporter-worker-1  | - ** ---------- .> results:     redis://redis:6379/0
reporter-worker-1  | - *** --- * --- .> concurrency: 1 (prefork)
reporter-worker-1  | -- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
reporter-worker-1  | --- ***** ----- 
reporter-worker-1  |  -------------- [queues]
reporter-worker-1  |                 .> reporter.worker.tasks exchange=reporter.worker.tasks(direct) key=reporter.worker.tasks
reporter-worker-1  |                 
reporter-worker-1  | 
reporter-worker-1  | [tasks]
reporter-worker-1  |   . reporter_worker_task
reporter-worker-1  | 
reporter-worker-1  | [2026-03-25 03:01:43,525: INFO/MainProcess] Connected to amqp://attackbot:**@rabbitmq:5672//
reporter-worker-1  | [2026-03-25 03:01:43,528: CRITICAL/MainProcess] Unrecoverable error: PreconditionFailed(406, "PRECONDITION_FAILED - inequivalent arg 'x-dead-letter-exchange' for queue 'report.jobs' in vhost '/': received none but current is the value '' of type 'longstr'", (50, 10), 'Queue.declare')
reporter-worker-1  | Traceback (most recent call last):
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/worker/worker.py", line 202, in start
reporter-worker-1  |     self.blueprint.start(self)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/bootsteps.py", line 116, in start
reporter-worker-1  |     step.start(parent)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/bootsteps.py", line 365, in start
reporter-worker-1  |     return self.obj.start()
reporter-worker-1  |            ^^^^^^^^^^^^^^^^
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/worker/consumer/consumer.py", line 340, in start
reporter-worker-1  |     blueprint.start(self)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/bootsteps.py", line 116, in start
reporter-worker-1  |     step.start(parent)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/bootsteps.py", line 397, in start
reporter-worker-1  |     self.consumers = self.get_consumers(channel)
reporter-worker-1  |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
reporter-worker-1  |   File "/app/backend/services/reporter/worker.py", line 162, in get_consumers
reporter-worker-1  |     Consumer(
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/messaging.py", line 414, in __init__
reporter-worker-1  |     self.revive(self.channel)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/messaging.py", line 436, in revive
reporter-worker-1  |     self.declare()
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/messaging.py", line 450, in declare
reporter-worker-1  |     queue.declare()
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/entity.py", line 617, in declare
reporter-worker-1  |     self._create_queue(nowait=nowait, channel=channel)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/entity.py", line 626, in _create_queue
reporter-worker-1  |     self.queue_declare(nowait=nowait, passive=False, channel=channel)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/entity.py", line 655, in queue_declare
reporter-worker-1  |     ret = channel.queue_declare(
reporter-worker-1  |           ^^^^^^^^^^^^^^^^^^^^^^
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/amqp/channel.py"
... [truncated]

STDERR:
<empty>
```

### Command: docker compose logs reporter-worker (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env logs --no-color --since 2026-03-25T03:00:59Z --tail 300 reporter-worker`

```text
STDOUT:
reporter-worker-1  | /usr/local/lib/python3.12/site-packages/celery/platforms.py:829: SecurityWarning: You're running the worker with superuser privileges: this is
reporter-worker-1  | absolutely not recommended!
reporter-worker-1  | 
reporter-worker-1  | Please specify a different user using the --uid option.
reporter-worker-1  | 
reporter-worker-1  | User information: uid=0 euid=0 gid=0 egid=0
reporter-worker-1  | 
reporter-worker-1  |   warnings.warn(SecurityWarning(ROOT_DISCOURAGED.format(
reporter-worker-1  |  
reporter-worker-1  |  -------------- celery@8043ccb65221 v5.4.0 (opalescent)
reporter-worker-1  | --- ***** ----- 
reporter-worker-1  | -- ******* ---- Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.41 2026-03-25 03:01:43
reporter-worker-1  | - *** --- * --- 
reporter-worker-1  | - ** ---------- [config]
reporter-worker-1  | - ** ---------- .> app:         reporter-worker:0x75f672e91490
reporter-worker-1  | - ** ---------- .> transport:   amqp://attackbot:**@rabbitmq:5672//
reporter-worker-1  | - ** ---------- .> results:     redis://redis:6379/0
reporter-worker-1  | - *** --- * --- .> concurrency: 1 (prefork)
reporter-worker-1  | -- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
reporter-worker-1  | --- ***** ----- 
reporter-worker-1  |  -------------- [queues]
reporter-worker-1  |                 .> reporter.worker.tasks exchange=reporter.worker.tasks(direct) key=reporter.worker.tasks
reporter-worker-1  |                 
reporter-worker-1  | 
reporter-worker-1  | [tasks]
reporter-worker-1  |   . reporter_worker_task
reporter-worker-1  | 
reporter-worker-1  | [2026-03-25 03:01:43,525: INFO/MainProcess] Connected to amqp://attackbot:**@rabbitmq:5672//
reporter-worker-1  | [2026-03-25 03:01:43,528: CRITICAL/MainProcess] Unrecoverable error: PreconditionFailed(406, "PRECONDITION_FAILED - inequivalent arg 'x-dead-letter-exchange' for queue 'report.jobs' in vhost '/': received none but current is the value '' of type 'longstr'", (50, 10), 'Queue.declare')
reporter-worker-1  | Traceback (most recent call last):
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/worker/worker.py", line 202, in start
reporter-worker-1  |     self.blueprint.start(self)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/bootsteps.py", line 116, in start
reporter-worker-1  |     step.start(parent)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/bootsteps.py", line 365, in start
reporter-worker-1  |     return self.obj.start()
reporter-worker-1  |            ^^^^^^^^^^^^^^^^
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/worker/consumer/consumer.py", line 340, in start
reporter-worker-1  |     blueprint.start(self)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/bootsteps.py", line 116, in start
reporter-worker-1  |     step.start(parent)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/celery/bootsteps.py", line 397, in start
reporter-worker-1  |     self.consumers = self.get_consumers(channel)
reporter-worker-1  |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
reporter-worker-1  |   File "/app/backend/services/reporter/worker.py", line 162, in get_consumers
reporter-worker-1  |     Consumer(
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/messaging.py", line 414, in __init__
reporter-worker-1  |     self.revive(self.channel)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/messaging.py", line 436, in revive
reporter-worker-1  |     self.declare()
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/messaging.py", line 450, in declare
reporter-worker-1  |     queue.declare()
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/entity.py", line 617, in declare
reporter-worker-1  |     self._create_queue(nowait=nowait, channel=channel)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/entity.py", line 626, in _create_queue
reporter-worker-1  |     self.queue_declare(nowait=nowait, passive=False, channel=channel)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/kombu/entity.py", line 655, in queue_declare
reporter-worker-1  |     ret = channel.queue_declare(
reporter-worker-1  |           ^^^^^^^^^^^^^^^^^^^^^^
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/amqp/channel.py", line 1162, in queue_declare
reporter-worker-1  |     return queue_declare_ok_t(*self.wait(
reporter-worker-1  |                                ^^^^^^^^^^
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/amqp/abstract_channel.py", line 99, in wait
reporter-worker-1  |     self.connection.drain_events(timeout=timeout)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/amqp/connection.py", line 526, in drain_events
reporter-worker-1  |     while not self.blocking_read(timeout):
reporter-worker-1  |               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/amqp/connection.py", line 532, in blocking_read
reporter-worker-1  |     return self.on_inbound_frame(frame)
reporter-worker-1  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/amqp/method_framing.py", line 53, in on_frame
reporter-worker-1  |     callback(channel, method_sig, buf, None)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/amqp/connection.py", line 538, in on_inbound_method
reporter-worker-1  |     return self.channels[channel_id].dispatch_method(
reporter-worker-1  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/amqp/abstract_channel.py", line 156, in dispatch_method
reporter-worker-1  |     listener(*args)
reporter-worker-1  |   File "/usr/local/lib/python3.12/site-packages/amqp/channel.py", line 293, in _on_close
reporter-worker-1  |     raise error_for_code(
reporter-worker-1  | amqp.exceptions.PreconditionFailed: Queue.declare: (406) PRECONDITION_FAILED - inequivalent arg 'x-dead-letter-exchange' for queue 'report.jobs' in vhost '/': received none but current is the value '' of type 'longstr'


STDERR:
<empty>
```

## Observed Gaps in Current Implementation
- Reporter worker currently validates `report.jobs` envelopes only.
- Specialist workers are queue listeners; deeper stages land in later milestones.
- This report reflects what ran in this test session, not aspirational docs.
