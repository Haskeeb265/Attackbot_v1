# AttackBot End-to-End Findings Report

- Generated at: `2026-03-24T13:15:54.113511+00:00`
- Report file: `E2E_SYSTEM_FINDINGS.md`
- Project root: `C:\Users\Home\Desktop\Projects\Attackbot_v1`
- Test outcome: `completed`

## Requested Mode
- Full end-to-end execution attempted against current M3 stack.
- All feature flags were set to `true` in scan start payload.
- Live-mode policy: no seeded/dummy fallback for primary scan.
- Program selection override active via `E2E_PINNED_PROGRAM_HANDLE` / `E2E_PINNED_PROGRAM_ID`.

## Execution Steps
1. 2026-03-24T12:57:34.331981+00:00 | Starting end-to-end system trace test
1. 2026-03-24T12:57:34.332223+00:00 | .env present (loaded 0 missing keys into process env)
1. 2026-03-24T12:57:35.378585+00:00 | Bringing up stack with docker compose up -d
1. 2026-03-24T12:57:39.871363+00:00 | Health probe scraper: status_code=200
1. 2026-03-24T12:57:40.354536+00:00 | Health probe core-engine: status_code=200
1. 2026-03-24T12:58:12.893838+00:00 | Health probe reporter: status_code=None
1. 2026-03-24T12:58:45.592380+00:00 | Health probe attack-graph-engine: status_code=None
1. 2026-03-24T12:58:46.156755+00:00 | Health probe api-gateway: status_code=200
1. 2026-03-24T12:58:47.001623+00:00 | Connected to database backend=docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
1. 2026-03-24T12:58:47.001641+00:00 | Pinned program selector configured: E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'
1. 2026-03-24T12:58:47.001645+00:00 | HackerOne credentials detected; triggering live scraper sync
1. 2026-03-24T12:59:47.344877+00:00 | Scraper trigger request failed; continuing with current live program inventory. error=ReadTimeout: 
1. 2026-03-24T13:04:20.265102+00:00 | Selected live HackerOne program for scan: 6e7f4e62-7a0f-400b-a9da-398c648161cb (weblate) via policy=pinned_program_handle
1. 2026-03-24T13:04:22.253957+00:00 | Queue purge pre-check scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-24T13:04:24.181393+00:00 | Queue purge attempt #1 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-24T13:04:24.746200+00:00 | Queue purge settle window scan.jobs: settled_unacked=True ready=0 unacked=0
1. 2026-03-24T13:04:26.316371+00:00 | Queue purge attempt #2 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-24T13:04:26.316394+00:00 | Waiting for queue baseline before triggering scan: queue=scan.jobs ready=0 unacked=0 timeout=60s
1. 2026-03-24T13:04:26.747752+00:00 | Queue baseline poll scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-24T13:04:26.747784+00:00 | Queue baseline reached: scan.jobs ready=0 unacked=0
1. 2026-03-24T13:04:26.747789+00:00 | Triggering core scan with all feature flags enabled
1. 2026-03-24T13:04:28.265423+00:00 | Scan status transition observed: running
1. 2026-03-24T13:15:46.642556+00:00 | Scan status transition observed: partial
1. 2026-03-24T13:15:46.642588+00:00 | Terminal scan status reached: partial

