# AttackBot End-to-End Findings Report

- Generated at: `2026-03-24T09:03:26.329942+00:00`
- Report file: `E2E_SYSTEM_FINDINGS.md`
- Project root: `C:\Users\Home\Desktop\Projects\Attackbot_v1`
- Test outcome: `in_progress_timeout`

## Requested Mode
- Full end-to-end execution attempted against current M3 stack.
- All feature flags were set to `true` in scan start payload.
- Live-mode policy: no seeded/dummy fallback for primary scan.
- Program selection override active via `E2E_PINNED_PROGRAM_HANDLE` / `E2E_PINNED_PROGRAM_ID`.

## Execution Steps
1. 2026-03-24T08:01:01.795270+00:00 | Starting end-to-end system trace test
1. 2026-03-24T08:01:01.795854+00:00 | .env present (loaded 0 missing keys into process env)
1. 2026-03-24T08:01:02.503723+00:00 | Bringing up stack with docker compose up -d
1. 2026-03-24T08:01:07.121360+00:00 | Health probe scraper: status_code=200
1. 2026-03-24T08:01:07.466581+00:00 | Health probe core-engine: status_code=200
1. 2026-03-24T08:01:39.904474+00:00 | Health probe reporter: status_code=None
1. 2026-03-24T08:02:12.359424+00:00 | Health probe attack-graph-engine: status_code=None
1. 2026-03-24T08:02:13.056864+00:00 | Health probe api-gateway: status_code=200
1. 2026-03-24T08:02:13.769315+00:00 | Connected to database backend=docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
1. 2026-03-24T08:02:13.769332+00:00 | Pinned program selector configured: E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'
1. 2026-03-24T08:02:13.769335+00:00 | HackerOne credentials detected; triggering live scraper sync
1. 2026-03-24T08:02:14.099920+00:00 | Scraper trigger responded with status_code=200
1. 2026-03-24T08:02:14.870412+00:00 | Selected live HackerOne program for scan: 6e7f4e62-7a0f-400b-a9da-398c648161cb (weblate) via policy=pinned_program_handle
1. 2026-03-24T08:02:15.805445+00:00 | Queue purge pre-check scan.jobs: ready=0 unacked=1 consumers=1
1. 2026-03-24T08:02:16.790540+00:00 | Queue purge attempt #1 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-24T08:03:21.427127+00:00 | Queue purge settle window scan.jobs: settled_unacked=False ready=0 unacked=1
1. 2026-03-24T08:03:22.481669+00:00 | Queue purge attempt #2 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-24T08:03:22.481688+00:00 | Waiting for queue baseline before triggering scan: queue=scan.jobs ready=0 timeout=60s
1. 2026-03-24T08:03:22.835369+00:00 | Queue baseline poll scan.jobs: ready=0 unacked=1 consumers=1
1. 2026-03-24T08:03:22.835420+00:00 | Queue baseline reached: scan.jobs ready=0
1. 2026-03-24T08:03:22.835428+00:00 | Triggering core scan with all feature flags enabled
1. 2026-03-24T09:03:24.222827+00:00 | Scan wait timed out after 3600s; collecting live snapshot
1. 2026-03-24T09:03:24.903175+00:00 | No scan_id available; skipped scan detail API/DB snapshots
1. 2026-03-24T09:03:25.796194+00:00 | Forced deep replay disabled in live mode (set E2E_ENABLE_FORCED_DEEP_TRACE=true to enable synthetic replay)

