# AttackBot End-to-End Findings Report

- Generated at: `2026-03-24T09:31:25.495110+00:00`
- Report file: `E2E_SYSTEM_FINDINGS.md`
- Project root: `C:\Users\Home\Desktop\Projects\Attackbot_v1`
- Test outcome: `completed`

## Requested Mode
- Full end-to-end execution attempted against current M3 stack.
- All feature flags were set to `true` in scan start payload.
- Live-mode policy: no seeded/dummy fallback for primary scan.
- Program selection override active via `E2E_PINNED_PROGRAM_HANDLE` / `E2E_PINNED_PROGRAM_ID`.

## Execution Steps
1. 2026-03-24T09:24:46.471516+00:00 | Starting end-to-end system trace test
1. 2026-03-24T09:24:46.471770+00:00 | .env present (loaded 0 missing keys into process env)
1. 2026-03-24T09:24:47.143698+00:00 | Bringing up stack with docker compose up -d
1. 2026-03-24T09:24:51.808276+00:00 | Health probe scraper: status_code=200
1. 2026-03-24T09:24:52.158217+00:00 | Health probe core-engine: status_code=200
1. 2026-03-24T09:25:24.844607+00:00 | Health probe reporter: status_code=None
1. 2026-03-24T09:25:57.358428+00:00 | Health probe attack-graph-engine: status_code=None
1. 2026-03-24T09:25:57.903594+00:00 | Health probe api-gateway: status_code=200
1. 2026-03-24T09:25:58.820238+00:00 | Connected to database backend=docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
1. 2026-03-24T09:25:58.820254+00:00 | Pinned program selector configured: E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'
1. 2026-03-24T09:25:58.820257+00:00 | HackerOne credentials detected; triggering live scraper sync
1. 2026-03-24T09:29:59.164363+00:00 | Scraper trigger request failed; continuing with current live program inventory. error=ReadTimeout: 
1. 2026-03-24T09:30:21.099223+00:00 | Selected live HackerOne program for scan: 6e7f4e62-7a0f-400b-a9da-398c648161cb (weblate) via policy=pinned_program_handle
1. 2026-03-24T09:30:22.351312+00:00 | Queue purge pre-check scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-24T09:30:23.419957+00:00 | Queue purge attempt #1 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-24T09:30:23.752976+00:00 | Queue purge settle window scan.jobs: settled_unacked=True ready=0 unacked=0
1. 2026-03-24T09:30:24.812231+00:00 | Queue purge attempt #2 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-24T09:30:24.812249+00:00 | Waiting for queue baseline before triggering scan: queue=scan.jobs ready=0 unacked=0 timeout=60s
1. 2026-03-24T09:30:25.156940+00:00 | Queue baseline poll scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-24T09:30:25.156968+00:00 | Queue baseline reached: scan.jobs ready=0 unacked=0
1. 2026-03-24T09:30:25.156973+00:00 | Triggering core scan with all feature flags enabled
1. 2026-03-24T09:30:26.290377+00:00 | Scan status transition observed: running
1. 2026-03-24T09:31:19.129648+00:00 | Scan status transition observed: completed
1. 2026-03-24T09:31:19.129674+00:00 | Terminal scan status reached: completed