## Runtime Context
- DB connection backend: `docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit`
- Live HackerOne mode: `True`
- Program source: `hackerone_live_pinned`
- Program selection policy: `pinned_program_handle`
- Pinned program handle override: `weblate`
- Pinned program ID override: `None`
- Program ID: `6e7f4e62-7a0f-400b-a9da-398c648161cb`
- Program handle: `weblate`
- Scan ID: `063ae238-f4f8-414a-9fd6-7454bef1d335`
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
| 3f8353c6-4119-4d43-97ed-8e2c851ae903 | getyourguide_vdp | GetYourGuide VDP | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 3c2be4cd-0170-42c1-8bbf-272ff8649e40 | tines_automation_vdp | Tines (VDP) | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 51b3b124-aa64-4993-8fdf-0d5e563f9b84 | sembcorp_industries | Sembcorp Industries | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 9468f3e1-ab82-4123-b550-2f8dca7f5548 | mod_supply_chain_vdp | MOD Supply Chain VDP | hackerone | True | 145 | False | not selected: run pinned to explicit program selector(s) |
| 0f571b56-45bb-47ea-96c5-6f0654b58e5a | vercel_platform_protection | Vercel Platform Protection | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 1756e644-7596-4324-8b62-4b7397e4676c | anduril_industries | Anduril Industries | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 4b4ab447-45f6-4069-b509-1187c6544dc8 | bose_vdp | Bose (VDP) | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 3fa4813c-1f5b-42e2-9476-bc7c86d4b59f | twilio | Twilio | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| decf54c8-88fa-43f7-9748-edaf0e64d326 | doordash | DoorDash | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| ce7429fd-1845-47e7-bcea-be9df83c42d3 | mueller_water_products_vdp | Mueller Water Products (VDP) | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 2fc5c460-9bcb-4934-8528-c98a348f3f07 | henkel_vdp | Henkel | hackerone | True | 238 | False | not selected: run pinned to explicit program selector(s) |
| 8ccd4f99-537a-4ced-8459-ae1de54123c9 | vueling_vdp | Vueling | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 371a2a54-74f8-42fc-8b6a-2cf683108bd3 | mufg-vdp | MUFG VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| eed464ce-a67e-494d-8572-12d148cbf4ec | docusign | DocuSign | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 810fd9c9-eb10-4c3f-b21c-6395f4507dfb | bankunited | BankUnited | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| dd2f6ea2-a6a8-4998-956f-6011489b2982 | robinhood | Robinhood Markets Bounty | hackerone | True | 25 | False | not selected: run pinned to explicit program selector(s) |
| 858fe5ec-8792-4782-ac94-3d9acb53a34c | robinhood_markets | Robinhood Markets | hackerone | True | 30 | False | not selected: run pinned to explicit program selector(s) |
| 84f2cf6a-85bd-42be-be30-01fe7f29ba11 | british_airways_vdp | British Airways VDP | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 928e4621-6695-46e0-a920-ba39f4fbe095 | regions_financial | Regions Financial | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 925cdd74-685d-4ad4-bb04-13f5f6dd3787 | vercel-open-source | Vercel Open Source | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 6daebed2-35cd-48ef-b12c-4681545877b9 | netscaler_public_program | NetScaler Public Program | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 332b779a-4f44-478c-b7f4-14734e4bf0d7 | lovable-vdp | Lovable VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 6f76580c-b696-4dcc-851a-e7b9877fb408 | hack_the_box | Hack The Box | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 2531f111-d174-4310-b077-46d7555a389d | banco_plata | Banco Plata | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 325c4b12-4495-41dc-b380-a4ddc38fda8f | braze_inc | Braze, Inc. | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| ed29591a-4069-475e-a896-e7c0a6c85d25 | meesho_bbp | Meesho | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| c50a4e09-e9f6-46bc-8a18-b8352c0e9274 | tucows_vdp | Tucows (VDP) | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| cf570b66-0b07-4497-b2d5-6bb600d224ba | tbs-sct | Treasury Board of Canada Secretariat/Secrétariat du Conseil du Trésor du Canada | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| c4cea536-9974-489e-a3d1-df2a997faf8f | citi_group | Citi Group | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 9e66052c-f300-4e3a-8e92-7e47ae3c767e | kong | Kong | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 7b6d9d26-db72-4a06-8d86-e467fc72f69a | worldpay | Worldpay | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 8610a261-292b-434b-b6bd-45085ef82e25 | hertz | Hertz VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 7f98847f-8330-4e39-b831-39c4485769a0 | experian | Experian | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 57cf38bf-1c79-4c8c-ac7e-c3a3057b0c05 | hexagon_vdp | Hexagon-VDP | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 4cb6d661-8523-4551-9732-0f43ceadb18a | eightfold | Eightfold | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| e7352aca-e365-4cf8-b8ce-ea992b796282 | centene_vdp | Centene_vdp | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 246e3339-15ef-4d82-b42d-bcc78b17c49e | msci | MSCI | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| ecec566c-70ea-43c8-a7a6-7fadf2abc83a | ferrero | Ferrero | hackerone | True | 274 | False | not selected: run pinned to explicit program selector(s) |
| 4b2de34b-55bd-4b5c-b4e2-f4f8d964b293 | dust | Dust | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| b7cdc7de-37e6-48ea-99bb-0a42fc1fc2ff | hotmartvdp | Hotmart (VDP) | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 44cedc52-7547-4e32-91b4-a5bd5f605452 | hex | Hex | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| cef0a23c-3378-4a46-ba35-e1798ec4ed38 | hyland_software | Hyland Software | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 254925be-ff0e-4c12-a342-b463e38725a7 | whoop_bug_bounty | Whoop Bug Bounty | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| e51f73f9-fe76-44c2-a269-e20b3bb5d1f0 | baird_vdp | Baird | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 949ad6ef-6164-452d-8811-bcd2a5f765a6 | northerntechhq | Northern.tech | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 00dee5b7-5a59-4802-92b8-18f9cdff349e | alibaba_vdp | Alibaba VDP | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 4a0c4627-4c84-48a4-be94-3a89b49b8752 | hemi_labs_vdp | Hemi VDP | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 626f4022-ea0d-4013-9203-ecd9487aa26e | kraken-tech | Kraken Tech | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| efad25d9-be1a-4500-91b9-e6dfae6ca638 | bcny | The Browser Company of NYC | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| ffc9a0d5-1656-43ce-945f-ae7ac91b4500 | 1password | 1Password - Enterprise Password Manager | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 497970dc-fbc9-4d64-9881-3d134ec3a59a | 1password_ctf | 1Password - CTF | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2ef3efbf-a072-4368-bcf2-b5b74d84d5d0 | neon_bbp | Neon | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 2a9482df-9877-47cd-a85e-4552afb5225d | penn_entertainment | Penn Entertainment | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| 920d43e8-9590-47cd-83f0-7ebd571899f4 | kaseya | Kaseya | hackerone | True | 38 | False | not selected: run pinned to explicit program selector(s) |
| 005ba800-68d7-45e5-80fb-47cd7ed1d876 | oppo_bbp | OPPO | hackerone | True | 124 | False | not selected: run pinned to explicit program selector(s) |
| e2a28528-8efd-4da2-971c-d3530c5a9188 | hubspot | HubSpot | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| 95757948-34db-4c6f-ab60-afe292b12b13 | adevinta_vdp | Adevinta | hackerone | True | 23 | False | not selected: run pinned to explicit program selector(s) |

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
  "completed_at": "2026-03-24T13:15:45.853221+00:00",
  "created_at": "2026-03-24T13:04:27.844928+00:00",
  "error_detail": null,
  "finding_count": 0,
  "partial_detail": "{\"errors\": {\"nuclei_scan\": \"nuclei exited with code 2. stderr: \"}, \"failed_stages\": [\"nuclei_scan\"]}",
  "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb",
  "retry_count": 0,
  "scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335",
  "severity_breakdown": "{\"low\": 0, \"high\": 0, \"info\": 0, \"medium\": 0, \"critical\": 0}",
  "started_at": "2026-03-24T13:04:27.844928+00:00",
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
| 1.0 | asset_discovery | completed | 2026-03-24T13:04:28.064380+00:00 | 2026-03-24T13:05:08.849572+00:00 |  |
| 2.0 | fingerprinting | completed | 2026-03-24T13:05:08.854881+00:00 | 2026-03-24T13:05:15.274355+00:00 |  |
| 3.0 | enumeration | completed | 2026-03-24T13:05:15.277028+00:00 | 2026-03-24T13:15:45.327170+00:00 |  |
| 4.0 | nuclei_scan | failed | 2026-03-24T13:15:45.347315+00:00 | 2026-03-24T13:15:45.832477+00:00 | nuclei exited with code 2. stderr:  |
| 5.0 | web_vuln_tests | completed | 2026-03-24T13:15:45.347315+00:00 | 2026-03-24T13:15:45.837319+00:00 |  |
| 6.0 | js_secrets | completed | 2026-03-24T13:15:45.840594+00:00 | 2026-03-24T13:15:45.843490+00:00 |  |
| 10.1 | report_handoff | completed | 2026-03-24T13:15:45.859488+00:00 | 2026-03-24T13:15:45.889637+00:00 |  |

