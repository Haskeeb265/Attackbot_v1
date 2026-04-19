# AttackBot End-to-End Findings Report

- Generated at: `2026-03-25T03:46:53.729490+00:00`
- Report file: `E2E_Runs/E2E_SYSTEM_FINDINGS#7.md`
- Project root: `C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1`
- Test outcome: `completed`

## Requested Mode
- Full end-to-end execution attempted against current M3 stack.
- All feature flags were set to `true` in scan start payload.
- Live-mode policy: no seeded/dummy fallback for primary scan.
- Program selection override active via `E2E_PINNED_PROGRAM_HANDLE` / `E2E_PINNED_PROGRAM_ID`.

## Execution Steps
1. 2026-03-25T03:43:00.257224+00:00 | Starting end-to-end system trace test
1. 2026-03-25T03:43:00.257485+00:00 | .env present (loaded 0 missing keys into process env)
1. 2026-03-25T03:43:00.865947+00:00 | Bringing up stack with docker compose up -d
1. 2026-03-25T03:43:48.814924+00:00 | Health probe scraper: status_code=200
1. 2026-03-25T03:43:49.239614+00:00 | Health probe core-engine: status_code=200
1. 2026-03-25T03:44:22.393510+00:00 | Health probe reporter: status_code=None
1. 2026-03-25T03:44:55.559100+00:00 | Health probe attack-graph-engine: status_code=None
1. 2026-03-25T03:44:56.002254+00:00 | Health probe api-gateway: status_code=200
1. 2026-03-25T03:44:56.827639+00:00 | Connected to database backend=docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
1. 2026-03-25T03:44:56.827658+00:00 | Pinned program selector configured: E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'
1. 2026-03-25T03:44:56.827662+00:00 | HackerOne credentials detected; triggering live scraper sync
1. 2026-03-25T03:44:57.243151+00:00 | Scraper trigger responded with status_code=200
1. 2026-03-25T03:44:58.759026+00:00 | Selected existing real program with scope: 2715b22b-3506-4fb1-bece-95cad2eec341 (weblate) via policy=pinned_program_handle
1. 2026-03-25T03:45:00.767299+00:00 | Queue purge pre-check scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-25T03:45:02.072452+00:00 | Queue purge attempt #1 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-25T03:45:02.508313+00:00 | Queue purge settle window scan.jobs: settled_unacked=True ready=0 unacked=0
1. 2026-03-25T03:45:03.859882+00:00 | Queue purge attempt #2 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-25T03:45:03.859910+00:00 | Waiting for queue baseline before triggering scan: queue=scan.jobs ready=0 unacked=0 timeout=60s
1. 2026-03-25T03:45:04.295005+00:00 | Queue baseline poll scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-25T03:45:04.295037+00:00 | Queue baseline reached: scan.jobs ready=0 unacked=0
1. 2026-03-25T03:45:04.295043+00:00 | Triggering core scan with all feature flags enabled
1. 2026-03-25T03:45:16.516398+00:00 | Scan start response included scan_id=aa869b2a-7992-4217-9225-88d7157b3642
1. 2026-03-25T03:45:17.243821+00:00 | Scan status transition observed: running
1. 2026-03-25T03:46:46.822435+00:00 | Scan status transition observed: completed
1. 2026-03-25T03:46:46.822452+00:00 | Terminal scan status reached: completed