## Runtime Context
- DB connection backend: `docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit`
- Live HackerOne mode: `True`
- Program source: `hackerone_live_pinned`
- Program selection policy: `pinned_program_handle`
- Pinned program handle override: `weblate`
- Pinned program ID override: `None`
- Program ID: `6e7f4e62-7a0f-400b-a9da-398c648161cb`
- Program handle: `weblate`
- Scan ID: `None`
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
| 1315fda6-c093-4389-9365-24d464660591 | dropcontact | Dropcontact | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 92b67def-d6cd-4210-90c7-6a6a5d6049d2 | aig | AIG | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| 5a2a0bac-faec-431b-a3b2-1720a875eaeb | rebellion-defense | Rebellion Defense | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| ce225b05-de93-4794-803a-68456b94b5bf | estee-lauder |  Esteé  Lauder | hackerone | True | 471 | False | not selected: run pinned to explicit program selector(s) |
| 322b5053-7f3e-40a9-95b8-ce44c8056c90 | callsign | Callsign | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 63277526-d224-4d8f-9e43-18b402cfb2cd | polygon-technology | Polygon Technology | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| d93974c0-de5d-4e92-9141-97fe3ea918c6 | finra | FINRA Response | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| b8ecb6b7-4e68-43e7-adee-05a48b295d35 | blackrock | BlackRock | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 7ddb4bf8-e9f7-4d9f-94ce-0b90b67e508e | zebra_vdp | Zebra VDP | hackerone | True | 57 | False | not selected: run pinned to explicit program selector(s) |
| c6b0154b-ef80-49ef-bb8f-f771e5093603 | launchdarkly | LaunchDarkly | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| bb9eb57a-63c4-43fe-b6ec-fd0e74d15e5c | figma | Figma | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| a015ce0e-3758-472b-9b2b-dd92fd149baa | vendasta | Vendasta | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| e392fb6a-f758-40b9-bf1c-c9dc3873b3e1 | cs_money | CS Money | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 9a9f66f7-894d-4166-8b8d-7dd63783218d | mendix | Mendix | hackerone | True | 23 | False | not selected: run pinned to explicit program selector(s) |
| b67cfba5-4d87-4696-80a7-4fe58039fb72 | lichess | Lichess | hackerone | True | 48 | False | not selected: run pinned to explicit program selector(s) |
| 8bed05b2-6b97-43b4-8472-c8064dee2541 | insightly | Insightly | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 696b5925-0209-422e-a6d6-e946391d7f3f | trycourier | Courier | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 4f937622-125c-4983-b12d-e561d0ea3ebc | shutterfly_vdp | Shutterfly VDP | hackerone | True | 35 | False | not selected: run pinned to explicit program selector(s) |
| cb6ddb1d-7b2f-4133-befd-d9e1d1e3f559 | n45ht | N45HT | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2873891f-c2e9-4b1a-8e3e-936397c26fd1 | h1-ctf | h1-ctf | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 26fa2031-3729-4468-9d60-0fa822495417 | cognizant | Cognizant | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| 3ccf26f1-1c29-4ecb-80f0-4bad95f982c9 | ups | UPS VDP | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 6fabb9ea-a090-43d9-8018-88ca2b430389 | alibaba | Alibaba BBP | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 86514cb2-9ee7-4045-b700-23068381f6fb | openmage | OpenMage | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 803dcf50-c57c-484c-9ba9-c9c65d6b5c0e | shein | SHEIN | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 42bff9f7-a981-4dd6-a573-740a4ddc4afb | logsnitch | LogSnitch | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 8ba91bf7-af2b-41df-b14f-efefd02fb258 | cedars-sinai | Cedars-Sinai | hackerone | True | 39 | False | not selected: run pinned to explicit program selector(s) |
| f835eb2d-7557-41ec-b92f-bf39a884816c | flexport_vdp | Flexport VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| be220f3d-88ef-4400-8c60-49b49a16855d | gener8 | Gener8 | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 5b120193-97b0-4c7f-800b-219afa4cf6b7 | cirrusinsight | Cirrus Insight | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 2fe4446d-5174-47e3-8a51-2b0d2d7f1165 | stagingdoteverydotorg | Staging.every.org | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 5543a319-be5e-4883-8126-93f4d34237c2 | navient_solutions | Navient Solutions LLC | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 771c2f24-ca9f-4bb2-8ded-a7fe986e44d5 | btfs | BTFS | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 81110ddb-3a2d-4d5c-9415-7078af80f806 | r3 | R3 | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 97effe20-2938-4b3a-b93a-6a60db824426 | faraday_inc | Faraday, Inc. | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| d9821596-5413-4c83-91bc-7a5346ed5b75 | td-bank | TD Bank Group | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 12eb7baf-9ac4-4138-9392-060767197fa5 | aiven_ltd | Aiven Ltd | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| f2f4243b-7709-4603-9fbc-2b5621588cd5 | hostinger | hostinger  | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 8ad84356-ab78-4607-b1d1-35c4f536b31c | standard_notes | Standard Notes | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 634b23d0-0361-4adf-bcd1-9d4e4a129c49 | simple_poll | Simple Poll | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 41dbef41-e07d-4980-b2dc-d74bc4c2aff2 | skale_network | SKALE Network | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| cce5742d-76c7-485b-9be7-09722c5bc842 | rghost | RGhost | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 3abb2f59-4f25-482e-93a5-b5632a6862f2 | playstation | PlayStation | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| bdd062b4-d522-49a2-9891-e5883a270031 | myndr | Myndr | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 2309c43a-8d02-49fc-95d3-0eb9eeb2959e | pubg | PUBG | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 5fccff2b-e504-45f0-b88c-160e6dc69fec | chorus_jg4l2 | Chorus | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 4a0bba8e-8a12-4487-ac9f-cd832a487c2c | evernote | Evernote | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 00d87f92-f683-4e2e-aedc-b1366c1301d0 | earny | Earny | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 3b0dbe8f-12c2-4544-8eb6-f1122e9f7532 | usps | USPS - United States Postal Service | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 772b7f0a-2eab-44d8-843e-c53e6e20bbac | truecaller | Truecaller  | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| c48e7bbd-a946-4240-aa30-d30f5ef5eb35 | picsart | Picsart | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 115116c9-7821-44d5-8f31-8aaebe2e8f43 | lemlist | lemlist | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 39ddc3c8-2235-488f-b526-5450ff7ba5ef | amazonvrp | Amazon Vulnerability Research Program | hackerone | True | 100 | False | not selected: run pinned to explicit program selector(s) |
| 54f2e8cf-1aa9-42e3-a8f5-6b24ddb46d42 | hcl_software | HCL Software Inc. | hackerone | True | 48 | False | not selected: run pinned to explicit program selector(s) |
| bccd1892-c449-4144-9ac1-fd7777535c04 | thomsonreuters-public | Thomson Reuters | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| d92cab14-409c-4e69-ad48-29d7e6bfa9a4 | exodus | Exodus | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| a77de624-2a02-4bd0-9cf5-21719c8179f2 | companyhub | CompanyHub | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| d2b31872-c476-496f-9faa-933e35acb349 | gmelius | Gmelius | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 3e0ea45b-16b5-43ce-8fcf-e6051dac70e8 | mobisystems_ltd | MobiSystems Ltd. | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| c5afde2a-fa7e-43b2-a4c7-99ed2d7cfe1d | thnks | Thnks | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| c9e1a9cb-494c-4da9-bb1b-2e7f84371dfa | oasisprotocol | Oasis Protocol Foundation | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 25b995eb-8a71-424c-9508-98191cd9b8bd | copper | Copper | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| e291283a-bece-4611-ad50-8cf947f576d8 | jnj_mobile | JNJ Mobile | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 640526e0-fe25-42c8-9e75-317087ba78f0 | overloop | Overloop | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 4056ed22-d013-4494-8aa1-291d9312b1ad | stripo | Stripo Inc | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 4976af33-8feb-4927-8400-893165527052 | palo_alto_software | Palo Alto Software | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 6778fdcb-f3c0-490d-8e4c-ed3b68b1cc7b | uphabit | UpHabit | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 317d2a46-3634-4a12-b07a-e19903883c0a | investnext | InvestNext | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 823e82ef-a3cb-4489-9704-a51c8915c67d | mtn_group | MTN Group | hackerone | True | 494 | False | not selected: run pinned to explicit program selector(s) |
| 1c62e816-1266-4bc6-b029-4404d2588c53 | panther_labs | Panther Labs | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| be13bad7-4386-41ed-98b9-7411b9af9bea | coinspot | CoinSpot | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 6366fb04-6e56-4b2d-a4ad-33622f339c55 | nuri | Nuri | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 9422141b-6275-475e-b821-2c01c6787b00 | people_interactive | People Interactive | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 3bab9a92-27de-4957-b41f-0bdb035237af | top_echelon_software | Top Echelon Software | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| b4d07c09-ead0-4a6c-a2e3-1f83d6a347e2 | keybank | KeyBank | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| b6792cbc-89a0-477d-888c-11640caac6d4 | aodocs | AODocs | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 26394514-3922-4dad-9cca-c8c291f5f6ce | solidus | Solidus | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 0ee323c9-6e84-4ece-a496-121e92fac183 | lark_technologies | Lark Technologies | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| e6ab4892-aeca-4e40-979e-090e1dda18d5 | amitree_inc | Amitree Inc | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| f9235c88-4efe-47e2-bd40-81acecf08e13 | worklytics | Worklytics | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2ac2b205-74d5-4aca-ac7c-030272f7893e | mailtime_technology_inc | Mailtime Technology Inc. | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 95741101-7103-4ae2-bd72-e4d65aa3138c | replyify | Replyify | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 41b60cd7-e6f0-44ec-834c-4bb520aa5a16 | raivo | Raivo | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| ce1b6a76-0eef-4ba2-b2de-bc28eaddcb55 | consensys | Consensys | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| beebec81-9337-4aa0-a7fa-c1ffdffd2991 | gocardless_bbp | GoCardless Bug Bounty Program | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 1e71635f-488b-43fc-b715-15065857f988 | dynatrace | Dynatrace | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| ccec96ab-3727-49f6-8e23-07a5e32c6cf4 | forescout_technologies | ForeScout Technologies | hackerone | True | 63 | False | not selected: run pinned to explicit program selector(s) |
| ce3d38f5-fc2a-40fd-b502-725b1386334d | kubernetes | Kubernetes | hackerone | True | 83 | False | not selected: run pinned to explicit program selector(s) |
| c1e9c03d-7085-40fa-ab8d-d3d97637a0bb | midpoint_h1c | Midpoint (European Commission - DIGIT) | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| d4ff35d1-20b1-437f-ad5d-0a88e1e879b2 | impresscms | ImpressCMS | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 9ac7e70a-7b20-44a5-b2b9-619e2b7b6c62 | starling_bank | Starling Bank VDP | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 8e306685-7aed-4c31-832b-c3c5f75cdab1 | spell | Spell | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2151cb2c-83a8-4709-b19d-b8bf1a34ff2b | endless_group | Endless Group | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 582ba165-340c-462e-8e88-2fdd8aa70af6 | early_warning | Early Warning | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| ea28eb14-43ff-4f54-910f-517c4c877229 | ridewithvia | Via | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 311b3ec1-e862-4678-95af-09642bfd568b | apache_kafka_h1c | Apache Kafka (European Commission - DIGIT) | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| b81f2c67-a43b-45e6-a8ef-19f85147dbc1 | filezilla_h1c | FileZilla (European Commission - DIGIT) | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 0da5c421-5eb3-4917-88d0-acec7cd08682 | putty_h1c | PuTTY (European Commission - DIGIT) | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 9d2fbc16-75b1-4fd5-bd65-2e7be64774dc | vlc_h1c | VLC (European Commission - DIGIT) | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| fdc4bd36-5ccb-4062-bddc-d17dce74f243 | filezilla | FileZilla | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 1af0200a-b789-47ca-bc0c-0ada7ea954e6 | capital-one | Capital One | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| a71e9f2e-2f90-4ec0-b2f6-81ebba878727 | ford | Ford | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| e7c1445e-3b87-4d52-a146-8fd2cf1f7e88 | reddit | Reddit | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| cd6f7da3-10fc-48bd-a02c-bb0fe7d72962 | curl | curl | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 68085551-a6f1-4995-8c11-437410b0e67e | remitano | Remitano | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| e2fff78a-ecf4-4d6e-971d-b803b6a024a3 | instacart | Instacart | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 405fc1b8-752e-4b9c-acfe-07ae2ee2bafe | central-security-project | Central Security Project | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| cbd10c54-be1a-4509-8f5c-ea0d27f170fb | fronthq | Front | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 41a1e9f5-81ef-4db4-b9e2-f3371ed6d34d | etoro_bbp | eToro BBP | hackerone | True | 42 | False | not selected: run pinned to explicit program selector(s) |
| e33d02e7-2157-4b7e-a977-4498a2a73d77 | insulet_corporation | Insulet Corporation | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| d881a921-c30c-484e-9531-99cdf8087e88 | fanduel | FanDuel | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 1c73fa85-6945-46e1-a6fc-b9bc8f570602 | sweatco_ltd | Sweatco Ltd | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 20a0e8f6-e13e-4403-a1bc-d5db01c1eab5 | expediagroup_bbp | Expedia Group Bug Bounty | hackerone | True | 53 | False | not selected: run pinned to explicit program selector(s) |
| 32e2fb94-54b4-413a-8857-61d180ad6b61 | urbancompany | Urban Company | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 2db2ffca-a15e-48a7-97a5-f48da6bfdf74 | creditkarma | Credit Karma | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 955a7cd5-4d7a-456c-905c-30bd156910a3 | mercadolibre | MercadoLibre | hackerone | True | 67 | False | not selected: run pinned to explicit program selector(s) |
| 7c225209-349a-4fba-87be-346f58d5cefb | expediagroup | Expedia Group VDP | hackerone | True | 35 | False | not selected: run pinned to explicit program selector(s) |
| 41ae4fe4-0e68-482e-9a82-cd2f17e5c567 | defectdojo | DefectDojo | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 83f3858a-f1f7-41e3-8f56-ee8abca85fbc | flickr | Flickr | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 7e8813c0-4b39-4615-969e-9ecf26404bad | logitech | Logitech | hackerone | True | 86 | False | not selected: run pinned to explicit program selector(s) |
| 15d9b87c-4022-442b-b0b8-d74811515508 | remitly | Remitly | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| 135c6e67-72b1-4421-81fc-f83ff88a5dea | eslint | ESLint | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 995f1f36-42ad-47a6-ac49-1fcb58b0bc95 | chainlink | Chainlink | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| a586b917-634b-4c80-9e03-49edb66caca3 | nisc | NISC-VDP | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| eb057109-8ced-44b1-b573-5d717fa141b7 | marriott | Marriott Bug Bounty Program | hackerone | True | 80 | False | not selected: run pinned to explicit program selector(s) |
| e4d1112d-cbdc-465a-9f68-c45c156d8ded | cfptime | CFP Time | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 6848701b-69ee-4fd7-8490-8e3bd8364c80 | chaturbate | Chaturbate | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| b5ac8061-4400-4252-abfe-f69ec6b6d541 | hannob | Hanno's projects | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| ff05b5b8-18ca-42a3-b232-c9edd6ea805c | s-pankki | S-Pankki | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| e05cfe25-b802-4f2d-bd5c-df7339dae5da | arkadiyt-projects | arkadiyt-projects | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 1881f6ca-9b8f-4df0-b575-034c37a6a06d | pixiv | pixiv | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 2aab1a9c-5176-4da8-acea-6cc322bc0c10 | liberapay | Liberapay | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 167c9df5-c7e3-4561-a711-0d0282adbced | crypto | Crypto.com | hackerone | True | 23 | False | not selected: run pinned to explicit program selector(s) |
| 2fbdcfe0-7255-497f-888f-7ff1495b490f | ratelimited | RATELIMITED | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 2f46a142-616c-4851-8557-65155f574ba0 | ycombinator | Y Combinator | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| d9790fa2-c1e4-4eec-9589-1636c5d9a7da | passhash | passhash | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 45dc06e3-e022-4044-93a8-410dcae153d2 | pingidentity | Ping Identity | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 2cd4374b-7474-4e2b-817f-a566904bc9ed | crowdstrike | Crowdstrike | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| 560961c8-2bad-420a-bf05-861ff4a4e465 | affirm | Affirm | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| a414ca84-f09c-4f45-b2d7-815e46f68dd7 | coalition | Coalition, Inc. | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| dda96618-8834-4cfc-babe-1dc5db15669d | cosmos | Cosmos | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 60fafd88-f4a6-42a6-980b-64e189962fb3 | databricks | Databricks | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 5f524a60-478c-4225-8eaa-341e694abf6c | flutteruki | Flutter UK&I | hackerone | True | 42 | False | not selected: run pinned to explicit program selector(s) |
| 99770bc0-4a69-41f6-82e3-760b3433da53 | jamieweb | JamieWeb | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 354457aa-7dc4-426f-9315-fb5ad76a3a3e | ed | Ed | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 70c8bad9-b07b-4ae2-9546-a91700ddfd81 | bitmex | BitMEX | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| b4db9ca5-b6d1-4624-ae33-51ddc7b8d8b5 | smule | Smule | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 99f5d538-ad7e-4e8c-bcf7-e75f91b3de8f | fig | Fig | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| f6d29926-3daf-4514-92d6-b391e8f7d5d6 | elastic | Elastic | hackerone | True | 60 | False | not selected: run pinned to explicit program selector(s) |
| 41411df5-20f1-4764-ba33-9b607eaefc0f | valve | Valve | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| 12369ee1-fb66-4890-828d-037f5f878a61 | epicgames | Epic Games | hackerone | True | 85 | False | not selected: run pinned to explicit program selector(s) |
| ff5f44f7-84b5-4075-8622-14fc430c7f98 | deconf_com | Deconf | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 5eadcf25-0b60-4264-a403-3b2718eb9870 | nodejs | Node.js | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 231cc23d-f8d4-464b-8b23-a476c6217869 | netlify | Netlify | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 395a645f-8fda-485e-825f-1c6f3b5004d9 | kartpay | Kartpay | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| e2693bfb-fb61-4085-98a4-30d88f3b6a74 | streak_com | Streak | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| c607b815-fc86-49a0-8c23-d5526c4525ca | usertesting | UserTesting | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| bd68f803-bb66-4f2c-9b9b-a93833873809 | superhuman | Superhuman (formerly Grammarly) | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| 0bb51995-bc1f-4b29-b1da-ce42c06ff51a | hyperledger | Linux Foundation Decentralized Trust | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| b94274cf-e32d-4b08-93bf-7ee7a435c30f | upserve | Upserve  | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 230e00ec-3fed-498b-b357-fcdd272a349a | malwarebytes | Malwarebytes | hackerone | True | 36 | False | not selected: run pinned to explicit program selector(s) |
| a4446391-c627-4259-a794-8fa987918a9b | delight_im | delight.im | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| d64ed3f0-ecc7-4fb7-af7a-67aa5d19736c | wakatime | WakaTime | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 6d2e6c82-8418-42b3-af11-1a317eb3339a | yoti | Yoti | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 9fceae7f-57e6-4f5f-be7f-d04776b1ab49 | infogram | Infogram | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 961b3766-6ddf-4c98-9e16-256aaf5495a6 | bumble | Bumble | hackerone | True | 50 | False | not selected: run pinned to explicit program selector(s) |
| 89a9fe01-6ad8-4116-8493-7c2a3d1c6c3b | wink_jq3al | WINK | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| a8935f9c-e3fa-40e9-b117-92eaa2e83018 | omise | Omise | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| a3e6da23-751a-460c-861f-883c63cee88b | bitwarden | Bitwarden | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| b973e214-6904-4a36-ae9b-a6b8779a88cf | parrot_sec | Parrot Sec | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 0495cdc2-2f7a-4a4c-8a45-82331cc636fa | stellar | Stellar.org | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| dafaef72-05eb-4cea-850c-6a28f5e01832 | teradici | Teradici | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| edeaf83f-6e9f-4452-ba0a-bdbdc2a38653 | autodesk | Autodesk | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 37314144-6a37-4eb2-9570-0ba319f0cd94 | rocket_chat | Rocket.Chat | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 5039f25c-dca8-468b-a3cc-6088d5061ac5 | roblox | Roblox | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 6e7f4e62-7a0f-400b-a9da-398c648161cb | weblate | Weblate | hackerone | True | 6 | True | selected: matched E2E_PINNED_PROGRAM_HANDLE=weblate |
| 402ad4a2-ad7e-4916-a413-94e4b3b58f4c | homebrew | Homebrew | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d4eb30b8-bdb4-44a8-94ca-88eb7f38db35 | oportun_vdp | Oportun | hackerone | True | 44 | False | not selected: run pinned to explicit program selector(s) |
| 64c8cbc9-9a86-424b-a909-391216363988 | rbkmoney | RBKmoney | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 9cac4292-e873-4f48-94c1-125a6c3844f2 | nordsecurity | Nord Security | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| ac6fbf30-0d88-4281-80d1-3b7bcc12eb56 | discourse | Discourse | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 8200ae94-af09-4cac-b684-169e0723ec31 | nutanix | Nutanix | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| bd9aa5aa-119b-48af-b7dd-4379c5358e7c | mapsmarker_com_e_u | MapsMarker.com e.U. | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| a36c25a9-4b62-4074-b1a1-342815d8783d | nintendo | Nintendo | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| a138bc0a-4447-4966-bb8c-1c74f9c15171 | sony | Sony | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 33d4c605-6736-422b-9738-ceb8e40f43a6 | alvosec | Alvosec | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 067a3372-2c26-4cd5-9e8a-eb1e0b29eeae | enjin | Enjin | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| abe31247-34ba-4eae-ae09-70ff158a8eec | lyst | Lyst | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 1514a635-9c0a-4b64-b5d2-b363bda95a03 | disclosure-assistance | Disclosure Assistance | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 2678455c-ace8-4b05-8779-fb155fc6b65d | xiaomi | Xiaomi | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 2cdcd0ca-ce0f-428a-a76c-9325948a3895 | deptofdefense | U.S. Dept Of Defense | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 94f0c9ab-b44d-4ba1-991a-f70eb1407496 | semrush | Semrush | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 921de303-2b2d-4318-8a23-340bf42c64be | brave | Brave Software | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 4ff43bb7-f27a-43f4-8cf8-10fb7f61d039 | shopify-scripts | shopify-scripts | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| dbc4a0ce-a18c-4e8a-8f22-73c9b1f5560e | cornershop | Cornershop | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| eb10d4df-480f-4709-b3b9-bcffeeffdac3 | plaid | Plaid | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 72f9f60f-f776-452e-9369-28ead1dfb4b9 | portswigger | PortSwigger Web Security | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| f81474d7-9616-42b8-9511-7c99e7eddbd5 | toyota | Toyota | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 80083660-d58e-4cda-9ae9-d76bfab3d92f | localizejs | Localize | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| fed60227-0528-41df-aa9a-8aa3ba2f3d17 | hiro | Hiro | hackerone | True | 0 | False | no non-empty in_scope scope entries |

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
    "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb",
    "status": "queued"
  },
  "status_code": 200
}
```

### Final Scan Row
```json
{}
```

### Scan Wait Result
```json
{
  "note": "No scan row observed after start request",
  "status_at_snapshot": null,
  "terminal_reached": false,
  "timeout_seconds": 3600
}
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
        "consumers": 1,
        "exists": true,
        "messages": 0,
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
        "messages": 1,
        "messages_ready": 0,
        "messages_unacknowledged": 1,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "state_before": {
        "consumers": 1,
        "exists": true,
        "messages": 1,
        "messages_ready": 0,
        "messages_unacknowledged": 1,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "unacked_after": 1,
      "unacked_before": 1
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
        "messages": 1,
        "messages_ready": 0,
        "messages_unacknowledged": 1,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "state_before": {
        "consumers": 1,
        "exists": true,
        "messages": 1,
        "messages_ready": 0,
        "messages_unacknowledged": 1,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "unacked_after": 1,
      "unacked_before": 1
    }
  ],
  "enabled": true,
  "final_state": {
    "consumers": 1,
    "exists": true,
    "messages": 1,
    "messages_ready": 0,
    "messages_unacknowledged": 1,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "initial_state": {
    "consumers": 1,
    "exists": true,
    "messages": 1,
    "messages_ready": 0,
    "messages_unacknowledged": 1,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "ok": true,
  "queue": "scan.jobs",
  "settle_poll_seconds": 5.0,
  "settle_state": {
    "consumers": 1,
    "exists": true,
    "messages": 1,
    "messages_ready": 0,
    "messages_unacknowledged": 1,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "settle_timeout_seconds": 60,
  "settled_unacked": false
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
    "messages": 1,
    "messages_ready": 0,
    "messages_unacknowledged": 1,
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
| browser.jobs | True | 0 | 0 | 0 | 1 |  |  |
| browser.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| api.fuzz.jobs | True | 0 | 0 | 0 | 1 |  |  |
| api.fuzz.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| js.analysis.jobs | True | 0 | 0 | 0 | 1 |  |  |
| js.analysis.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| scenario.jobs | True | 0 | 0 | 0 | 1 |  |  |
| scenario.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| verify.jobs | True | 0 | 0 | 0 | 1 |  |  |
| verify.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| ai.analysis.jobs | True | 0 | 0 | 0 | 1 |  |  |
| ai.analysis.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| report.jobs | True | 0 | 0 | 0 | 1 |  |  |
| report.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| reports.completed | True | 0 | 0 | 0 | 0 |  |  |

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
- Reason: `Forced deep replay disabled in live mode (set E2E_ENABLE_FORCED_DEEP_TRACE=true to enable synthetic replay)`

## Process Evidence
### Command: docker compose up -d
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env up -d`

```text
STDOUT:
<empty>

STDERR:
 Container attackbot-postgres-1  Running
 Container attackbot-minio-1  Running
 Container attackbot-rabbitmq-1  Running
 Container attackbot-neo4j-1  Running
 Container attackbot-vault-1  Running
 Container attackbot-redis-1  Running
 Container attackbot-attack-graph-engine-1  Running
 Container attackbot-core-engine-1  Running
 Container attackbot-loki-1  Running
 Container attackbot-scraper-1  Running
 Container attackbot-prometheus-1  Running
 Container attackbot-api-fuzzer-worker-1  Running
 Container attackbot-browser-worker-1  Running
 Container attackbot-grafana-1  Running
 Container attackbot-js-analysis-worker-1  Running
 Container attackbot-ai-analysis-worker-1  Running
 Container attackbot-core-worker-1  Running
 Container attackbot-exploit-verifier-1  Running
 Container attackbot-reporter-1  Running
 Container attackbot-scenario-runner-1  Running
 Container attackbot-api-gateway-1  Running
 Container attackbot-reporter-worker-1  Running
 Container attackbot-tempo-1  Starting
 Container attackbot-vault-1  Waiting
 Container attackbot-minio-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-tempo-1  Started
 Container attackbot-postgres-1  Healthy
 Container attackbot-vault-1  Healthy
 Container attackbot-migrate-1  Starting
 Container attackbot-vault-init-1  Starting
 Container attackbot-minio-1  Healthy
 Container attackbot-minio-init-1  Starting
 Container attackbot-vault-init-1  Started
 Container attackbot-minio-init-1  Started
 Container attackbot-migrate-1  Started
 Container attackbot-redis-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-neo4j-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-redis-1  Healthy
 Container attackbot-postgres-1  Healthy
 Container attackbot-postgres-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-neo4j-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-postgres-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-minio-init-1  Exited
 Container attackbot-minio-init-1  Exited
 Container attackbot-minio-init-1  Exited
 Container attackbot-migrate-1  Exited
 Container attackbot-reporter-1  Waiting
 Container attackbot-migrate-1  Exited
 Container attackbot-migrate-1  Exited
 Container attackbot-migrate-1  Exited
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-attack-graph-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-scraper-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-reporter-1  Waiting
 Container attackbot-attack-graph-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-reporter-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-reporter-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-scraper-1  Healthy

```

### Command: docker compose ps
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env ps`

```text
STDOUT:
NAME                              IMAGE                           COMMAND                  SERVICE               CREATED             STATUS                          PORTS
attackbot-ai-analysis-worker-1    attackbot-ai-analysis-worker    "celery -A backend.sâ€¦"   ai-analysis-worker    About an hour ago   Up About an hour                
attackbot-api-fuzzer-worker-1     attackbot-api-fuzzer-worker     "celery -A backend.sâ€¦"   api-fuzzer-worker     About an hour ago   Up About an hour                
attackbot-api-gateway-1           attackbot-api-gateway           "uvicorn backend.serâ€¦"   api-gateway           About an hour ago   Up About an hour (unhealthy)    0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
attackbot-attack-graph-engine-1   attackbot-attack-graph-engine   "uvicorn backend.serâ€¦"   attack-graph-engine   About an hour ago   Up About an hour (healthy)      8006/tcp
attackbot-browser-worker-1        attackbot-browser-worker        "celery -A backend.sâ€¦"   browser-worker        About an hour ago   Up About an hour                
attackbot-core-engine-1           attackbot-core-engine           "uvicorn backend.serâ€¦"   core-engine           59 minutes ago      Up 58 minutes (healthy)         0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
attackbot-core-worker-1           attackbot-core-worker           "celery -A backend.sâ€¦"   core-worker           59 minutes ago      Up 58 minutes                   8002/tcp
attackbot-exploit-verifier-1      attackbot-exploit-verifier      "celery -A backend.sâ€¦"   exploit-verifier      About an hour ago   Up About an hour                
attackbot-grafana-1               grafana/grafana:latest          "/run.sh"                grafana               About an hour ago   Up About an hour                0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
attackbot-js-analysis-worker-1    attackbot-js-analysis-worker    "celery -A backend.sâ€¦"   js-analysis-worker    About an hour ago   Up About an hour                
attackbot-loki-1                  grafana/loki:latest             "/usr/bin/loki -confâ€¦"   loki                  About an hour ago   Up About an hour                3100/tcp
attackbot-minio-1                 minio/minio                     "/usr/bin/docker-entâ€¦"   minio                 About an hour ago   Up About an hour (healthy)      9000/tcp
attackbot-neo4j-1                 neo4j:5-community               "tini -g -- /startupâ€¦"   neo4j                 About an hour ago   Up About an hour (healthy)      7473-7474/tcp, 7687/tcp
attackbot-postgres-1              postgres:16                     "docker-entrypoint.sâ€¦"   postgres              About an hour ago   Up About an hour (healthy)      0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
attackbot-prometheus-1            prom/prometheus:latest          "/bin/prometheus --câ€¦"   prometheus            About an hour ago   Up About an hour                9090/tcp
attackbot-rabbitmq-1              rabbitmq:3-management           "docker-entrypoint.sâ€¦"   rabbitmq              About an hour ago   Up About an hour (healthy)      0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
attackbot-redis-1                 redis:7-alpine                  "docker-entrypoint.sâ€¦"   redis                 About an hour ago   Up About an hour (healthy)      6379/tcp
attackbot-reporter-1              attackbot-reporter              "uvicorn backend.serâ€¦"   reporter              About an hour ago   Up About an hour (healthy)      8003/tcp
attackbot-reporter-worker-1       attackbot-reporter-worker       "celery -A backend.sâ€¦"   reporter-worker       About an hour ago   Up About an hour                8003/tcp
attackbot-scenario-runner-1       attackbot-scenario-runner       "celery -A backend.sâ€¦"   scenario-runner       About an hour ago   Up About an hour                
attackbot-scraper-1               attackbot-scraper               "uvicorn backend.serâ€¦"   scraper               59 minutes ago      Up 58 minutes (healthy)         0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
attackbot-tempo-1                 grafana/tempo:latest            "/tempo"                 tempo                 About an hour ago   Restarting (1) 11 seconds ago   
attackbot-vault-1                 hashicorp/vault:1.15            "docker-entrypoint.sâ€¦"   vault                 About an hour ago   Up About an hour (healthy)      8200/tcp


STDERR:
<empty>
```

### Command: docker compose logs (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env logs --no-color --since 2026-03-24T08:03:22Z --tail 300 scraper core-engine core-worker reporter reporter-worker`

```text
STDOUT:
core-engine-1  | INFO:     127.0.0.1:39918 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:41760 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:60650 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:57778 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:57720 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:58370 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:55380 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:48108 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:50030 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:60200 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:38012 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:43776 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:41634 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:38028 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:37982 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:50888 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:57974 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:40472 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:41508 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:42222 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:36802 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:58566 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:49754 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:44522 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:42296 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:38368 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:41988 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:44680 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:46490 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:49708 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:59856 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:37880 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:41910 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:37966 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:60546 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:41864 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:51436 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:38468 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:45016 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:44580 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:45482 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:50208 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:33086 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:38974 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:55486 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | Running job "recover_stuck_scans (trigger: interval[0:05:00], next run at: 2026-03-24 08:52:42 UTC)" (scheduled at 2026-03-24 08:47:42.473726+00:00)
core-engine-1  | Job "recover_stuck_scans (trigger: interval[0:05:00], next run at: 2026-03-24 08:52:42 UTC)" executed successfully
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:53640 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:56390 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     172.20.0.13:44692 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:45690 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | INFO:     127.0.0.1:37594 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:52326 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:57212 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     127.0.0.1:55364 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:50416 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:41800 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:40904 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | INFO:     127.0.0.1:40696 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:54528 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     172.20.0.13:46400 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:52206 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     127.0.0.1:33406 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | Running job "Reconciler.reconcile (trigger: interval[0:05:00], next run at: 2026-03-24 08:52:12 UTC)" (scheduled at 2026-03-24 08:47:12.155146+00:00)
core-engine-1  | INFO:     172.20.0.3:59994 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | {"reason": "E2E_PAUSE_RECONCILER is enabled", "event": "reconciler_paused", "service": "scraper", "level": "info", "timestamp": "2026-03-24T08:47:12.155827Z"}
scraper-1      | Job "Reconciler.reconcile (trigger: interval[0:05:00], next run at: 2026-03-24 08:52:12 UTC)" executed successfully
scraper-1      | INFO:     172.20.0.13:45596 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:51844 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:38586 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:55422 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:36558 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:47258 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:43166 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:60384 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     172.20.0.3:49058 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:32930 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:53712 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:51134 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     127.0.0.1:50778 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:37666 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     172.20.0.3:35912 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | INFO:     127.0.0.1:52778 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:58604 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:45016 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:54226 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:50942 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:40146 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:55300 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:44246 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     172.20.0.13:58088 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     127.0.0.1:55724 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:35850 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:46724 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:47214 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:39804 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:58606 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     127.0.0.1:37396 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     127.0.0.1:59234 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:33022 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:59898 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:46170 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:58766 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:55262 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:40606 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:42866 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:39154 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:54134 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:49636 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:50668 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:37954 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:40166 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:34192 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:37044 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     172.20.0.13:55480 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     127.0.0.1:46958 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:33744 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.3:53374 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:43328 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:52068 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:38320 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:37806 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     172.20.0.3:45178 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | INFO:     127.0.0.1:49964 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:49852 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:47444 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:53174 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:36456 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:35818 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:37130 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:60518 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | INFO:     172.20.0.3:39578 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     172.20.0.13:54054 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:56176 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:42422 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:60322 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:50480 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     127.0.0.1:39088 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:40204 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:49706 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:47622 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:55794 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:59858 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:55544 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:54460 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:47628 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:58908 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1      | INFO:     172.20.0.13:51328 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:41134 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:41116 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     127.0.0.1:36588 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:33250 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:33974 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:50896 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | Running job "recover_stuck_scans (trigger: interval[0:05:00], next run at: 2026-03-24 08:57:42 UTC)" (scheduled at 2026-03-24 08:52:42.473726+00:00)
core-engine-1  | Job "recover_stuck_scans (trigger: interval[0:05:00], next run at: 2026-03-24 08:57:42 UTC)" executed successfully
scraper-1      | INFO:     172.20.0.13:57534 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:37664 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:52806 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | INFO:     172.20.0.3:48656 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:44658 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:47384 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:33770 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:42064 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:55120 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:50972 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.20.0.3:42610 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:44374 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:58558 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:36874 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:57340 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:56924 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:54672 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:45644 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:49360 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:60720 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:41406 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:52506 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:55126 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:57544 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.13:44976 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:40658 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.20.0.3:48126 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.20.0.13:35760 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:51512 - "GET /a
... [truncated]

STDERR:
<empty>
```

### Command: docker compose logs reporter-worker (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env logs --no-color --since 2026-03-24T08:03:22Z --tail 300 reporter-worker`

```text
STDOUT:
reporter-worker-1  | [2026-03-24 08:50:37,746: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "923f3129-eaf7-492a-bcdd-057d7055f4b5", "event_type": "scan.completed", "scan_id": "97db2ef8-a621-49ed-be2c-3e8fd0d0de49", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T08:50:37.735778Z"}
reporter-worker-1  | [2026-03-24 08:50:37,752: WARNING/MainProcess] {"scan_id": "97db2ef8-a621-49ed-be2c-3e8fd0d0de49", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T08:50:37.752550Z"}
reporter-worker-1  | [2026-03-24 08:50:37,753: WARNING/MainProcess] {"scan_id": "97db2ef8-a621-49ed-be2c-3e8fd0d0de49", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-24T08:50:37.752992Z"}


STDERR:
<empty>
```

## Observed Gaps in Current Implementation
- Reporter worker currently validates `report.jobs` envelopes only.
- Specialist workers are queue listeners; deeper stages land in later milestones.
- This report reflects what ran in this test session, not aspirational docs.