## Runtime Context
- DB connection backend: `docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit`
- Live HackerOne mode: `True`
- Program source: `hackerone_live_pinned`
- Program selection policy: `pinned_program_handle`
- Pinned program handle override: `weblate`
- Pinned program ID override: `None`
- Program ID: `6e7f4e62-7a0f-400b-a9da-398c648161cb`
- Program handle: `weblate`
- Scan ID: `19f8436a-990c-43a6-ab42-5761dcb704ce`
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
  "error": "ReadTimeout: ",
  "payload": null,
  "status_code": null
}
```

## Program Selection Audit
| program_id | handle | name | platform | is_active | valid_in_scope_count | selected | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
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
| 2a1fbf25-dd35-4918-a7a7-521f34137581 | gocd | GoCD | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| f253c099-7fe8-4bae-bc54-6b922ae8eced | acronis | Acronis | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| 40eaf863-885c-46c5-88b4-34c9bd4c1e96 | secnews | SecNews | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 6e5b555e-7386-43d7-bfa1-3d1d129bd3d1 | line | LY Corporation | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 7d37e692-1082-4ad2-a2cf-2d05a05df33d | pyca | Python Cryptographic Authority | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 2ac6e7e1-9545-4ee2-a09b-b3bef9b52ee8 | nextcloud | Nextcloud | hackerone | True | 95 | False | not selected: run pinned to explicit program selector(s) |
| d29ab0ae-bce5-41ce-84a4-d1823d7281a3 | files | Files.com | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 1fe2edf8-7ac7-420a-a07b-ce8db808418f | pushwoosh | Pushwoosh | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| fadf85ac-c30e-4a1d-a4de-ecc857e740f5 | exness | EXNESS | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 0dde3d67-1f05-43ef-a505-22a8e70edd9b | fantasytote | FantasyTote | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| ae40ec6b-f76f-4f17-88ed-f9d87a3461a8 | owox | OWOX, Inc. | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 8ff46e63-5960-45c1-be30-b37af4904cc6 | drugs_com | Drugs.com | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 121abbf4-b34a-4a8d-a1da-662b90e6ffef | helium | Helium | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 80694604-4951-4a76-9dff-f25a2bb468c2 | websummit | WebSummit | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 5aed26be-cabd-4b73-95b0-a2569d996ba3 | duckduckgo | DuckDuckGo | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 583455ff-c1b2-4eed-a1bf-d1ec20492b09 | aspen | Aspen | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| c4e3e80a-d235-4cf3-a0d5-c6f032179a06 | dyson | Dyson | hackerone | True | 66 | False | not selected: run pinned to explicit program selector(s) |
| dcd34f34-a383-4ed8-8b14-12e8357f6072 | phpbb | phpBB | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| ccf90cb2-df6b-43d0-b3e5-72291c7268a5 | mainwp | MainWP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 832b2c1d-099a-419e-be45-bcd32129ae73 | mariadb | MariaDB | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| ec94cf71-73f6-425e-9576-5d1c8f67902f | bitaccess | bitaccess | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| ddc031cb-3865-4198-ae24-ca5ccf350ffe | kiwicom | Kiwi.com | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 8d58b937-448e-43ec-80bd-05211484a360 | paragonie | Paragon Initiative Enterprises | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 8db2246d-79ad-4c7e-8241-37461c12d93d | rubygems | RubyGems | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 6367e662-d6f0-4ae1-a425-f4ee7a43be18 | flipkart | Flipkart | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 342a508b-e64a-4f41-bd2e-5ecce6b15494 | hyatt | Hyatt Hotels | hackerone | True | 65 | False | not selected: run pinned to explicit program selector(s) |
| c5f253f9-94a4-4de0-9930-7d603b82ec8e | monero | Monero | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d11d188b-8cea-4dd2-9971-eb812734088c | ruby | Ruby | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 453871e6-d86e-4120-8a60-c9607570def0 | gm | General Motors | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 2b26ba48-6c1c-4594-9b7a-8981709686bd | bime | Bime | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 8f552a06-03cf-4b0f-9e2f-e77ed2ec0a28 | fetlife | FetLife | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 9e184aa0-aaac-4d5e-820e-c61ca807338d | msd | Merck & Co., Inc., Rahway, NJ, USA | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 8d19aff3-9006-48b3-a3a9-c195a45bbf7f | goldmansachs | Goldman Sachs | hackerone | True | 46 | False | not selected: run pinned to explicit program selector(s) |
| 36c39c28-c70e-4f88-b10d-40a6a23b260b | bestbuy | Best Buy | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 09a6b4f1-e5bd-4372-9cf9-236569f25364 | equifax | Equifax-vdp | hackerone | True | 282 | False | not selected: run pinned to explicit program selector(s) |
| 78d28a09-3206-440f-ac41-c7192dfede1d | codeigniter | CodeIgniter | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 0cf28e2b-e922-4462-921a-0afdfe7e3da5 | quora | Quora | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 89eaf166-3a86-4ec8-a62d-10163ad98be6 | homebargains | Home Bargains | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 7a833178-8c7a-49bd-b4f6-7c1fe8dbf0fb | versioncake | Version Cake | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 61ba22ad-82ea-4d37-a791-1f3fdb0ac469 | owncloud | ownCloud | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| 714323f0-bb8d-427e-978e-055d4ab9b57e | kiwi-ki | KIWI.KI GmbH | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 0a48369f-5e02-4f58-bf66-4880ae248b36 | wealthsimple | Wealthsimple | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 973be14f-fbdc-4bce-80a6-3d274cff2e17 | eternal | Eternal | hackerone | True | 34 | False | not selected: run pinned to explicit program selector(s) |
| 34c986eb-fd42-41f9-94eb-69d6630315a4 | deriv | Deriv.com | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 5e9ddce3-3858-47db-9c8d-064009f00057 | unikrn | Unikrn | hackerone | True | 25 | False | not selected: run pinned to explicit program selector(s) |
| 8f8a287e-76c0-44e9-8fdd-3501e195483c | revive_adserver | Revive Adserver | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2bdf95ea-e4ac-4085-912d-68bbc6f00278 | clear | CLEAR | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 10679ed4-ff1c-4dc7-8886-97c8fe77ab04 | libsass | LibSass | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 66e52caa-f8e2-4668-985d-e7f5e84d48ff | rockstargames | Rockstar Games | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| b519e472-f45e-4bb1-9688-bbffc45868f7 | ibm | IBM | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 0a5b5694-e8a5-4771-bbc5-196fe845dea3 | spotify | Spotify | hackerone | True | 43 | False | not selected: run pinned to explicit program selector(s) |
| 21892d03-04b2-41db-8a9b-cc412cd50502 | starbucks | Starbucks | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| c3f8c7b4-f3bb-4803-805b-e288658e01a6 | trellix | Trellix | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| f12d95d6-178e-402c-a095-00a05621e2f4 | badoo | Badoo | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d77becc1-cac7-4a12-8577-45aa74dd52c0 | matomo | Matomo | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| c6c5b27a-d2ec-464f-ac90-fc3e4af2816f | paypal | PayPal | hackerone | True | 41 | False | not selected: run pinned to explicit program selector(s) |
| 3e9ff314-3b42-46ac-8693-8e3c02cfd99f | github | GitHub | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| 96ec7d68-f3e1-4669-9167-cdfac2158f99 | torproject | Tor | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 6c2d8461-4676-4916-96b7-8ad298fc21a2 | nokogiri | Nokogiri | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 6579848c-bebc-4ac1-89dc-3d47b82cd3c7 | goodrx | GoodRx | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 8c10af19-0722-4525-af9a-eb08175586fa | grab | Grab | hackerone | True | 33 | False | not selected: run pinned to explicit program selector(s) |
| 1957c1be-09db-417f-9ed3-831a50175a10 | legalrobot | Legal Robot | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 5bc98e9c-4bb8-4391-84a8-7a4eef492593 | udemy | Udemy | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 13637e1a-8d24-447a-873b-6ded9206cca2 | coursera | Coursera | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| ee6f99bc-dedb-4fb2-8147-fd90c89a11e7 | ips | Invision Power Services, Inc. | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 409e4cb7-b730-4e1b-8ffd-92d84f74c1cf | shopify | Shopify | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 4a94343f-7dd2-401b-862f-1709a2b559ab | mapbox | Mapbox | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 84bd16fe-721e-4ed0-8339-36a261d94383 | moneybird | Moneybird | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| e12e958b-85a7-484e-9b26-19c932f1cae2 | kayak | KAYAK | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 00f3dbd2-9c65-42ad-919d-4948a12f7ae6 | airbnb | Airbnb | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| d6f2c4fa-5150-4955-ba9b-769132a5da63 | bookingcom | Booking.com | hackerone | True | 49 | False | not selected: run pinned to explicit program selector(s) |
| 628003b4-809d-4e8a-98fe-e21c5b6dbddd | airtable | Airtable | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| f23f4c32-2f6a-4cf2-a33a-972877b5b8f4 | ui | Ubiquiti Inc. | hackerone | True | 50 | False | not selected: run pinned to explicit program selector(s) |
| 8996a5a8-e366-4f31-8189-a542cc4dc55f | imgur | Imgur | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 7c83cc3c-6b87-48e3-9f54-8dd63c4ab1b9 | mobilevikings | Mobile Vikings | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 9b86fc98-6b9f-4bc3-9895-58209b25d650 | scopely | Scopely | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| 19795eb5-a5fa-4555-a143-bc4475ab9438 | yelp | Yelp | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 28ab7677-7aef-4a21-8931-7b990b6c380d | snapchat | Snapchat | hackerone | True | 40 | False | not selected: run pinned to explicit program selector(s) |
| cf468475-a469-4216-89a2-821efbbee072 | informatica | Informatica | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| e0352128-ba11-4f49-a539-7d7fade24f2f | algolia | Algolia | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 562d6c0d-bb44-4d60-a872-91c71f3ecb9b | glasswire | GlassWire | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 5a068198-9603-4e8f-ad24-d27c8d0f913e | wordpoints | WordPoints | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 9dea39a4-5914-4abc-a37b-4bc3d33c56c3 | adobe | Adobe | hackerone | True | 69 | False | not selected: run pinned to explicit program selector(s) |
| 0eacc7f2-7bb6-4c32-9ec4-e5564b601401 | uber | Uber | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 6429b578-08dd-46a5-879b-5ea589414086 | greenhouse | Greenhouse.io | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 36ee672f-0ed1-4f44-8c79-f11d382684d6 | cert | CERT/CC | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d1ae8e41-34c1-4ec6-a49a-5a2becc1cf74 | wp-api | WP API | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 8af8d718-7660-4939-8b59-71fa14a990b5 | digitalsellz | DigitalSellz | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 8ba18a83-aea5-48e4-9c23-d4115fb20ec0 | expressionengine | ExpressionEngine | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 604fdef1-b87c-42bd-8ff0-bd356b90c33b | gitlab | GitLab | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 19a5b952-f903-49dd-af8e-03dc41d370d8 | formassembly | FormAssembly | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 727392f4-5800-4d02-8001-060d86dd7fa2 | urbandictionary | Urban Dictionary | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| ecaa3fbd-da8b-4744-ba37-9032be4cacbe | glassdoor | Glassdoor | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 4839928b-dce4-44bc-8ba9-243a6e4661a6 | stopthehacker | StopTheHacker | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 17a0adc2-e6bf-423d-99eb-1066b33d717b | iandunn-projects | Ian Dunn | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 71db3dcc-e655-4c12-9941-49fe36adcc4b | irccloud | IRCCloud | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 0e9c20e6-0ffb-4d53-942e-04d6e1b1beb6 | khanacademy | Khan Academy | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 7d3f0748-6711-4717-b192-e21188bcdf4c | att | AT&T | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 9c592c88-39e6-4926-a91f-030a1e84464b | automattic | Automattic | hackerone | True | 29 | False | not selected: run pinned to explicit program selector(s) |
| 1fd4513c-5c44-46c9-a853-f3e2fc386ffe | coinbase | Coinbase | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 58f7fdfe-f838-4243-8258-c1aded033ef6 | publitas | Publitas | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 43c20a1e-1d42-426d-9275-f85b866291cd | tinder | Tinder | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| a3db4cad-2fd4-4ab7-914d-16ec9af932ca | slack | Slack | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| c5628097-f805-4ec8-8d01-1e11733f5c91 | basecamp | Basecamp | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 193137e0-c3ca-452b-b74a-6bc664965602 | x | X / xAI | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| 89d7f41d-f3f4-4baf-a352-50832ef4cc67 | concretecms | Concrete CMS | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| fba2d891-8b22-4d14-94ac-fd99c79dae82 | priceline | Priceline | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 6debe663-4a98-472a-b2db-6459e3ea8753 | linkedin | LinkedIn | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| d49aede0-7a07-4e82-9038-4cc473a47ca3 | vimeo | Vimeo | hackerone | True | 36 | False | not selected: run pinned to explicit program selector(s) |
| d9d22c1e-a9f9-4409-b538-1c5cbbc3635e | wordpress | WordPress | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| e62d163e-fa1e-4f62-8ad0-346b122784ce | mavenlink | Mavenlink | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 32b2ebf8-c75e-49d9-a4fb-f241bca2c0af | cloudflare | Cloudflare Public Bug Bounty | hackerone | True | 53 | False | not selected: run pinned to explicit program selector(s) |
| c10b5c25-8200-4b76-855c-793a48cc877b | django | Django | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| c0767679-05a1-465e-a631-a41be8edaba2 | rails | Ruby on Rails | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 0cebaec4-4cea-47db-a3ef-47641c40eac7 | phabricator | Phabricator | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 6c84c51b-bfb0-470d-9a66-9a7dedf40f52 | security | HackerOne | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
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
{
  "completed_at": "2026-03-24T09:31:18.925017+00:00",
  "created_at": "2026-03-24T09:30:25.845353+00:00",
  "error_detail": null,
  "finding_count": 0,
  "partial_detail": null,
  "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb",
  "retry_count": 0,
  "scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce",
  "severity_breakdown": "{\"low\": 0, \"high\": 0, \"info\": 0, \"medium\": 0, \"critical\": 0}",
  "started_at": "2026-03-24T09:30:25.845353+00:00",
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
| 1.0 | asset_discovery | completed | 2026-03-24T09:30:25.967195+00:00 | 2026-03-24T09:31:18.919990+00:00 |  |
| 10.1 | report_handoff | completed | 2026-03-24T09:31:18.927163+00:00 | 2026-03-24T09:31:18.940570+00:00 |  |

### Artifact Counts
```json
{
  "assets_count": 0,
  "endpoints_count": 0,
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
{
  "payload": {
    "completed_at": "2026-03-24T09:31:18.925017+00:00",
    "error_detail": null,
    "finding_count": 0,
    "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb",
    "scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce",
    "severity_breakdown": {
      "critical": 0,
      "high": 0,
      "info": 0,
      "low": 0,
      "medium": 0
    },
    "started_at": "2026-03-24T09:30:25.845353+00:00",
    "status": "completed"
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/scans/19f8436a-990c-43a6-ab42-5761dcb704ce"
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
  "url": "http://localhost:8002/api/v1/scans/19f8436a-990c-43a6-ab42-5761dcb704ce/findings"
}
```

## Forced Deep Trace (Downstream Replay)
_Not executed._

## Process Evidence
### Command: docker compose up -d
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env up -d`

```text
STDOUT:
<empty>

STDERR:
 Container attackbot-neo4j-1  Running
 Container attackbot-minio-1  Running
 Container attackbot-rabbitmq-1  Running
 Container attackbot-postgres-1  Running
 Container attackbot-redis-1  Running
 Container attackbot-vault-1  Running
 Container attackbot-prometheus-1  Running
 Container attackbot-loki-1  Running
 Container attackbot-grafana-1  Running
 Container attackbot-attack-graph-engine-1  Running
 Container attackbot-scraper-1  Running
 Container attackbot-reporter-1  Running
 Container attackbot-core-engine-1  Running
 Container attackbot-reporter-worker-1  Running
 Container attackbot-ai-analysis-worker-1  Running
 Container attackbot-api-gateway-1  Running
 Container attackbot-js-analysis-worker-1  Running
 Container attackbot-api-fuzzer-worker-1  Running
 Container attackbot-browser-worker-1  Running
 Container attackbot-scenario-runner-1  Running
 Container attackbot-exploit-verifier-1  Running
 Container attackbot-core-worker-1  Running
 Container attackbot-tempo-1  Starting
 Container attackbot-minio-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-vault-1  Waiting
 Container attackbot-tempo-1  Started
 Container attackbot-postgres-1  Healthy
 Container attackbot-vault-1  Healthy
 Container attackbot-migrate-1  Starting
 Container attackbot-vault-init-1  Starting
 Container attackbot-minio-1  Healthy
 Container attackbot-minio-init-1  Starting
 Container attackbot-minio-init-1  Started
 Container attackbot-vault-init-1  Started
 Container attackbot-migrate-1  Started
 Container attackbot-neo4j-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-neo4j-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-minio-init-1  Exited
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-postgres-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-minio-init-1  Exited
 Container attackbot-redis-1  Healthy
 Container attackbot-postgres-1  Healthy
 Container attackbot-postgres-1  Healthy
 Container attackbot-minio-init-1  Exited
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-migrate-1  Exited
 Container attackbot-migrate-1  Exited
 Container attackbot-reporter-1  Waiting
 Container attackbot-migrate-1  Exited
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-migrate-1  Exited
 Container attackbot-core-engine-1  Waiting
 Container attackbot-reporter-1  Waiting
 Container attackbot-attack-graph-engine-1  Waiting
 Container attackbot-scraper-1  Waiting
 Container attackbot-reporter-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-scraper-1  Healthy
 Container attackbot-attack-graph-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-reporter-1  Healthy
 Container attackbot-core-engine-1  Healthy

```

### Command: docker compose ps
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env ps`

```text
STDOUT:
NAME                              IMAGE                           COMMAND                  SERVICE               CREATED       STATUS                          PORTS
attackbot-ai-analysis-worker-1    attackbot-ai-analysis-worker    "celery -A backend.sâ€¦"   ai-analysis-worker    3 hours ago   Up 3 hours                      
attackbot-api-fuzzer-worker-1     attackbot-api-fuzzer-worker     "celery -A backend.sâ€¦"   api-fuzzer-worker     3 hours ago   Up 3 hours                      
attackbot-api-gateway-1           attackbot-api-gateway           "uvicorn backend.serâ€¦"   api-gateway           3 hours ago   Up 3 hours (unhealthy)          0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
attackbot-attack-graph-engine-1   attackbot-attack-graph-engine   "uvicorn backend.serâ€¦"   attack-graph-engine   3 hours ago   Up 3 hours (healthy)            8006/tcp
attackbot-browser-worker-1        attackbot-browser-worker        "celery -A backend.sâ€¦"   browser-worker        3 hours ago   Up 3 hours                      
attackbot-core-engine-1           attackbot-core-engine           "uvicorn backend.serâ€¦"   core-engine           2 hours ago   Up 2 hours (healthy)            0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
attackbot-core-worker-1           attackbot-core-worker           "celery -A backend.sâ€¦"   core-worker           2 hours ago   Up 2 hours                      8002/tcp
attackbot-exploit-verifier-1      attackbot-exploit-verifier      "celery -A backend.sâ€¦"   exploit-verifier      3 hours ago   Up 3 hours                      
attackbot-grafana-1               grafana/grafana:latest          "/run.sh"                grafana               3 hours ago   Up 3 hours                      0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
attackbot-js-analysis-worker-1    attackbot-js-analysis-worker    "celery -A backend.sâ€¦"   js-analysis-worker    3 hours ago   Up 3 hours                      
attackbot-loki-1                  grafana/loki:latest             "/usr/bin/loki -confâ€¦"   loki                  3 hours ago   Up 3 hours                      3100/tcp
attackbot-minio-1                 minio/minio                     "/usr/bin/docker-entâ€¦"   minio                 3 hours ago   Up 3 hours (healthy)            9000/tcp
attackbot-neo4j-1                 neo4j:5-community               "tini -g -- /startupâ€¦"   neo4j                 3 hours ago   Up 3 hours (healthy)            7473-7474/tcp, 7687/tcp
attackbot-postgres-1              postgres:16                     "docker-entrypoint.sâ€¦"   postgres              3 hours ago   Up 3 hours (healthy)            0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
attackbot-prometheus-1            prom/prometheus:latest          "/bin/prometheus --câ€¦"   prometheus            3 hours ago   Up 3 hours                      9090/tcp
attackbot-rabbitmq-1              rabbitmq:3-management           "docker-entrypoint.sâ€¦"   rabbitmq              3 hours ago   Up 3 hours (healthy)            0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
attackbot-redis-1                 redis:7-alpine                  "docker-entrypoint.sâ€¦"   redis                 3 hours ago   Up 3 hours (healthy)            6379/tcp
attackbot-reporter-1              attackbot-reporter              "uvicorn backend.serâ€¦"   reporter              3 hours ago   Up 3 hours (healthy)            8003/tcp
attackbot-reporter-worker-1       attackbot-reporter-worker       "celery -A backend.sâ€¦"   reporter-worker       3 hours ago   Up 3 hours                      8003/tcp
attackbot-scenario-runner-1       attackbot-scenario-runner       "celery -A backend.sâ€¦"   scenario-runner       3 hours ago   Up 3 hours                      
attackbot-scraper-1               attackbot-scraper               "uvicorn backend.serâ€¦"   scraper               2 hours ago   Up 2 hours (healthy)            0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
attackbot-tempo-1                 grafana/tempo:latest            "/tempo"                 tempo                 3 hours ago   Restarting (1) 31 seconds ago   
attackbot-vault-1                 hashicorp/vault:1.15            "docker-entrypoint.sâ€¦"   vault                 3 hours ago   Up 3 hours (healthy)            8200/tcp


STDERR:
<empty>
```

### Command: docker compose logs (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env logs --no-color --since 2026-03-24T09:30:25Z --tail 300 scraper core-engine core-worker reporter reporter-worker`

```text
STDOUT:
reporter-worker-1  | [2026-03-24 09:31:18,953: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "79660c7a-e531-4a26-99e4-1aa301a7d54c", "event_type": "scan.completed", "scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T09:31:18.949711Z"}
reporter-worker-1  | [2026-03-24 09:31:18,958: WARNING/MainProcess] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T09:31:18.958310Z"}
reporter-worker-1  | [2026-03-24 09:31:18,958: WARNING/MainProcess] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-24T09:31:18.958675Z"}
reporter-1         | INFO:     127.0.0.1:47382 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:57258 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:41030 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:47004 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:47462 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:60350 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:58894 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:46994 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:44598 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:45430 - "GET /metrics HTTP/1.1" 200 OK
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/programs/6e7f4e62-7a0f-400b-a9da-398c648161cb "HTTP/1.1 200 OK"
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/programs/6e7f4e62-7a0f-400b-a9da-398c648161cb/scope "HTTP/1.1 200 OK"
core-engine-1      | INFO:     172.20.0.1:59322 - "POST /api/v1/scans/start HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:54952 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:58410 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:39288 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:54216 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:48108 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:55798 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:60552 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:44764 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:48716 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | INFO:     172.20.0.1:44176 - "GET /api/v1/scans/19f8436a-990c-43a6-ab42-5761dcb704ce HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.1:44186 - "GET /api/v1/scans/19f8436a-990c-43a6-ab42-5761dcb704ce/findings HTTP/1.1" 200 OK
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:54350 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.1:44198 - "GET /api/v1/queue/dlq/inspect HTTP/1.1" 200 OK
core-worker-1      | [2026-03-24 09:30:25,561: INFO/MainProcess] Task core_engine.scan_task[53b4750c-cf41-48c6-85fe-aaf4f5c9bb00] received
core-worker-1      | [2026-03-24 09:30:25,620: WARNING/ForkPoolWorker-2] {"program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "event_type": "program.scraped", "event": "Scan task received", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:25.614714Z"}
core-worker-1      | [2026-03-24 09:30:25,674: WARNING/ForkPoolWorker-2] {"pool_size": 10, "max_overflow": 20, "event": "db_initialized", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:25.674548Z"}
core-worker-1      | [2026-03-24 09:30:25,682: WARNING/ForkPoolWorker-2] {"endpoint": "minio:9000", "secure": false, "event": "minio_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:25.682744Z"}
core-worker-1      | [2026-03-24 09:30:25,858: WARNING/ForkPoolWorker-2] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "event": "Scan created", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:25.857974Z"}
core-worker-1      | [2026-03-24 09:30:25,927: INFO/ForkPoolWorker-2] HTTP Request: GET http://scraper:8001/api/v1/programs/6e7f4e62-7a0f-400b-a9da-398c648161cb/scope "HTTP/1.1 200 OK"
core-worker-1      | [2026-03-24 09:30:25,965: WARNING/ForkPoolWorker-2] {"url": "amqp://attackbot:attackbot@rabbitmq:5672/", "event": "queue_publisher_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:25.965055Z"}
core-worker-1      | [2026-03-24 09:30:25,965: WARNING/ForkPoolWorker-2] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "event": "Stage 0: Scope filter", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:25.965699Z"}
core-worker-1      | [2026-03-24 09:30:25,967: WARNING/ForkPoolWorker-2] {"in_scope_count": 6, "out_of_scope_count": 2, "event": "ScopeFilter built", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:25.966984Z"}
core-worker-1      | [2026-03-24 09:30:25,970: WARNING/ForkPoolWorker-2] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "skipped_counts": {"url_host_not_domain_led": 5}, "event": "asset_discovery_seed_scope_skipped", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:25.970044Z"}
core-worker-1      | [2026-03-24 09:30:25,974: WARNING/ForkPoolWorker-2] {"args": "subfinder", "timeout": 180, "event": "Running subfinder[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:25.974214Z"}
core-worker-1      | [2026-03-24 09:30:56,838: WARNING/ForkPoolWorker-2] {"domain": "hosted.weblate.org", "event": "alterx_skipped_no_subfinder_results", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:56.838562Z"}
core-worker-1      | [2026-03-24 09:30:56,839: WARNING/ForkPoolWorker-2] {"args": "dnsx", "timeout": 270, "event": "Running dnsx[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:56.839448Z"}
core-worker-1      | [2026-03-24 09:30:57,717: WARNING/ForkPoolWorker-2] {"args": "httpx", "timeout": 180, "event": "Running httpx[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:30:57.717247Z"}
core-worker-1      | [2026-03-24 09:31:18,916: WARNING/ForkPoolWorker-2] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "seed_domains": 1, "assets_found": 0, "errors": 0, "event": "Stage 1 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:31:18.916284Z"}
core-worker-1      | [2026-03-24 09:31:18,923: WARNING/ForkPoolWorker-2] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "event": "No assets found \u2014 skipping Stages 2\u20136", "service": "core-worker", "level": "warning", "timestamp": "2026-03-24T09:31:18.923160Z"}
core-worker-1      | [2026-03-24 09:31:18,939: WARNING/ForkPoolWorker-2] {"queue": "report.jobs", "event_type": "scan.completed", "event_id": "79660c7a-e531-4a26-99e4-1aa301a7d54c", "event": "message_published", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:31:18.938935Z"}
core-worker-1      | [2026-03-24 09:31:18,942: WARNING/ForkPoolWorker-2] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "event": "Published scan.completed to report.jobs", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:31:18.942601Z"}
core-worker-1      | [2026-03-24 09:31:18,942: WARNING/ForkPoolWorker-2] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "findings_saved": 0, "status": "completed", "breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}, "event": "Stage 10 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:31:18.942931Z"}
core-worker-1      | [2026-03-24 09:31:18,945: WARNING/ForkPoolWorker-2] {"event": "queue_publisher_closed", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T09:31:18.945026Z"}
core-worker-1      | [2026-03-24 09:31:18,958: INFO/ForkPoolWorker-2] Task core_engine.scan_task[53b4750c-cf41-48c6-85fe-aaf4f5c9bb00] succeeded in 53.3603559309995s: None
scraper-1          | INFO:     172.20.0.13:33116 - "GET /api/v1/programs/6e7f4e62-7a0f-400b-a9da-398c648161cb HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.13:33116 - "GET /api/v1/programs/6e7f4e62-7a0f-400b-a9da-398c648161cb/scope HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.4:58810 - "GET /api/v1/programs/6e7f4e62-7a0f-400b-a9da-398c648161cb/scope HTTP/1.1" 200 OK
scraper-1          | {"handle": "parrot_sec", "program_id": "b973e214-6904-4a36-ae9b-a6b8779a88cf", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:25.963220Z"}
scraper-1          | {"handle": "bitwarden", "program_id": "a3e6da23-751a-460c-861f-883c63cee88b", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:27.735592Z"}
scraper-1          | {"handle": "omise", "program_id": "a8935f9c-e3fa-40e9-b117-92eaa2e83018", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:29.533600Z"}
scraper-1          | INFO:     127.0.0.1:36348 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "wink_jq3al", "program_id": "89a9fe01-6ad8-4116-8493-7c2a3d1c6c3b", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:31.742446Z"}
scraper-1          | INFO:     172.20.0.3:36252 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     172.20.0.13:50178 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "bumble", "program_id": "961b3766-6ddf-4c98-9e16-256aaf5495a6", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:33.746732Z"}
scraper-1          | {"handle": "infogram", "program_id": "9fceae7f-57e6-4f5f-be7f-d04776b1ab49", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:35.596834Z"}
scraper-1          | {"handle": "yoti", "program_id": "6d2e6c82-8418-42b3-af11-1a317eb3339a", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:37.525800Z"}
scraper-1          | {"handle": "wakatime", "program_id": "d64ed3f0-ecc7-4fb7-af7a-67aa5d19736c", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:39.335800Z"}
scraper-1          | INFO:     127.0.0.1:41738 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "delight_im", "program_id": "a4446391-c627-4259-a794-8fa987918a9b", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:41.627784Z"}
scraper-1          | INFO:     172.20.0.13:55096 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "malwarebytes", "program_id": "230e00ec-3fed-498b-b357-fcdd272a349a", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:43.514583Z"}
scraper-1          | {"handle": "upserve", "program_id": "b94274cf-e32d-4b08-93bf-7ee7a435c30f", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:45.387852Z"}
scraper-1          | INFO:     172.20.0.3:54174 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | {"handle": "hyperledger", "program_id": "0bb51995-bc1f-4b29-b1da-ce42c06ff51a", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:47.431928Z"}
scraper-1          | {"handle": "superhuman", "program_id": "bd68f803-bb66-4f2c-9b9b-a93833873809", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:49.125735Z"}
scraper-1          | INFO:     127.0.0.1:40854 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "usertesting", "program_id": "c607b815-fc86-49a0-8c23-d5526c4525ca", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:50.986568Z"}
scraper-1          | {"handle": "streak_com", "program_id": "e2693bfb-fb61-4085-98a4-30d88f3b6a74", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:53.504942Z"}
scraper-1          | INFO:     172.20.0.13:49826 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "kartpay", "program_id": "395a645f-8fda-485e-825f-1c6f3b5004d9", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:55.379345Z"}
scraper-1          | {"handle": "netlify", "program_id": "231cc23d-f8d4-464b-8b23-a476c6217869", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:57.119187Z"}
scraper-1          | {"handle": "nodejs", "program_id": "5eadcf25-0b60-4264-a403-3b2718eb9870", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:30:58.967485Z"}
scraper-1          | {"handle": "deconf_com", "program_id": "ff5f44f7-84b5-4075-8622-14fc430c7f98", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:00.657647Z"}
scraper-1          | INFO:     127.0.0.1:52460 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.3:34378 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | {"handle": "epicgames", "program_id": "12369ee1-fb66-4890-828d-037f5f878a61", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:03.282662Z"}
scraper-1          | INFO:     172.20.0.13:42356 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "valve", "program_id": "41411df5-20f1-4764-ba33-9b607eaefc0f", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:04.965760Z"}
scraper-1          | {"handle": "elastic", "program_id": "f6d29926-3daf-4514-92d6-b391e8f7d5d6", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:07.460606Z"}
scraper-1          | {"handle": "fig", "program_id": "99f5d538-ad7e-4e8c-bcf7-e75f91b3de8f", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:09.485759Z"}
scraper-1          | {"handle": "smule", "program_id": "b4db9ca5-b6d1-4624-ae33-51ddc7b8d8b5", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:11.251276Z"}
scraper-1          | INFO:     127.0.0.1:49508 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "bitmex", "program_id": "70c8bad9-b07b-4ae2-9546-a91700ddfd81", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:13.139182Z"}
scraper-1          | INFO:     172.20.0.13:53912 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "ed", "program_id": "354457aa-7dc4-426f-9315-fb5ad76a3a3e", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:14.731477Z"}
scraper-1          | {"handle": "jamieweb", "program_id": "99770bc0-4a69-41f6-82e3-760b3433da53", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:16.248309Z"}
scraper-1          | INFO:     172.20.0.3:35032 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | {"handle": "flutteruki", "program_id": "5f524a60-478c-4225-8eaa-341e694abf6c", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:19.467227Z"}
scraper-1          | INFO:     127.0.0.1:55892 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "databricks", "program_id": "60fafd88-f4a6-42a6-980b-64e189962fb3", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:22.853626Z"}
scraper-1          | INFO:     172.20.0.13:47012 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "cosmos", "program_id": "dda96618-8834-4cfc-babe-1dc5db15669d", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T09:31:24.504805Z"}


STDERR:
<empty>
```

### Command: docker compose logs reporter-worker (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env logs --no-color --since 2026-03-24T09:30:25Z --tail 300 reporter-worker`

```text
STDOUT:
reporter-worker-1  | [2026-03-24 09:31:18,953: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "79660c7a-e531-4a26-99e4-1aa301a7d54c", "event_type": "scan.completed", "scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T09:31:18.949711Z"}
reporter-worker-1  | [2026-03-24 09:31:18,958: WARNING/MainProcess] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T09:31:18.958310Z"}
reporter-worker-1  | [2026-03-24 09:31:18,958: WARNING/MainProcess] {"scan_id": "19f8436a-990c-43a6-ab42-5761dcb704ce", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-24T09:31:18.958675Z"}


STDERR:
<empty>
```

## Observed Gaps in Current Implementation
- Reporter worker currently validates `report.jobs` envelopes only.
- Specialist workers are queue listeners; deeper stages land in later milestones.
- This report reflects what ran in this test session, not aspirational docs.