### Artifact Counts
```json
{
  "assets_count": 2,
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
    "completed_at": "2026-03-24T13:15:45.853221+00:00",
    "error_detail": null,
    "finding_count": 0,
    "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb",
    "scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335",
    "severity_breakdown": {
      "critical": 0,
      "high": 0,
      "info": 0,
      "low": 0,
      "medium": 0
    },
    "started_at": "2026-03-24T13:04:27.844928+00:00",
    "status": "partial"
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/scans/063ae238-f4f8-414a-9fd6-7454bef1d335"
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
  "url": "http://localhost:8002/api/v1/scans/063ae238-f4f8-414a-9fd6-7454bef1d335/findings"
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
 Container attackbot-loki-1  Running
 Container attackbot-prometheus-1  Running
 Container attackbot-vault-1  Running
 Container attackbot-postgres-1  Running
 Container attackbot-neo4j-1  Running
 Container attackbot-grafana-1  Running
 Container attackbot-minio-1  Running
 Container attackbot-rabbitmq-1  Running
 Container attackbot-redis-1  Running
 Container attackbot-attack-graph-engine-1  Running
 Container attackbot-scraper-1  Running
 Container attackbot-reporter-1  Running
 Container attackbot-core-engine-1  Running
 Container attackbot-reporter-worker-1  Running
 Container attackbot-exploit-verifier-1  Running
 Container attackbot-api-fuzzer-worker-1  Running
 Container attackbot-ai-analysis-worker-1  Running
 Container attackbot-scenario-runner-1  Running
 Container attackbot-browser-worker-1  Running
 Container attackbot-api-gateway-1  Running
 Container attackbot-core-worker-1  Running
 Container attackbot-js-analysis-worker-1  Running
 Container attackbot-tempo-1  Starting
 Container attackbot-vault-1  Waiting
 Container attackbot-minio-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-tempo-1  Started
 Container attackbot-postgres-1  Healthy
 Container attackbot-migrate-1  Starting
 Container attackbot-vault-1  Healthy
 Container attackbot-vault-init-1  Starting
 Container attackbot-minio-1  Healthy
 Container attackbot-minio-init-1  Starting
 Container attackbot-migrate-1  Started
 Container attackbot-neo4j-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-minio-init-1  Started
 Container attackbot-minio-init-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-vault-init-1  Started
 Container attackbot-neo4j-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-minio-init-1  Exited
 Container attackbot-minio-init-1  Exited
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-postgres-1  Healthy
 Container attackbot-postgres-1  Healthy
 Container attackbot-minio-init-1  Exited
 Container attackbot-postgres-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-migrate-1  Exited
 Container attackbot-migrate-1  Exited
 Container attackbot-reporter-1  Waiting
 Container attackbot-migrate-1  Exited
 Container attackbot-migrate-1  Exited
 Container attackbot-scraper-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-reporter-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-attack-graph-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Healthy
 Container attackbot-reporter-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-reporter-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-scraper-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-attack-graph-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-core-engine-1  Healthy

```