## Runtime Context
- DB connection backend: `docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit`
- Live HackerOne mode: `False`
- Program source: `existing_real_pinned`
- Program selection policy: `pinned_program_handle`
- Pinned program handle override: `weblate`
- Pinned program ID override: `None`
- Program ID: `2715b22b-3506-4fb1-bece-95cad2eec341`
- Program handle: `weblate`
- Scan ID: `aa869b2a-7992-4217-9225-88d7157b3642`
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
| 2715b22b-3506-4fb1-bece-95cad2eec341 | weblate | Weblate | hackerone | True | 6 | True | selected: matched E2E_PINNED_PROGRAM_HANDLE=weblate |
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
| d45dcf3d-14e5-4c43-bab8-167492552534 | deribit | Deribit | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 35ad2fe4-48e8-4a17-a5e9-684ca994a5bd | ro | Ro | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 3cd52096-3828-4949-8af3-f74fce05b487 | fidelity | Fidelity | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 4d6e498f-6828-4ade-986a-cf77bac04bdf | alohi | Alohi | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| ad08f212-cd63-4473-b0d1-fe1c99426786 | ripio | Ripio | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| ebcc6c62-a6fe-4621-9195-ca081c4d3770 | sorare | Sorare | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 865d9b09-5a63-45e5-ba6e-69fe2957de2e | mongodb | MongoDB | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| d45770fe-d005-420e-b34c-1052001cbb96 | unitigroup | Uniti | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 02ea3298-f9a0-4596-99e9-0973249b2f97 | sidefx | SideFX | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 1288744d-6f8e-458c-b6b9-36099d709026 | moov | Moov | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| e6f0e835-e637-4954-8e75-a859fced1c55 | hilton | Hilton | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| cfcef7a2-26a9-43e3-a3a3-c7413b693dcd | allegion | Allegion | hackerone | True | 134 | False | not selected: run pinned to explicit program selector(s) |
| 1ff8cf28-980c-4186-9c32-1321b5bccf4d | wickr | Wickr | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 81ee7cc0-102d-4383-8ac7-f296f6b04a9c | agoric | Agoric | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| e11db1c4-dcaa-45fc-b403-d83818783b09 | wellsfargo-bbp | Wells Fargo Bounty | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 136f26e5-c9cb-40c0-8827-565f00b80883 | fresenius | Fresenius | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| eeffd5de-4f21-4a87-a06d-da929a1278af | amazonvrp-devices | Amazon Vulnerability Research Program - Devices | hackerone | True | 33 | False | not selected: run pinned to explicit program selector(s) |
| 518e040c-fb7c-45e0-a920-553eff264f5d | mondelez | Mondelēz International | hackerone | True | 311 | False | not selected: run pinned to explicit program selector(s) |
| 54f5a094-36b6-4876-bd22-137055d49cfe | palantir_public | Palantir Public | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 2ca88bf3-1813-4c42-bad0-3137b31ae4b7 | divvy-homes | Divvy Homes | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 41088ada-d97b-4bcb-89eb-48838ebb963c | disney | The Walt Disney Company | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 109dd66a-2651-4642-9682-3d83d55ca559 | inspectorio | Inspectorio | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 579146b3-6fca-4a56-ba25-02e0b3546573 | clarivate | Clarivate | hackerone | True | 5027 | False | not selected: run pinned to explicit program selector(s) |
| a167fa9d-ef6e-42e7-b50a-eb1b285cdae0 | godaddy-vdp | GoDaddy VDP | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 75801c9c-22ca-403a-bb30-1261c36c3cf1 | veeam | Veeam | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 588f2cf8-393f-4ed0-a335-636792279162 | moonpay | MoonPay  | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 232c9f17-efc2-4617-9762-2b4e5d36f3f5 | redis-vdp | Redis VDP | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| b991b629-eaf0-4eca-9c07-a5aa3f567157 | pagerduty | PagerDuty | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 5b465710-b91f-46be-b8e2-004972fd0262 | apnic | APNIC | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| af48f049-eb34-47b5-8d69-2a5166f6144b | blend-labs | Blend Labs | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| acd2f7fc-8475-40c0-8308-e9a8957d150b | caterpillar | Caterpillar | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 35c77130-6fde-4537-85a4-c3990ba43ffe | ibb | Internet Bug Bounty | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| 621d8179-be24-4b5f-978a-c8d31be34693 | razorpay | Razorpay | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 820d9d25-4b34-4c44-bbb4-671df9825875 | oanda | OANDA | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 5d2eed5f-ac79-49c2-a15d-3071f5b5e57d | planet-labs | Planet Labs | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 10e79ab8-2e17-43a6-bfad-bd130628ac8b | tenable | Tenable | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| bd44874f-ff07-431d-97d0-71798251d234 | fastly-vdp | Fastly VDP | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 92f115ef-2130-4a58-8857-a9e85201c512 | sega | SEGA | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| d601075b-ca6f-4609-a601-04d4a9bc708e | koho | KOHO | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| a902e3b1-214a-47f1-885a-0b199fdc97d6 | hy-vee | Hy-Vee | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 23309003-ba37-41c5-98b3-198026dd524b | octopus-energy | Octopus Energy Group | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| bc6dfc77-1b8c-4120-92be-19d4654db9d4 | newegg | Newegg | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 7b6007b3-aaac-473e-92d1-1a58890e8079 | keurigdrpepper | Keurig Dr Pepper | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| c9494122-3510-4571-b606-57ae1ee75867 | tesco | Tesco | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| fafaf645-02f5-4e3a-ab61-6941bc59a751 | servicenow-disclosure | ServiceNow Disclosure | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| aac11905-f1eb-47d7-b724-2265d98be3f9 | particle-health-vdp | Particle Health VDP | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 9e3aa617-101e-46b6-adb1-c0175cc6db0b | krisp | Krisp | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| 193d8103-e71a-404e-b43a-8a001a19084a | zooplus | Zooplus | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| f3d84e78-8bc1-49cf-b4c9-816deaf78644 | whatnot | Whatnot | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| d77d1b7e-7d32-4170-b750-7415e8ab102b | us-department-of-state | U.S. Department of State | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| afdf5c2d-194b-44c7-ab5e-eebf867ff67b | latamairlines | LATAM Airlines | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 478ced79-94c0-45af-8b5b-793f3d3d1c8e | zurich-insurance | Zurich Insurance | hackerone | True | 42 | False | not selected: run pinned to explicit program selector(s) |
| 637948a7-7eaa-4b1e-a8fc-6ef18139f68c | nominet | Nominet | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 9c0104c8-a0f9-4410-95c9-a42dbfac8871 | upchieve | UPchieve | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d9b173c9-51bd-4719-8aba-2278cc755c2e | khealth | KHealth | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| a9df3ef4-e0e4-40e3-884a-fbcb354ce684 | smtp2go | SMTP2GO BBP | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| a425d59f-0bcb-43a4-beaa-9d38c85bea98 | playtika | Playtika | hackerone | True | 65 | False | not selected: run pinned to explicit program selector(s) |
| f879243f-0c72-47a6-b5c5-25fda3a7bada | beiersdorf | Beiersdorf | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| f147bc2f-f163-465a-bd11-c18954aaae18 | mcuboot | MCUboot | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 9744dd16-7b09-4bb7-9b46-116defd349c7 | vodafone | Vodafone | hackerone | True | 67 | False | not selected: run pinned to explicit program selector(s) |
| f58f5975-a765-4822-a95a-be2748493836 | fastify | Fastify | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 1ddce056-d0a2-4218-9e42-5010f5a752f9 | trendyol | Trendyol | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| dd36fa14-14f7-4b74-aa3a-516429ca71d4 | compass-bbp | Compass | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 61695502-fe6d-47bd-8816-ba4e7f86bb8f | mtb | M&T Bank Vulnerability Disclosure | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| b211cb09-f802-4163-83f7-ac6b570546b7 | dib-vdp | DIB-VDP | hackerone | True | 659 | False | not selected: run pinned to explicit program selector(s) |
| 3d2c410a-956c-4463-b602-7d3b8a1a7bcb | global-payments | Global Payments | hackerone | True | 34 | False | not selected: run pinned to explicit program selector(s) |
| 51fc3146-183e-4292-804e-ab23b0a83693 | glovo | Glovo | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 76c16a2d-b3c3-437f-a9b9-796a152f543f | jetblue | JetBlue | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 812bbd6f-38c6-4d06-890e-a3b37c9d24af | capital-one-bounty | Capital One Bug Bounty | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 35a64535-cf5b-4f84-afa2-bfc618ce598b | fanduel-vdp | FanDuel Response | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 15bce600-96b2-47fe-b581-4cf1f65f219a | who-covid-19-mobile-app | WHO COVID-19 Mobile App | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 41e65fb7-a719-46ae-9956-b2ea68026d40 | payoneer | Payoneer | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 86333b40-907d-4376-9687-58763167d6f3 | hypr-corp | HYPR | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| be425d22-de15-4fee-a287-3d7e610ab383 | pfizer | Pfizer | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 300d11bd-bec3-485a-a6e9-6b6c3bd98271 | costco | Costco | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 0d0d3ee8-48a4-48ec-8f1f-8930615183b1 | paystack-vdp | Paystack Vulnerability Disclosure | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 4803fe43-d0b0-4c88-b8d9-c3ca41a9fcab | stripe | Stripe | hackerone | True | 46 | False | not selected: run pinned to explicit program selector(s) |
| 36724ace-f7f1-4565-90ee-dcc00fd496b9 | on | On  | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| e43dcbca-9205-4371-880f-c154438e849f | judgeme | Judge.me  | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 94fca460-ba6a-4092-8bd1-cf4e4b426084 | doppler | Doppler | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 0a2f4e59-af1a-4416-adb8-3ebb2fde959c | gymshark | Gymshark | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 53530398-2993-43d3-bc5d-16c275ce8542 | emoney-advisor | eMoney Advisor | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| f4a911b8-0e9d-44a2-a427-ba81436caf71 | grindr | Grindr | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| c0289163-e5b1-4d24-9c52-4683f3447381 | csg-public | Cloud Software Group | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 70ef7227-5d67-4add-8599-fbdbbddc0ea9 | gsa_bbp | GSA Bounty | hackerone | True | 46 | False | not selected: run pinned to explicit program selector(s) |
| bf7231da-7106-4fa4-a729-a48e5f4ff8d7 | mars | Mars | hackerone | True | 110 | False | not selected: run pinned to explicit program selector(s) |
| 19e66ed9-9e3c-4a60-9e69-0663b8ba46dd | gsa_vdp | U.S. General Services Administration | hackerone | True | 426 | False | not selected: run pinned to explicit program selector(s) |
| b5c52123-aafa-4650-8d45-34f786d7a3d8 | xvideos | XVIDEOS | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| f46c712a-7c52-4afb-9186-8a3210c978da | trafficfactory | Traffic Factory | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| c91fbe74-2ee2-4aa8-9a60-243e33193bb7 | anywhererealestate | Anywhere Real Estate | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 6ff5cedd-8798-43e5-a2c7-d775116803db | ohiosecretaryofstate | Ohio Secretary of State | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 51c3be5b-3563-4a63-a98b-fff1caf08b55 | freshworks | Freshworks  | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 3f7c1041-18cd-4767-bbf8-d6718af9f26e | wonder-vdp | Blue Apron (Wonder Group) VDP | hackerone | True | 25 | False | not selected: run pinned to explicit program selector(s) |
| 78ccde73-23a1-42ea-acc3-768c649f3e1e | cbre | CBRE | hackerone | True | 8716 | False | not selected: run pinned to explicit program selector(s) |
| b6bf2821-79af-4480-b051-81ecf81e5411 | hudapp | Hud App | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| d122ea9c-aa96-4df6-97da-fbb8a2435a99 | 8x8-bounty | 8x8 | hackerone | True | 99 | False | not selected: run pinned to explicit program selector(s) |
| 232a2594-a4ac-4dcd-9905-17fd371a828d | john-deere | John Deere | hackerone | True | 1909 | False | not selected: run pinned to explicit program selector(s) |
| 22d8b1da-9e27-4637-995b-b508438990ef | tiktok | TikTok | hackerone | True | 39 | False | not selected: run pinned to explicit program selector(s) |
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
    "scan_id": "aa869b2a-7992-4217-9225-88d7157b3642",
    "status": "queued"
  },
  "status_code": 200
}
```

### Final Scan Row
```json
{
  "completed_at": "2026-03-25T03:46:46.161387+00:00",
  "created_at": "2026-03-25T03:45:04.780317+00:00",
  "error_detail": null,
  "finding_count": 0,
  "partial_detail": null,
  "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341",
  "retry_count": 0,
  "scan_id": "aa869b2a-7992-4217-9225-88d7157b3642",
  "severity_breakdown": "{\"low\": 0, \"high\": 0, \"info\": 0, \"medium\": 0, \"critical\": 0}",
  "started_at": "2026-03-25T03:45:04.780317+00:00",
  "status": "completed"
}
```

### Scan Wait Result
```json
{
  "status_at_snapshot": "completed",
  "terminal_reached": true,
  "timeout_seconds": 3600
}
```

### Pipeline Stage Timeline
| stage_number | stage_name | status | started_at | completed_at | error_detail |
| --- | --- | --- | --- | --- | --- |
| 1.0 | asset_discovery | completed | 2026-03-25T03:45:16.728596+00:00 | 2026-03-25T03:45:51.010800+00:00 |  |
| 2.0 | fingerprinting | completed | 2026-03-25T03:45:51.013420+00:00 | 2026-03-25T03:45:52.392187+00:00 |  |
| 3.0 | enumeration | completed | 2026-03-25T03:45:52.393910+00:00 | 2026-03-25T03:45:53.307107+00:00 |  |
| 4.0 | nuclei_scan | completed | 2026-03-25T03:45:52.393913+00:00 | 2026-03-25T03:46:46.150085+00:00 |  |
| 5.0 | web_vuln_tests | completed | 2026-03-25T03:45:53.308765+00:00 | 2026-03-25T03:46:46.153531+00:00 |  |
| 6.0 | js_secrets | completed | 2026-03-25T03:45:53.308834+00:00 | 2026-03-25T03:46:46.155941+00:00 |  |
| 10.1 | report_handoff | completed | 2026-03-25T03:46:46.163852+00:00 | 2026-03-25T03:46:46.173671+00:00 |  |

### Artifact Counts
```json
{
  "assets_count": 2,
  "endpoints_count": 6,
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
| scan.jobs | True | 1 | 0 | 1 | 1 |  |  |
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
{
  "payload": {
    "completed_at": "2026-03-25T03:46:46.161387+00:00",
    "error_detail": null,
    "finding_count": 0,
    "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341",
    "scan_id": "aa869b2a-7992-4217-9225-88d7157b3642",
    "severity_breakdown": {
      "critical": 0,
      "high": 0,
      "info": 0,
      "low": 0,
      "medium": 0
    },
    "started_at": "2026-03-25T03:45:04.780317+00:00",
    "status": "completed"
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/scans/aa869b2a-7992-4217-9225-88d7157b3642"
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
  "url": "http://localhost:8002/api/v1/scans/aa869b2a-7992-4217-9225-88d7157b3642/findings"
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
 Container attackbot-vault-1 Running 
 Container attackbot-redis-1 Running 
 Container attackbot-postgres-1 Running 
 Container attackbot-minio-1 Running 
 Container attackbot-prometheus-1 Running 
 Container attackbot-rabbitmq-1 Running 
 Container attackbot-neo4j-1 Running 
 Container attackbot-loki-1 Running 
 Container attackbot-grafana-1 Running 
 Container attackbot-attack-graph-engine-1 Running 
 Container attackbot-reporter-1 Running 
 Container attackbot-core-engine-1 Recreate 
 Container attackbot-scraper-1 Running 
 Container attackbot-reporter-worker-1 Running 
 Container attackbot-core-engine-1 Recreated 
 Container attackbot-js-analysis-worker-1 Running 
 Container attackbot-browser-worker-1 Running 
 Container attackbot-scenario-runner-1 Running 
 Container attackbot-exploit-verifier-1 Running 
 Container attackbot-ai-analysis-worker-1 Running 
 Container attackbot-api-fuzzer-worker-1 Running 
 Container attackbot-core-worker-1 Recreate 
 Container attackbot-api-gateway-1 Running 
 Container attackbot-core-worker-1 Recreated 
 Container attackbot-tempo-1 Starting 
 Container attackbot-minio-1 Waiting 
 Container attackbot-vault-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-tempo-1 Started 
 Container attackbot-vault-1 Healthy 
 Container attackbot-vault-init-1 Starting 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-migrate-1 Starting 
 Container attackbot-minio-1 Healthy 
 Container attackbot-minio-init-1 Starting 
 Container attackbot-migrate-1 Started 
 Container attackbot-neo4j-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-vault-init-1 Started 
 Container attackbot-minio-init-1 Started 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-neo4j-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-core-engine-1 Starting 
 Container attackbot-migrate-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-core-engine-1 Started 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-attack-graph-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-scraper-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-reporter-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-reporter-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-scraper-1 Healthy 
 Container attackbot-attack-graph-engine-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
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
attackbot-ai-analysis-worker-1    attackbot-ai-analysis-worker    "celery -A backend.sâ€¦"   ai-analysis-worker    22 minutes ago   Up 21 minutes                   
attackbot-api-fuzzer-worker-1     attackbot-api-fuzzer-worker     "celery -A backend.sâ€¦"   api-fuzzer-worker     22 minutes ago   Up 21 minutes                   
attackbot-api-gateway-1           attackbot-api-gateway           "uvicorn backend.serâ€¦"   api-gateway           58 minutes ago   Up 57 minutes (unhealthy)       0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
attackbot-attack-graph-engine-1   attackbot-attack-graph-engine   "uvicorn backend.serâ€¦"   attack-graph-engine   58 minutes ago   Up 58 minutes (healthy)         8006/tcp
attackbot-browser-worker-1        attackbot-browser-worker        "celery -A backend.sâ€¦"   browser-worker        22 minutes ago   Up 21 minutes                   
attackbot-core-engine-1           attackbot-core-engine           "uvicorn backend.serâ€¦"   core-engine           47 seconds ago   Up 40 seconds (healthy)         0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
attackbot-core-worker-1           attackbot-core-worker           "celery -A backend.sâ€¦"   core-worker           45 seconds ago   Up Less than a second           8002/tcp
attackbot-exploit-verifier-1      attackbot-exploit-verifier      "celery -A backend.sâ€¦"   exploit-verifier      22 minutes ago   Up 21 minutes                   
attackbot-grafana-1               grafana/grafana:latest          "/run.sh"                grafana               58 minutes ago   Up 58 minutes                   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
attackbot-js-analysis-worker-1    attackbot-js-analysis-worker    "celery -A backend.sâ€¦"   js-analysis-worker    22 minutes ago   Up 21 minutes                   
attackbot-loki-1                  grafana/loki:latest             "/usr/bin/loki -confâ€¦"   loki                  58 minutes ago   Up 58 minutes                   3100/tcp
attackbot-minio-1                 minio/minio                     "/usr/bin/docker-entâ€¦"   minio                 58 minutes ago   Up 58 minutes (healthy)         9000/tcp
attackbot-neo4j-1                 neo4j:5-community               "tini -g -- /startupâ€¦"   neo4j                 58 minutes ago   Up 58 minutes (healthy)         7473-7474/tcp, 7687/tcp
attackbot-postgres-1              postgres:16                     "docker-entrypoint.sâ€¦"   postgres              58 minutes ago   Up 58 minutes (healthy)         0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
attackbot-prometheus-1            prom/prometheus:latest          "/bin/prometheus --câ€¦"   prometheus            58 minutes ago   Up 58 minutes                   9090/tcp
attackbot-rabbitmq-1              rabbitmq:3-management           "docker-entrypoint.sâ€¦"   rabbitmq              58 minutes ago   Up 58 minutes (healthy)         0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
attackbot-redis-1                 redis:7-alpine                  "docker-entrypoint.sâ€¦"   redis                 58 minutes ago   Up 58 minutes (healthy)         6379/tcp
attackbot-reporter-1              attackbot-reporter              "uvicorn backend.serâ€¦"   reporter              22 minutes ago   Up 22 minutes (healthy)         8003/tcp
attackbot-reporter-worker-1       attackbot-reporter-worker       "celery -A backend.sâ€¦"   reporter-worker       22 minutes ago   Up 22 minutes                   8003/tcp
attackbot-scenario-runner-1       attackbot-scenario-runner       "celery -A backend.sâ€¦"   scenario-runner       22 minutes ago   Up 21 minutes                   
attackbot-scraper-1               attackbot-scraper               "uvicorn backend.serâ€¦"   scraper               58 minutes ago   Up 58 minutes (healthy)         0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
attackbot-tempo-1                 grafana/tempo:latest            "/tempo"                 tempo                 58 minutes ago   Restarting (1) 32 seconds ago   
attackbot-vault-1                 hashicorp/vault:1.15            "docker-entrypoint.sâ€¦"   vault                 58 minutes ago   Up 58 minutes (healthy)         8200/tcp


STDERR:
<empty>
```

### Command: docker compose logs (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env logs --no-color --since 2026-03-25T03:45:04Z --tail 300 scraper core-engine core-worker reporter reporter-worker`

```text
STDOUT:
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341 "HTTP/1.1 200 OK"
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope "HTTP/1.1 200 OK"
core-engine-1  | {"scan_id": "aa869b2a-7992-4217-9225-88d7157b3642", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "event": "Scan created", "service": "core-engine", "level": "info", "timestamp": "2026-03-25T03:45:04.790297Z"}
core-engine-1  | {"check": "nuclei", "detail": "/usr/local/bin/nuclei", "event": "worker_toolchain_check_ok", "service": "core-engine", "level": "info", "timestamp": "2026-03-25T03:45:16.401765Z"}
core-engine-1  | {"check": "nuclei_templates", "detail": null, "event": "worker_toolchain_check_ok", "service": "core-engine", "level": "info", "timestamp": "2026-03-25T03:45:16.401866Z"}
core-engine-1  | INFO:     172.18.0.1:41778 - "POST /api/v1/scans/start HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:41880 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:34726 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:51472 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:52554 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:38828 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:35980 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:35858 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:37844 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:46522 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:41002 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:43172 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:50966 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:46038 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:39798 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:55078 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:42466 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | INFO:     172.18.0.1:36584 - "GET /api/v1/scans/aa869b2a-7992-4217-9225-88d7157b3642 HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.1:36588 - "GET /api/v1/scans/aa869b2a-7992-4217-9225-88d7157b3642/findings HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.1:36596 - "GET /api/v1/queue/dlq/inspect HTTP/1.1" 200 OK
scraper-1      | INFO:     172.18.0.12:58310 - "GET /api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341 HTTP/1.1" 200 OK
scraper-1      | INFO:     172.18.0.12:58310 - "GET /api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:46702 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "boozt", "program_id": "a0a83ed8-f012-47d7-86ca-ee8a354a0d41", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:05.982712Z"}
scraper-1      | {"handle": "magic-eden", "program_id": "4657ef79-95ca-41f6-a710-1c681b563963", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:08.149224Z"}
scraper-1      | INFO:     172.18.0.8:47958 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | {"handle": "greenfly", "program_id": "1f5189f2-1c90-4a11-a3ba-381f3b88f483", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:11.601527Z"}
scraper-1      | {"handle": "pornbox", "program_id": "3681e0c6-db18-4d17-ab03-2303e8742818", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:14.026705Z"}
scraper-1      | INFO:     127.0.0.1:42780 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.18.0.12:47960 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "abn_amro_vdp", "program_id": "a543452f-a58d-4a0a-b904-1d455e9eda3a", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:16.574564Z"}
scraper-1      | INFO:     172.18.0.20:47826 - "GET /api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope HTTP/1.1" 200 OK
scraper-1      | {"handle": "superbet", "program_id": "f3ea0780-d119-4d6f-9caf-ac511dd3d248", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:18.714230Z"}
scraper-1      | {"handle": "okg", "program_id": "39e4b656-407a-4b54-bc2d-fe3b1c7f0bbc", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:20.615386Z"}
scraper-1      | {"handle": "redox_bbp", "program_id": "8ec6d75a-2e1f-40f6-921d-d93f2e17431b", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:22.547125Z"}
scraper-1      | INFO:     172.18.0.8:53404 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     172.18.0.12:59894 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "tron_dao", "program_id": "613dbb33-88e2-48de-9a34-1c45ea7def6e", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:24.481069Z"}
scraper-1      | INFO:     127.0.0.1:60324 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "stripchat", "program_id": "ddf08ab8-ad77-4f47-9325-6524b89ea264", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:26.239434Z"}
scraper-1      | {"handle": "mozilla", "program_id": "85c30330-4939-4ce3-87d2-5f887acd1dd4", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:28.461108Z"}
scraper-1      | {"handle": "fertitta_entertainment", "program_id": "f3b52586-ed0e-4d31-a491-ff79ea0012c8", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:30.337072Z"}
scraper-1      | {"handle": "truist_financial", "program_id": "55429276-a7e3-4b1c-b750-f7effd7acd6c", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:32.210982Z"}
scraper-1      | {"handle": "eero", "program_id": "14e786e0-4005-4c25-b6c0-138cc19e4ef7", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:34.090034Z"}
scraper-1      | INFO:     172.18.0.12:53088 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:33300 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "eufy_security", "program_id": "b947214a-7683-4b57-9885-b4096831fb9c", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:36.125457Z"}
scraper-1      | {"handle": "brightspeed", "program_id": "0b7b00bc-6299-4014-a878-140ceb7834b6", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:38.554902Z"}
scraper-1      | INFO:     172.18.0.8:53460 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | {"handle": "six-group", "program_id": "d9f269a7-ab0e-4858-a959-d2a14f6d0405", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:40.641092Z"}
scraper-1      | Running job "Reconciler.reconcile (trigger: interval[0:05:00], next run at: 2026-03-25 03:50:42 UTC)" (scheduled at 2026-03-25 03:45:42.116792+00:00)
scraper-1      | {"reason": "E2E_PAUSE_RECONCILER is enabled", "event": "reconciler_paused", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:42.117251Z"}
scraper-1      | Job "Reconciler.reconcile (trigger: interval[0:05:00], next run at: 2026-03-25 03:50:42 UTC)" executed successfully
scraper-1      | Running job "_publish_due_scan_jobs (trigger: interval[1:00:00], next run at: 2026-03-25 04:45:42 UTC)" (scheduled at 2026-03-25 03:45:42.117221+00:00)
scraper-1      | {"reason": "E2E_PAUSE_RECONCILER is enabled", "queue": "scan.jobs", "event": "scan_publish_batch_paused", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:42.117604Z"}
scraper-1      | Job "_publish_due_scan_jobs (trigger: interval[1:00:00], next run at: 2026-03-25 04:45:42 UTC)" executed successfully
scraper-1      | {"handle": "eurofins", "program_id": "ba0e7c1f-17b9-45e8-b1aa-fe6883dc1923", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:42.547266Z"}
scraper-1      | INFO:     172.18.0.12:33066 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "ring", "program_id": "3be932b8-fdd9-4ff6-a19e-f013d12056f1", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:45.050376Z"}
scraper-1      | INFO:     127.0.0.1:35058 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "toolsforhumanity", "program_id": "dd2d06f9-ccf7-46d0-96c1-0c59ff761cff", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:46.910054Z"}
scraper-1      | {"handle": "alshaya", "program_id": "54126f82-aad1-4308-a294-a1c4c68e6895", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:49.908183Z"}
scraper-1      | {"handle": "visa", "program_id": "7cc8dbc1-2c0c-4278-aa4d-2c965844b39a", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:52.498001Z"}
scraper-1      | INFO:     172.18.0.8:47644 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | {"handle": "aboitizpower_corporation", "program_id": "eff772b5-1531-49d6-a30a-c33089f5b855", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:54.507642Z"}
scraper-1      | INFO:     172.18.0.12:49542 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:38882 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "roke_vdp", "program_id": "e602eef3-5357-4745-87fe-05add1e3e6b5", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:56.488548Z"}
scraper-1      | {"handle": "oaknorth_bank", "program_id": "dd2c2e91-74e3-4bb2-9223-b86f7cc519ef", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:45:59.628844Z"}
scraper-1      | {"handle": "aven_response", "program_id": "3f8347c3-225c-4302-bfeb-0c2747932e9c", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:01.460624Z"}
scraper-1      | {"handle": "bykea", "program_id": "b98dee25-9890-4ca8-a061-70496ce904d3", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:03.386873Z"}
scraper-1      | INFO:     172.18.0.12:42144 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:49344 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "aon", "program_id": "2137586b-b008-415d-85f2-23ff587d6800", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:07.082569Z"}
scraper-1      | INFO:     172.18.0.8:44364 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | {"handle": "lightspark_bbp", "program_id": "23619d41-3791-45cf-aea9-c28b78bfc447", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:08.938680Z"}
scraper-1      | {"handle": "fireblocks_mpc", "program_id": "bb3562cb-1a91-4c5c-a84f-e034371ccec1", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:10.781540Z"}
scraper-1      | {"handle": "leather_wallet", "program_id": "b9cb60a6-a627-4fb4-ad3b-a715875db188", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:12.630444Z"}
scraper-1      | {"handle": "inditex", "program_id": "09f3fdec-3981-4d5a-b9c3-cc61f261a945", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:14.525791Z"}
scraper-1      | INFO:     172.18.0.12:47438 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "trip_com", "program_id": "341e7a8c-ab28-40b9-ac4c-5246511b7108", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:16.466116Z"}
scraper-1      | INFO:     127.0.0.1:49956 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "transunion", "program_id": "0ba9fcc8-d483-4836-93bc-b0891f6d88f7", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:19.364133Z"}
scraper-1      | {"handle": "bybit_fintech", "program_id": "ee6bab54-b009-4131-8230-5dd43cdaa4de", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:21.192236Z"}
scraper-1      | {"handle": "vectra_ai_vdp", "program_id": "1c0232d6-538c-421a-b8a3-6a3cfb29e96c", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:23.000318Z"}
scraper-1      | INFO:     172.18.0.8:59678 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | {"handle": "3cx", "program_id": "0f2faa42-8692-4df0-adbb-97a1b4f880aa", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:24.844653Z"}
scraper-1      | INFO:     172.18.0.12:35678 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "aeromexico_vdp", "program_id": "9401c467-e244-448a-9d7b-f75e210f1c70", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:26.665810Z"}
scraper-1      | INFO:     127.0.0.1:55844 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "audible", "program_id": "f27237a5-1ba9-4ad8-b5bb-a0442edab0ed", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:28.952618Z"}
scraper-1      | {"handle": "privy-bbp", "program_id": "197acc8b-6050-49a0-9980-eb024c618651", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:30.897848Z"}
scraper-1      | {"handle": "23andme_bbp", "program_id": "c1f6492b-87f2-418c-ad79-d95ea9fc2476", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:32.996928Z"}
scraper-1      | {"handle": "temu", "program_id": "f7fddd77-c199-4e78-83bd-10ee375e1216", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:34.941872Z"}
scraper-1      | INFO:     172.18.0.12:45262 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "dailypay_vdp", "program_id": "ee23e009-2cc0-4725-9026-e58e0bf6ffa4", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:36.804048Z"}
scraper-1      | INFO:     127.0.0.1:50052 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.18.0.8:51284 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | {"handle": "banco_bmg", "program_id": "bafe79e1-1f81-4d42-9483-68b03c05d0b6", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:40.057454Z"}
scraper-1      | {"handle": "netflix", "program_id": "2e7e3f5d-8ada-400f-9014-23eb70822861", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:42.958570Z"}
scraper-1      | {"handle": "wellhive", "program_id": "5a8d1d93-5da6-4157-91e0-a73e0a92c983", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:44.773561Z"}
scraper-1      | INFO:     172.18.0.12:36920 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     127.0.0.1:37184 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "corebridge_financial", "program_id": "e6fffff4-80a9-41c6-b62e-e2555ffa3015", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:47.340072Z"}
scraper-1      | {"handle": "unico_idtech", "program_id": "7a6cd785-d593-4fe6-8be7-2be081928cfc", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:49.193228Z"}
scraper-1      | {"handle": "interco_vdp", "program_id": "5e14c7c5-07a8-4e6c-9cd8-c7e71e10b8ed", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:51.074902Z"}
scraper-1      | {"handle": "chia_network", "program_id": "6c4ea566-26eb-4ca9-a6fb-ab38cb9c58e2", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:46:52.902437Z"}
reporter-worker-1  | [2026-03-25 03:46:46,168: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "2f2be9d2-6872-4f84-a38f-00f29e5f4720", "event_type": "scan.completed", "scan_id": "aa869b2a-7992-4217-9225-88d7157b3642", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T03:46:46.168060Z"}
reporter-worker-1  | [2026-03-25 03:46:46,168: WARNING/MainProcess] {"scan_id": "aa869b2a-7992-4217-9225-88d7157b3642", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T03:46:46.168910Z"}
reporter-worker-1  | [2026-03-25 03:46:46,169: WARNING/MainProcess] {"scan_id": "aa869b2a-7992-4217-9225-88d7157b3642", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-25T03:46:46.169022Z"}
core-worker-1      | [2026-03-25 03:45:16,515: INFO/MainProcess] Task core_engine.scan_task[c8045949-f0a5-48dc-8eee-e0dc0206ef97] received
core-worker-1      | [2026-03-25 03:45:16,520: WARNING/ForkPoolWorker-2] {"program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "event_type": "program.scraped", "event": "Scan task received", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:45:16.519919Z"}
core-worker-1      | [2026-03-25 03:45:16,629: WARNING/ForkPoolWorker-2] {"pool_size": 10, "max_overflow": 20, "event": "db_initialized", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:45:16.629570Z"}
core-worker-1      | [2026-03-25 03:45:16,630: WARNING/ForkPoolWorker-2] {"endpoint": "minio:9000", "secure": false, "event": "minio_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:45:16.630562Z"}
core-worker-1      | [2026-03-25 03:45:16,692: WARNING/ForkPoolWorker-2] {"scan_id": "aa869b2a-7992-4217-9225-88d7157b3642", "event": "Resuming existing scan", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:45:16.691931Z"}
core-worker-1      | [2026-03-25 03:45:16,719: INFO/ForkPoolWorker-2] HTTP Request: GET http://scraper:8001/api/v1/
... [truncated]

STDERR:
<empty>
```

### Command: docker compose logs reporter-worker (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env logs --no-color --since 2026-03-25T03:45:04Z --tail 300 reporter-worker`

```text
STDOUT:
reporter-worker-1  | [2026-03-25 03:46:46,168: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "2f2be9d2-6872-4f84-a38f-00f29e5f4720", "event_type": "scan.completed", "scan_id": "aa869b2a-7992-4217-9225-88d7157b3642", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T03:46:46.168060Z"}
reporter-worker-1  | [2026-03-25 03:46:46,168: WARNING/MainProcess] {"scan_id": "aa869b2a-7992-4217-9225-88d7157b3642", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T03:46:46.168910Z"}
reporter-worker-1  | [2026-03-25 03:46:46,169: WARNING/MainProcess] {"scan_id": "aa869b2a-7992-4217-9225-88d7157b3642", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-25T03:46:46.169022Z"}


STDERR:
<empty>
```

## Observed Gaps in Current Implementation
- Reporter worker currently validates `report.jobs` envelopes only.
- Specialist workers are queue listeners; deeper stages land in later milestones.
- This report reflects what ran in this test session, not aspirational docs.