### Command: docker compose ps
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env ps`

```text
STDOUT:
NAME                              IMAGE                           COMMAND                  SERVICE               CREATED       STATUS                          PORTS
attackbot-ai-analysis-worker-1    attackbot-ai-analysis-worker    "celery -A backend.sâ€¦"   ai-analysis-worker    6 hours ago   Up 6 hours                      
attackbot-api-fuzzer-worker-1     attackbot-api-fuzzer-worker     "celery -A backend.sâ€¦"   api-fuzzer-worker     6 hours ago   Up 6 hours                      
attackbot-api-gateway-1           attackbot-api-gateway           "uvicorn backend.serâ€¦"   api-gateway           6 hours ago   Up 6 hours (unhealthy)          0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
attackbot-attack-graph-engine-1   attackbot-attack-graph-engine   "uvicorn backend.serâ€¦"   attack-graph-engine   6 hours ago   Up 6 hours (healthy)            8006/tcp
attackbot-browser-worker-1        attackbot-browser-worker        "celery -A backend.sâ€¦"   browser-worker        6 hours ago   Up 6 hours                      
attackbot-core-engine-1           attackbot-core-engine           "uvicorn backend.serâ€¦"   core-engine           6 hours ago   Up 6 hours (healthy)            0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
attackbot-core-worker-1           attackbot-core-worker           "celery -A backend.sâ€¦"   core-worker           6 hours ago   Up 6 hours                      8002/tcp
attackbot-exploit-verifier-1      attackbot-exploit-verifier      "celery -A backend.sâ€¦"   exploit-verifier      6 hours ago   Up 6 hours                      
attackbot-grafana-1               grafana/grafana:latest          "/run.sh"                grafana               6 hours ago   Up 6 hours                      0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
attackbot-js-analysis-worker-1    attackbot-js-analysis-worker    "celery -A backend.sâ€¦"   js-analysis-worker    6 hours ago   Up 6 hours                      
attackbot-loki-1                  grafana/loki:latest             "/usr/bin/loki -confâ€¦"   loki                  6 hours ago   Up 6 hours                      3100/tcp
attackbot-minio-1                 minio/minio                     "/usr/bin/docker-entâ€¦"   minio                 6 hours ago   Up 6 hours (healthy)            9000/tcp
attackbot-neo4j-1                 neo4j:5-community               "tini -g -- /startupâ€¦"   neo4j                 6 hours ago   Up 6 hours (healthy)            7473-7474/tcp, 7687/tcp
attackbot-postgres-1              postgres:16                     "docker-entrypoint.sâ€¦"   postgres              6 hours ago   Up 6 hours (healthy)            0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
attackbot-prometheus-1            prom/prometheus:latest          "/bin/prometheus --câ€¦"   prometheus            6 hours ago   Up 6 hours                      9090/tcp
attackbot-rabbitmq-1              rabbitmq:3-management           "docker-entrypoint.sâ€¦"   rabbitmq              6 hours ago   Up 6 hours (healthy)            0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
attackbot-redis-1                 redis:7-alpine                  "docker-entrypoint.sâ€¦"   redis                 6 hours ago   Up 6 hours (healthy)            6379/tcp
attackbot-reporter-1              attackbot-reporter              "uvicorn backend.serâ€¦"   reporter              6 hours ago   Up 6 hours (healthy)            8003/tcp
attackbot-reporter-worker-1       attackbot-reporter-worker       "celery -A backend.sâ€¦"   reporter-worker       6 hours ago   Up 6 hours                      8003/tcp
attackbot-scenario-runner-1       attackbot-scenario-runner       "celery -A backend.sâ€¦"   scenario-runner       6 hours ago   Up 6 hours                      
attackbot-scraper-1               attackbot-scraper               "uvicorn backend.serâ€¦"   scraper               6 hours ago   Up 6 hours (healthy)            0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
attackbot-tempo-1                 grafana/tempo:latest            "/tempo"                 tempo                 6 hours ago   Restarting (1) 15 seconds ago   
attackbot-vault-1                 hashicorp/vault:1.15            "docker-entrypoint.sâ€¦"   vault                 6 hours ago   Up 6 hours (healthy)            8200/tcp


STDERR:
<empty>
```

### Command: docker compose logs (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env logs --no-color --since 2026-03-24T13:04:26Z --tail 300 scraper core-engine core-worker reporter reporter-worker`

```text
STDOUT:
scraper-1          | INFO:     172.20.0.13:47406 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.3:40410 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     127.0.0.1:35594 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "fig", "program_id": "99f5d538-ad7e-4e8c-bcf7-e75f91b3de8f", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:05:48.332143Z"}
scraper-1          | {"handle": "smule", "program_id": "b4db9ca5-b6d1-4624-ae33-51ddc7b8d8b5", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:05:51.611888Z"}
scraper-1          | {"handle": "bitmex", "program_id": "70c8bad9-b07b-4ae2-9546-a91700ddfd81", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:05:54.282079Z"}
scraper-1          | INFO:     172.20.0.13:55462 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "ed", "program_id": "354457aa-7dc4-426f-9315-fb5ad76a3a3e", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:05:56.939843Z"}
scraper-1          | INFO:     127.0.0.1:46724 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "jamieweb", "program_id": "99770bc0-4a69-41f6-82e3-760b3433da53", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:05:59.597018Z"}
scraper-1          | INFO:     172.20.0.3:45784 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | {"handle": "flutteruki", "program_id": "5f524a60-478c-4225-8eaa-341e694abf6c", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:03.140180Z"}
scraper-1          | {"handle": "databricks", "program_id": "60fafd88-f4a6-42a6-980b-64e189962fb3", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:06.073314Z"}
scraper-1          | INFO:     172.20.0.13:39042 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:34526 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "cosmos", "program_id": "dda96618-8834-4cfc-babe-1dc5db15669d", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:09.029031Z"}
reporter-worker-1  | [2026-03-24 13:15:45,903: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "ebeacb03-c56f-45f1-9d28-9c1e0179fea6", "event_type": "scan.completed", "scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T13:15:45.898831Z"}
core-worker-1      | [2026-03-24 13:04:27,250: INFO/MainProcess] Task core_engine.scan_task[0294e644-1b05-4d03-97ba-e3d4322a46d1] received
reporter-worker-1  | [2026-03-24 13:15:45,911: WARNING/MainProcess] {"scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T13:15:45.911033Z"}
reporter-worker-1  | [2026-03-24 13:15:45,911: WARNING/MainProcess] {"scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-24T13:15:45.911474Z"}
core-worker-1      | [2026-03-24 13:04:27,394: WARNING/ForkPoolWorker-2] {"program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "event_type": "program.scraped", "event": "Scan task received", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:27.382908Z"}
core-worker-1      | [2026-03-24 13:04:27,540: WARNING/ForkPoolWorker-2] {"pool_size": 10, "max_overflow": 20, "event": "db_initialized", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:27.539777Z"}
core-worker-1      | [2026-03-24 13:04:27,564: WARNING/ForkPoolWorker-2] {"endpoint": "minio:9000", "secure": false, "event": "minio_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:27.562628Z"}
reporter-1         | INFO:     127.0.0.1:35742 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:53130 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:53566 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "coalition", "program_id": "a414ca84-f09c-4f45-b2d7-815e46f68dd7", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:12.297663Z"}
reporter-1         | INFO:     172.20.0.3:58208 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:53780 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "affirm", "program_id": "560961c8-2bad-420a-bf05-861ff4a4e465", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:16.033364Z"}
scraper-1          | INFO:     172.20.0.3:38252 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     172.20.0.13:50600 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:55686 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "crowdstrike", "program_id": "2cd4374b-7474-4e2b-817f-a566904bc9ed", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:18.659377Z"}
scraper-1          | {"handle": "pingidentity", "program_id": "45dc06e3-e022-4044-93a8-410dcae153d2", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:21.179638Z"}
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/programs/6e7f4e62-7a0f-400b-a9da-398c648161cb "HTTP/1.1 200 OK"
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/programs/6e7f4e62-7a0f-400b-a9da-398c648161cb/scope "HTTP/1.1 200 OK"
scraper-1          | {"handle": "passhash", "program_id": "d9790fa2-c1e4-4eec-9589-1636c5d9a7da", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:25.195408Z"}
scraper-1          | INFO:     172.20.0.13:42242 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:58402 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "ycombinator", "program_id": "2f46a142-616c-4851-8557-65155f574ba0", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:30.111577Z"}
reporter-1         | INFO:     127.0.0.1:55110 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:39700 - "GET /metrics HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.1:33692 - "POST /api/v1/scans/start HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:55620 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:34822 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1          | INFO:     172.20.0.3:44270 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | {"handle": "ratelimited", "program_id": "2fbdcfe0-7255-497f-888f-7ff1495b490f", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:31.822786Z"}
reporter-1         | INFO:     127.0.0.1:46714 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:60386 - "GET /metrics HTTP/1.1" 200 OK
core-worker-1      | [2026-03-24 13:04:27,869: WARNING/ForkPoolWorker-2] {"scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "event": "Scan created", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:27.869609Z"}
core-worker-1      | [2026-03-24 13:04:27,991: INFO/ForkPoolWorker-2] HTTP Request: GET http://scraper:8001/api/v1/programs/6e7f4e62-7a0f-400b-a9da-398c648161cb/scope "HTTP/1.1 200 OK"
core-worker-1      | [2026-03-24 13:04:28,061: WARNING/ForkPoolWorker-2] {"url": "amqp://attackbot:attackbot@rabbitmq:5672/", "event": "queue_publisher_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:28.061341Z"}
reporter-1         | INFO:     127.0.0.1:46816 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:58202 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:58990 - "GET /metrics HTTP/1.1" 200 OK
core-worker-1      | [2026-03-24 13:04:28,062: WARNING/ForkPoolWorker-2] {"scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "event": "Stage 0: Scope filter", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:28.062262Z"}
core-worker-1      | [2026-03-24 13:04:28,064: WARNING/ForkPoolWorker-2] {"in_scope_count": 6, "out_of_scope_count": 2, "event": "ScopeFilter built", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:28.064193Z"}
reporter-1         | INFO:     127.0.0.1:38786 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     127.0.0.1:51284 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:57944 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:44022 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:42848 - "GET /metrics HTTP/1.1" 404 Not Found
core-worker-1      | [2026-03-24 13:04:28,066: WARNING/ForkPoolWorker-2] {"scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "skipped_counts": {"url_host_not_domain_led": 5}, "event": "asset_discovery_seed_scope_skipped", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:28.066625Z"}
core-worker-1      | [2026-03-24 13:04:28,072: WARNING/ForkPoolWorker-2] {"args": "subfinder", "timeout": 180, "event": "Running subfinder[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:28.072139Z"}
reporter-1         | INFO:     172.20.0.3:33476 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:53980 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:47898 - "GET /metrics HTTP/1.1" 200 OK
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-worker-1      | [2026-03-24 13:04:59,576: WARNING/ForkPoolWorker-2] {"domain": "hosted.weblate.org", "event": "alterx_skipped_no_subfinder_results", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:59.575898Z"}
core-worker-1      | [2026-03-24 13:04:59,577: WARNING/ForkPoolWorker-2] {"args": "dnsx", "timeout": 270, "event": "Running dnsx[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:04:59.577793Z"}
reporter-1         | INFO:     127.0.0.1:40352 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:38160 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     127.0.0.1:34598 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
scraper-1          | {"handle": "crypto", "program_id": "167c9df5-c7e3-4561-a711-0d0282adbced", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:35.041258Z"}
scraper-1          | INFO:     172.20.0.13:49100 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "liberapay", "program_id": "2aab1a9c-5176-4da8-acea-6cc322bc0c10", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:38.103027Z"}
scraper-1          | INFO:     127.0.0.1:55596 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "pixiv", "program_id": "1881f6ca-9b8f-4df0-b575-034c37a6a06d", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:42.819501Z"}
core-engine-1      | INFO:     127.0.0.1:42098 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.3:36682 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | {"handle": "arkadiyt-projects", "program_id": "e05cfe25-b802-4f2d-bd5c-df7339dae5da", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:46.805659Z"}
scraper-1          | INFO:     172.20.0.13:53600 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:44496 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:56396 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:58898 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:57040 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:40454 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:39572 - "GET /api/v1/health HTTP/1.1" 200 OK
core-worker-1      | [2026-03-24 13:05:02,821: WARNING/ForkPoolWorker-2] {"args": "httpx", "timeout": 180, "event": "Running httpx[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:05:02.821566Z"}
core-worker-1      | [2026-03-24 13:05:08,837: WARNING/ForkPoolWorker-2] {"scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "seed_domains": 1, "assets_found": 1, "errors": 0, "event": "Stage 1 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:05:08.837111Z"}
core-worker-1      | [2026-03-24 13:05:08,856: WARNING/ForkPoolWorker-2] {"args": "httpx", "timeout": 180, "event": "Running httpx_fingerprint", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:05:08.856100Z"}
core-worker-1      | [2026-03-24 13:05:15,266: WARNING/ForkPoolWorker-2] {"scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "assets_enriched": 1, "event": "Stage 2 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:05:15.265844Z"}
core-engine-1      | INFO:     172.20.0.3:39710 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:57392 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:59378 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:57484 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:40890 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:39356 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:35906 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:52502 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:48386 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:46908 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "s-pankki", "program_id": "ff05b5b8-18ca-42a3-b232-c9edd6ea805c", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:49.466747Z"}
scraper-1          | {"handle": "hannob", "program_id": "b5ac8061-4400-4252-abfe-f69ec6b6d541", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:51.422640Z"}
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:50578 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:45612 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.3:38610 - "GET /metrics HTTP/1.1" 200 OK
scraper-1          | {"handle": "chaturbate", "program_id": "6848701b-69ee-4fd7-8490-8e3bd8364c80", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:54.290885Z"}
scraper-1          | {"handle": "cfptime", "program_id": "e4d1112d-cbdc-465a-9f68-c45c156d8ded", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:06:57.756723Z"}
scraper-1          | INFO:     172.20.0.13:56064 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:41254 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:40774 - "GET /metrics HTTP/1.1" 404 Not Found
core-worker-1      | [2026-03-24 13:05:15,278: WARNING/ForkPoolWorker-2] {"args": "ffuf", "timeout": 540, "event": "Running ffuf[https://hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:05:15.278507Z"}
core-worker-1      | [2026-03-24 13:14:15,278: WARNING/ForkPoolWorker-2] {"asset": "https://hosted.weblate.org", "error": "ffuf[https://hosted.weblate.org] timed out after 540s", "event": "ffuf failed", "service": "core-worker", "level": "warning", "timestamp": "2026-03-24T13:14:15.278703Z"}
core-worker-1      | [2026-03-24 13:14:15,279: WARNING/ForkPoolWorker-2] {"args": "waybackurls", "timeout": 90, "event": "Running waybackurls[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-24T13:14:15.279381Z"}
scraper-1          | INFO:     127.0.0.1:46760 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.3:36320 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | {"handle": "marriott", "program_id": "eb057109-8ced-44b1-b573-5d717fa141b7", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:07:07.393811Z"}
scraper-1          | INFO:     172.20.0.13:39964 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:50912 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | {"handle": "nisc", "program_id": "a586b917-634b-4c80-9e03-49edb66caca3", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:07:11.820610Z"}
scraper-1          | Running job "Reconciler.reconcile (trigger: interval[0:05:00], next run at: 2026-03-24 13:12:12 UTC)" (scheduled at 2026-03-24 13:07:12.155146+00:00)
reporter-1         | INFO:     172.20.0.3:47160 - "GET /metrics HTTP/1.1" 200 OK
scraper-1          | {"reason": "E2E_PAUSE_RECONCILER is enabled", "event": "reconciler_paused", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:07:12.155485Z"}
scraper-1          | Job "Reconciler.reconcile (trigger: interval[0:05:00], next run at: 2026-03-24 13:12:12 UTC)" executed successfully
scraper-1          | {"handle": "chainlink", "program_id": "995f1f36-42ad-47a6-ac49-1fcb58b0bc95", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-24T13:07:14.358608Z"}
scraper-1          | INFO:     172.20.0.3:59292 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:56408 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.3:32914 - "GET /metrics HTTP/1.1" 404 Not Found
reporter-1         | INFO:     127.0.0.1:41886 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:58252 - "GET /api/v1/health HTTP/1.1" 200 OK
core-worker-1      | [2026-03-24 13:15:45,306: WARNING/ForkPoolWorker-2] {"domain": "hosted.weblate.org", "error": "waybackurls[hosted.weblate.org] timed out after
... [truncated]

STDERR:
<empty>
```

### Command: docker compose logs reporter-worker (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env logs --no-color --since 2026-03-24T13:04:26Z --tail 300 reporter-worker`

```text
STDOUT:
reporter-worker-1  | [2026-03-24 13:15:45,903: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "ebeacb03-c56f-45f1-9d28-9c1e0179fea6", "event_type": "scan.completed", "scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T13:15:45.898831Z"}
reporter-worker-1  | [2026-03-24 13:15:45,911: WARNING/MainProcess] {"scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-24T13:15:45.911033Z"}
reporter-worker-1  | [2026-03-24 13:15:45,911: WARNING/MainProcess] {"scan_id": "063ae238-f4f8-414a-9fd6-7454bef1d335", "program_id": "6e7f4e62-7a0f-400b-a9da-398c648161cb", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-24T13:15:45.911474Z"}


STDERR:
<empty>
```

## Observed Gaps in Current Implementation
- Reporter worker currently validates `report.jobs` envelopes only.
- Specialist workers are queue listeners; deeper stages land in later milestones.
- This report reflects what ran in this test session, not aspirational docs.
